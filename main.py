"""
main.py — Ahira
PostgreSQL + MongoDB. All data is user-scoped.
Sessions expire after 30 days. Guests see empty data.
"""

import os
import json
import hmac
import hashlib
import uuid
import secrets
import smtplib
import ssl
import traceback
import unicodedata
from base64 import urlsafe_b64encode, urlsafe_b64decode
from datetime import datetime, timedelta
from typing import Optional
from email.message import EmailMessage

import requests
from fastapi import Body, Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from bson import ObjectId

from ai.database import Base, engine, get_db, test_connection
from ai.models import Reminder as ReminderModel
from ai.models import User, UserSession, UserRecoveryEmoji
import ai.crud as crud
import ai.mongo as mongo

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SESSION_COOKIE = "ahira_session"
SESSION_MAX_DAYS = 30
RECOVERY_EMOJI_COUNT = 4
RECOVERY_MAX_FAILED_ATTEMPTS = 5
RECOVERY_LOCK_MINUTES = 15
RECOVERY_TOKEN_TTL_MINUTES = 10
RECOVERY_EMOJI_MAP = {
    "🌙": "A1",
    "☕": "B2",
    "🌸": "C3",
    "🐇": "D4",
    "✨": "E5",
    "🪷": "F6",
    "🫧": "G7",
    "🌷": "H8",
    "⭐": "J9",
    "🕊️": "K1",
    "🍓": "L2",
    "💫": "M3",
    "🌊": "N4",
    "🦋": "P5",
    "🍃": "Q6",
    "🪻": "R7",
    "🍯": "S8",
    "🫶": "T9",
    "🌼": "U1",
    "🪄": "V2",
    "🩷": "W3",
    "🌤️": "X4",
    "🌛": "Y5",
    "🤍": "Z6",
    "😀": "AA1",
    "😭": "BB7",
    "🔥": "KK3",
    "❤️": "PP2",
}
RECOVERY_EMOJI_ALIASES = {
    "❤": "❤️",
    "♥": "❤️",
    "☀️": "🌤️",
    "☀": "🌤️",
    "🕊": "🕊️",
    "🌤": "🌤️",
}
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_PRIMARY_MODEL = "z-ai/glm-4.5-air:free"
OPENROUTER_DEFAULT_MODEL = OPENROUTER_PRIMARY_MODEL
OPENROUTER_FALLBACK_MODELS = [
    "openai/gpt-oss-20b:free",
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-120b:free",
]
OPENROUTER_TIMEOUT_SECONDS = 25
OPENROUTER_CONNECT_TIMEOUT_SECONDS = 5
OPENROUTER_SESSION = requests.Session()
OPENROUTER_LAST_STATUS = {
    "current_model": OPENROUTER_DEFAULT_MODEL,
    "last_successful_model": None,
    "last_response_time_ms": None,
    "last_provider_error": None,
    "failover_history": [],
    "status": "not_tested",
}


# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    db = next(get_db())
    try:
        run_feed_migrations(db)
        _ensure_season_one_seed_guard(db)
        print("[Ahira] ✅ Feed migrations applied")
    except Exception as e:
        db.rollback()
        print(f"[Ahira] ❌ Feed migrations failed: {e}")
    finally:
        db.close()

    if test_connection():
        print("[Ahira] ✅ PostgreSQL ready")
    else:
        print("[Ahira] ❌ PostgreSQL failed")
    mongo.get_client()
    mongo.ensure_indexes()
    _log_openrouter_startup_status()


def _ensure_season_one_seed_guard(db: Session):
    marker = db.execute(
        text(
            """
            SELECT 1
            FROM app_preferences
            WHERE user_id IS NULL AND pref_key = 'season_2026_01_seeded_v1'
            LIMIT 1
            """
        )
    ).first()
    if marker:
        return
    db.execute(
        text(
            """
            INSERT INTO seasons (season_code, start_date, end_date, is_active)
            VALUES ('2026-01', DATE '2026-01-01', DATE '2026-01-31', TRUE)
            ON CONFLICT (season_code) DO NOTHING
            """
        )
    )
    db.execute(
        text(
            """
            INSERT INTO app_preferences (user_id, pref_key, pref_value)
            VALUES (NULL, 'season_2026_01_seeded_v1', '{}'::jsonb)
            ON CONFLICT (user_id, pref_key) DO NOTHING
            """
        )
    )
    db.commit()


def _log_openrouter_startup_status():
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = OPENROUTER_DEFAULT_MODEL
    if key:
        print(
            f"[OpenRouter] ✅ API enabled model={model} "
            f"candidateCount={len(_openrouter_model_candidates())}"
        )
    else:
        print(
            f"[OpenRouter] ❌ OPENROUTER_API_KEY missing. "
            f"API disabled model={model}"
        )


def _openrouter_model_candidates() -> list[str]:
    candidates = [
        OPENROUTER_PRIMARY_MODEL,
        *OPENROUTER_FALLBACK_MODELS,
    ]
    seen = set()
    ordered = []
    for model in candidates:
        model = (model or "").strip()
        if not model or model in seen:
            continue
        seen.add(model)
        ordered.append(model)
    return ordered


def _set_openrouter_status(
    *,
    status: str,
    current_model: Optional[str] = None,
    last_successful_model: Optional[str] = None,
    last_response_time_ms: Optional[int] = None,
    last_provider_error: Optional[str] = None,
    failover_history: Optional[list[dict]] = None,
):
    OPENROUTER_LAST_STATUS.update(
        {
            "status": status,
            "current_model": current_model or OPENROUTER_LAST_STATUS.get("current_model"),
            "last_successful_model": last_successful_model,
            "last_response_time_ms": last_response_time_ms,
            "last_provider_error": last_provider_error,
            "failover_history": failover_history or [],
        }
    )


def _openrouter_status_payload() -> dict:
    return {
        "current_model": OPENROUTER_LAST_STATUS.get("current_model") or OPENROUTER_DEFAULT_MODEL,
        "last_successful_model": OPENROUTER_LAST_STATUS.get("last_successful_model"),
        "last_response_time_ms": OPENROUTER_LAST_STATUS.get("last_response_time_ms"),
        "last_provider_error": OPENROUTER_LAST_STATUS.get("last_provider_error"),
        "failover_history": OPENROUTER_LAST_STATUS.get("failover_history") or [],
        "status": OPENROUTER_LAST_STATUS.get("status") or "not_tested",
        "models": _openrouter_model_candidates(),
    }


def _extract_openrouter_content(decoded: dict, model: str) -> str:
    choices = decoded.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"openrouter_parse_missing_choices model={model}")
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first, dict) else {}
    if not isinstance(message, dict):
        raise RuntimeError(f"openrouter_parse_missing_message model={model}")
    raw = message.get("content")
    if isinstance(raw, str):
        content = raw.strip()
    elif isinstance(raw, list):
        parts = []
        for part in raw:
            if isinstance(part, dict):
                text = str(part.get("text") or "").strip()
                if text:
                    parts.append(text)
            elif isinstance(part, str) and part.strip():
                parts.append(part.strip())
        content = "\n".join(parts).strip()
    else:
        content = ""
    if not content:
        raise RuntimeError(f"openrouter_parse_empty_content model={model}")
    return content


# ── Session helper ────────────────────────────────────────────
def current_user(request: Request, db: Session):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None

    session = db.query(UserSession).filter(UserSession.token == token).first()
    if not session:
        return None

    age = datetime.utcnow() - session.created_at
    if age > timedelta(days=SESSION_MAX_DAYS):
        db.delete(session)
        db.commit()
        return None

    return session.user


# ── Schemas ───────────────────────────────────────────────────
class RegisterBody(BaseModel):
    name: str
    email: str
    password: str


class LoginBody(BaseModel):
    email: str
    password: str


class ChatBody(BaseModel):
    message: str
    history: list[dict] = []
    language_code: Optional[str] = None
    languageCode: Optional[str] = None


class ReminderBody(BaseModel):
    task: str
    date: Optional[str] = None
    time: Optional[str] = None
    priority: str = "normal"


class FeedReportBody(BaseModel):
    post_id: str
    post_type: str
    reason: str
    details: Optional[str] = None


class FeedCreateBody(BaseModel):
    content: str
    category: Optional[str] = "Daily Life ☕"
    mood: Optional[str] = "emotional"
    anonymousIdentity: Optional[str] = "☁️ Quiet Mind"
    postId: Optional[str] = None
    languageType: Optional[str] = None


class FeedCommentCreateBody(BaseModel):
    content: str
    anonymousIdentity: Optional[str] = "☁️ Quiet Mind"


class FeedReactionBody(BaseModel):
    reaction: Optional[str] = None
    previousReaction: Optional[str] = None


class TeamSelectBody(BaseModel):
    teamName: Optional[str] = None
    teamId: Optional[str] = None


class GameScoreBody(BaseModel):
    gameId: str
    score: int
    xpEarned: int = 0
    contributionPoints: int = 0
    seasonId: Optional[str] = None
    idempotencyKey: Optional[str] = None
    antiCheatMetadata: Optional[dict] = None
    durationMs: Optional[int] = 0
    deaths: Optional[int] = 0
    powerups: Optional[int] = 0
    attempts: Optional[int] = 1


class SyncQueueItemBody(BaseModel):
    actionType: str
    payload: dict
    idempotencyKey: str
    createdAt: Optional[str] = None


class SyncQueueBatchBody(BaseModel):
    items: list[SyncQueueItemBody]


class ReminderUpdateBody(BaseModel):
    task: str
    date: Optional[str] = None
    time: Optional[str] = None
    priority: str = "normal"
    completed: Optional[int] = None


class TeamChangeBody(BaseModel):
    teamName: Optional[str] = None
    teamId: Optional[str] = None


class DeleteAccountBody(BaseModel):
    password: str


class ForgotPasswordBody(BaseModel):
    email: str


class VerifyResetBody(BaseModel):
    email: str
    token: str


class ResetPasswordBody(BaseModel):
    email: str
    token: str
    newPassword: str


class RecoveryEmojiSetupBody(BaseModel):
    emoji_sequence: list[str]
    current_password: Optional[str] = None
    recovery_hint: Optional[str] = None


class RecoveryEmojiVerifyBody(BaseModel):
    email: str
    emoji_sequence: Optional[list[str]] = None
    emojis: Optional[list[str]] = None


class RecoveryEmojiResetBody(BaseModel):
    temporary_reset_token: Optional[str] = None
    reset_token: Optional[str] = None
    new_password: str


class WaterTrackBody(BaseModel):
    amountMl: int
    consumedAt: Optional[str] = None
    dayKey: Optional[str] = None
    source: Optional[str] = "manual"


class HabitTrackBody(BaseModel):
    habitCode: str
    value: int = 1
    dayKey: Optional[str] = None
    metadata: Optional[dict] = None


class MedicineTrackBody(BaseModel):
    medicineName: str
    dosage: Optional[str] = None
    timing: Optional[str] = None
    timings: Optional[list[str]] = None
    taken: bool = False
    dayKey: Optional[str] = None
    metadata: Optional[dict] = None


class DailyTaskTrackBody(BaseModel):
    taskCode: str
    title: str
    completed: bool = False
    dayKey: Optional[str] = None
    metadata: Optional[dict] = None


class PlannerTaskBody(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "normal"
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    completed: Optional[bool] = False


class UserHabitBody(BaseModel):
    habitName: str
    frequency: Optional[str] = "daily"
    targetCount: Optional[int] = 1


class HabitLogBody(BaseModel):
    completedAt: Optional[str] = None


class WellnessLogBody(BaseModel):
    mood: Optional[str] = None
    sleepHours: Optional[float] = None
    stressLevel: Optional[int] = None
    energyLevel: Optional[int] = None
    notes: Optional[str] = None


class GameProgressBody(BaseModel):
    gameId: str
    currentLevel: Optional[int] = 1
    highScore: Optional[int] = 0
    totalScore: Optional[int] = 0


class GoalBody(BaseModel):
    goalTitle: str
    goalDescription: Optional[str] = None
    targetValue: Optional[int] = 0
    currentProgress: Optional[int] = 0
    completed: Optional[bool] = False


class GroceryListBody(BaseModel):
    listName: str


class GroceryItemBody(BaseModel):
    itemName: str
    quantity: Optional[str] = "1"
    completed: Optional[bool] = False


class MedicineBody(BaseModel):
    medicineName: str
    dosage: Optional[str] = None
    firstTime: Optional[str] = None
    secondTime: Optional[str] = None
    thirdTime: Optional[str] = None
    isCombined: Optional[bool] = False
    notes: Optional[str] = None


class MedicineLogBody(BaseModel):
    status: str
    takenAt: Optional[str] = None


class GroceryItemUpdateBody(BaseModel):
    itemName: Optional[str] = None
    quantity: Optional[str] = None
    completed: Optional[bool] = None


class MedicineUpdateBody(BaseModel):
    medicineName: Optional[str] = None
    dosage: Optional[str] = None
    firstTime: Optional[str] = None
    secondTime: Optional[str] = None
    thirdTime: Optional[str] = None
    isCombined: Optional[bool] = None
    notes: Optional[str] = None
    taken: Optional[bool] = None


def _safe_language(value: Optional[str]) -> str:
    v = (value or "en").strip().lower()
    return v if v in {"en", "hi", "mr"} else "en"


def _safe_limit(value: int) -> int:
    return max(1, min(value, 50))


def _safe_offset(value: int) -> int:
    return max(0, value)


def _normalized_post_id(raw: str) -> str:
    value = (raw or "").strip()
    if value.startswith("news_") or value.startswith("user_"):
        return value
    return f"user_{value}"


def _mongo_post_id_from_any(raw: str) -> str:
    key = _normalized_post_id(raw)
    return key.replace("user_", "", 1)


TEAM_NAMES = [
    "Moon Souls",
    "Star Hearts",
    "Ocean Minds",
    "Sky Sparks",
    "Fire Wings",
    "Pink Clouds",
    "Sun Rays",
    "Night Dreams",
    "Green Aura",
    "White Souls",
]

TEAM_ID_TO_NAME = {
    name.strip().lower().replace(" ", "_"): name for name in TEAM_NAMES
}
TEAM_NAME_TO_ID = {v: k for k, v in TEAM_ID_TO_NAME.items()}


def _team_slug(value: Optional[str]) -> str:
    return (value or "").strip().lower().replace(" ", "_")


def _team_name_from_payload(team_name: Optional[str], team_id: Optional[str]) -> Optional[str]:
    if team_id:
        return TEAM_ID_TO_NAME.get(_team_slug(team_id))
    if team_name:
        raw = team_name.strip()
        for valid in TEAM_NAMES:
            if valid.lower() == raw.lower():
                return valid
        return TEAM_ID_TO_NAME.get(_team_slug(raw))
    return None


def _team_visuals(team_slug: str):
    return {
        "logoUrl": f"ahira://team/{team_slug}/logo",
        "logo_url": f"ahira://team/{team_slug}/logo",
        "bannerUrl": f"ahira://team/{team_slug}/banner",
        "banner_url": f"ahira://team/{team_slug}/banner",
        "flagUrl": f"ahira://team/{team_slug}/flag",
        "flag_url": f"ahira://team/{team_slug}/flag",
    }


def _leaderboard_cache_ttl_expired(generated_at: Optional[datetime], ttl_seconds: int = 30) -> bool:
    if generated_at is None:
        return True
    if generated_at.tzinfo is not None:
        generated_at = generated_at.replace(tzinfo=None)
    return (datetime.utcnow() - generated_at).total_seconds() > ttl_seconds


def _team_member_counts_sql() -> str:
    return """
        SELECT team_id, COUNT(*) AS member_count
        FROM user_profiles
        WHERE team_id IS NOT NULL
        GROUP BY team_id
    """


def _team_leaderboard_query_sql() -> str:
    return f"""
        SELECT
          t.id,
          t.name,
          t.logo_url,
          t.banner_url,
          t.member_count AS cached_member_count,
          COALESCE(tm.member_count, t.member_count, 0) AS member_count,
          COALESCE(st.total_points, t.total_points, 0) AS season_points,
          COALESCE(t.total_points, 0) AS total_points,
          COALESCE(t.season_wins, 0) AS season_wins,
          COALESCE(st.rank, 0) AS cached_rank
        FROM teams t
        LEFT JOIN seasons s ON s.season_code = :sid
        LEFT JOIN season_team_stats st
          ON st.team_id = t.id AND st.season_id = s.id
        LEFT JOIN (
            {_team_member_counts_sql()}
        ) tm ON tm.team_id = t.id
        ORDER BY COALESCE(st.total_points, t.total_points, 0) DESC, t.name ASC
        LIMIT :lim
    """


def _team_leaderboard_item(row: dict, rank: int):
    slug = _team_slug(str(row["name"]))
    season_points = int(row["season_points"] or 0)
    total_points = int(row["total_points"] or 0)
    member_count = int(row["member_count"] or 0)
    return {
        "rank": rank,
        "id": slug,
        "teamId": slug,
        "team_id": slug,
        "numericId": int(row["id"]),
        "name": row["name"],
        "teamName": row["name"],
        "points": season_points,
        "totalPoints": total_points,
        "seasonPoints": season_points,
        "season_points": season_points,
        "wins": int(row["season_wins"] or 0),
        "seasonWins": int(row["season_wins"] or 0),
        "memberCount": member_count,
        "member_count": member_count,
        "logoUrl": row["logo_url"] or f"ahira://team/{slug}/logo",
        "logo_url": row["logo_url"] or f"ahira://team/{slug}/logo",
        "bannerUrl": row["banner_url"] or f"ahira://team/{slug}/banner",
        "banner_url": row["banner_url"] or f"ahira://team/{slug}/banner",
        "flagUrl": f"ahira://team/{slug}/flag",
        "flag_url": f"ahira://team/{slug}/flag",
    }


def _read_fresh_team_leaderboard_cache(db: Session, season_code: str, limit: int):
    row = db.execute(
        text(
            """
            SELECT payload, generated_at
            FROM leaderboard_cache
            WHERE scope = 'team' AND season_id = :sid AND game_id IS NULL
            LIMIT 1
            """
        ),
        {"sid": season_code},
    ).mappings().first()
    if not row or _leaderboard_cache_ttl_expired(row["generated_at"]):
        return None
    payload = row["payload"]
    if not isinstance(payload, list) or not payload:
        return None
    items = []
    for idx, item in enumerate(payload[:limit], start=1):
        if isinstance(item, dict):
            items.append(item)
    return items if items else None


def _refresh_team_leaderboard_cache(db: Session, season_code: str, limit: int):
    rows = db.execute(
        text(_team_leaderboard_query_sql()),
        {"sid": season_code, "lim": limit},
    ).mappings().all()
    items = [_team_leaderboard_item(row, index) for index, row in enumerate(rows, start=1)]
    db.execute(
        text(
            """
            INSERT INTO leaderboard_cache (scope, season_id, game_id, payload, generated_at, updated_at)
            VALUES ('team', :sid, NULL, CAST(:payload AS JSONB), NOW(), NOW())
            ON CONFLICT (scope, season_id, game_id)
            DO UPDATE SET payload = EXCLUDED.payload, generated_at = EXCLUDED.generated_at, updated_at = NOW()
            """
        ),
        {"sid": season_code, "payload": json.dumps(items)},
    )
    return items


def _get_team_leaderboard(db: Session, season_code: str, limit: int, *, allow_cache: bool = True):
    if allow_cache:
        cached = _read_fresh_team_leaderboard_cache(db, season_code, limit)
        if cached is not None:
            print(
                f"[leaderboard.team] cache_hit season_id={season_code} rows={len(cached)}"
            )
            return cached, True
    print(f"[leaderboard.team] cache_miss season_id={season_code}")
    items = _refresh_team_leaderboard_cache(db, season_code, limit)
    print(
        f"[leaderboard.team] recalculated season_id={season_code} rows={len(items)}"
    )
    return items, False


def _resolve_submission_team(db: Session, user_id: int):
    row = db.execute(
        text(
            """
            SELECT team_id, selected_team_id, selected_team_name
            FROM user_profiles
            WHERE user_id = :uid
            """
        ),
        {"uid": user_id},
    ).mappings().first()
    if not row:
        return None

    team_id = row["team_id"]
    if team_id is not None:
        team = db.execute(
            text("SELECT id, name FROM teams WHERE id = :tid"),
            {"tid": team_id},
        ).mappings().first()
        if team:
            return int(team["id"]), str(team["name"])

    team_name = _team_name_from_payload(row["selected_team_name"], row["selected_team_id"])
    if team_name:
        team = db.execute(
            text("SELECT id, name FROM teams WHERE name = :name"),
            {"name": team_name},
        ).mappings().first()
        if team:
            db.execute(
                text(
                    """
                    UPDATE user_profiles
                    SET team_id = :tid,
                        selected_team_id = :selected_team_id,
                        selected_team_name = :selected_team_name,
                        updated_at = NOW()
                    WHERE user_id = :uid
                    """
                ),
                {
                    "uid": user_id,
                    "tid": team["id"],
                    "selected_team_id": _team_slug(team["name"]),
                    "selected_team_name": team["name"],
                },
            )
            return int(team["id"]), str(team["name"])
    return None


def _profile_payload(db: Session, user):
    db.execute(
        text("INSERT INTO user_profiles (user_id) VALUES (:uid) ON CONFLICT (user_id) DO NOTHING"),
        {"uid": user.id},
    )
    db.commit()
    row = db.execute(
        text(
            """
            SELECT up.user_id, up.team_id, up.team_change_count, up.team_selected_at,
                   up.selected_team_id, up.selected_team_name, up.created_at, up.updated_at,
                   t.name AS team_name
            FROM user_profiles up
            LEFT JOIN teams t ON up.team_id = t.id
            WHERE up.user_id = :uid
            """
        ),
        {"uid": user.id},
    ).mappings().first()
    if not row:
        return None, None
    team_name = (row["selected_team_name"] or row["team_name"] or "").strip()
    team_slug = (row["selected_team_id"] or _team_slug(team_name)).strip()
    selected_team = None
    if team_name and team_slug:
        selected_team = {
            "id": team_slug,
            "teamId": team_slug,
            "name": team_name,
            "teamName": team_name,
            **_team_visuals(team_slug),
        }
    profile = {
        "user_id": row["user_id"],
        "userId": row["user_id"],
        "team_id": team_slug or None,
        "teamId": team_slug or None,
        "team_name": team_name or None,
        "teamName": team_name or None,
        "team_change_count": int(row["team_change_count"] or 0),
        "teamChangeCount": int(row["team_change_count"] or 0),
        "team_selected_at": row["team_selected_at"].isoformat() if row["team_selected_at"] else None,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }
    return profile, selected_team


def _season_id(now: Optional[datetime] = None) -> str:
    dt = now or datetime.utcnow()
    return dt.strftime("%Y-%m")


def _ensure_season_row(db: Session, season_code: str):
    try:
        year_s, month_s = season_code.split("-")
        year = int(year_s)
        month = int(month_s)
    except Exception:
        now = datetime.utcnow()
        year = now.year
        month = now.month
        season_code = f"{year}-{str(month).zfill(2)}"
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    db.execute(
        text(
            """
            INSERT INTO seasons (season_code, start_date, end_date, is_active)
            VALUES (:season_code, :start_date, :end_date, TRUE)
            ON CONFLICT (season_code) DO NOTHING
            """
        ),
        {
            "season_code": season_code,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def _day_key(now: Optional[datetime] = None) -> str:
    dt = now or datetime.utcnow()
    return dt.strftime("%Y-%m-%d")


def _safe_iso_datetime(value: Optional[str], fallback: Optional[datetime] = None) -> datetime:
    if not value:
        return fallback or datetime.utcnow()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return fallback or datetime.utcnow()


def _mongo_oid(value: str):
    try:
        return ObjectId(value)
    except Exception:
        return None


def _feed_actor_name(user):
    if not user:
        return "Guest"
    return (user.name or "User").strip()[:100]


def _mongo_reaction_key(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    low = v.lower()
    if low == "feltthis":
        return "feltThis"
    return low if low in {"relate", "hug", "support"} else None


def _post_counts_from_mongo(post_id: str):
    post_key = _mongo_post_id_from_any(post_id)
    comments_col = mongo.get_collection("community_comments")
    reactions_col = mongo.get_collection("community_reactions")
    counts = {"relate": 0, "hug": 0, "support": 0, "feltThis": 0}
    comments_count = 0
    if comments_col is not None:
        comments_count = int(comments_col.count_documents({"post_id": post_key, "deleted": {"$ne": True}}))
    if reactions_col is not None:
        stats_cursor = reactions_col.aggregate(
            [
                {"$match": {"post_id": post_key}},
                {"$group": {"_id": "$reaction", "count": {"$sum": 1}}},
            ]
        )
        for row in stats_cursor:
            rk = _mongo_reaction_key(row.get("_id"))
            if rk in counts:
                counts[rk] = int(row.get("count") or 0)
    return comments_count, counts


def _sync_post_counters_mongo(post_id: str):
    posts_col = mongo.get_collection("community_posts")
    if posts_col is None:
        return None
    comments_count, reactions = _post_counts_from_mongo(post_id)
    posts_col.update_one(
        {"_id": _mongo_oid(_mongo_post_id_from_any(post_id))},
        {
            "$set": {
                "comment_count": comments_count,
                "comments_count": comments_count,
                "reactions": reactions,
                "updated_at": datetime.utcnow(),
            }
        },
    )
    return {"commentCount": comments_count, "reactions": reactions}


def _log_social_activity(post_id: str, actor_user_id: Optional[int], title: str, subtitle: str):
    posts_col = mongo.get_collection("community_posts")
    activity_col = mongo.get_collection("activity_feed")
    if posts_col is None or activity_col is None:
        return
    post = posts_col.find_one({"_id": _mongo_oid(_mongo_post_id_from_any(post_id))}) or {}
    author_id = post.get("author_user_id")
    if author_id is None:
        return
    if actor_user_id is not None and int(actor_user_id) == int(author_id):
        return
    activity_col.insert_one(
        {
            "user_id": int(author_id),
            "visibility": "private",
            "kind": "social",
            "title": title,
            "subtitle": subtitle,
            "post_id": _mongo_post_id_from_any(post_id),
            "created_at": datetime.utcnow(),
        }
    )


def _anti_cheat_flags(db: Session, user_id: int, game_id: str, score: int, idempotency_key: str):
    flags = []
    # Lightweight score thresholds; keep permissive and flag-only.
    max_score_by_game = {
        "quiz": 100000,
        "memory": 500000,
        "runner": 1000000,
    }
    threshold = max_score_by_game.get(game_id, 1000000)
    if score > threshold or score < 0:
        flags.append("impossible_score")

    recent_count = db.execute(
        text(
            """
            SELECT COUNT(*) AS c
            FROM game_score_submissions
            WHERE user_id = :user_id
              AND game_id = :game_id
              AND created_at > NOW() - INTERVAL '30 seconds'
            """
        ),
        {"user_id": user_id, "game_id": game_id},
    ).mappings().first()
    if int(recent_count["c"] or 0) >= 5:
        flags.append("suspicious_frequency")

    dup = db.execute(
        text(
            """
            SELECT 1
            FROM game_score_submissions
            WHERE user_id = :user_id AND idempotency_key = :idempotency_key
            LIMIT 1
            """
        ),
        {"user_id": user_id, "idempotency_key": idempotency_key},
    ).first()
    if dup:
        flags.append("duplicate_idempotency_key")

    return flags


def _refresh_season_team_stats(db: Session, season_code: str):
    season = db.execute(
        text("SELECT id FROM seasons WHERE season_code = :sid LIMIT 1"),
        {"sid": season_code},
    ).mappings().first()
    if not season:
        return
    sid = int(season["id"])
    db.execute(
        text(
            """
            INSERT INTO season_team_stats (season_id, team_id, total_points, wins, rank, updated_at, created_at)
            SELECT :season_id, t.id, COALESCE(SUM(h.points), 0), 0, NULL, NOW(), NOW()
            FROM teams t
            LEFT JOIN contribution_history h
              ON h.team_id = t.id AND h.season_id = :season_code
            GROUP BY t.id
            ON CONFLICT (season_id, team_id)
            DO UPDATE SET total_points = EXCLUDED.total_points, updated_at = NOW()
            """
        ),
        {"season_id": sid, "season_code": season_code},
    )
    ranked = db.execute(
        text(
            """
            SELECT team_id, total_points,
                   ROW_NUMBER() OVER (ORDER BY total_points DESC, team_id ASC) AS rnk
            FROM season_team_stats
            WHERE season_id = :sid
            """
        ),
        {"sid": sid},
    ).mappings().all()
    for row in ranked:
        db.execute(
            text("UPDATE season_team_stats SET rank = :rnk, updated_at = NOW() WHERE season_id = :sid AND team_id = :tid"),
            {"rnk": int(row["rnk"]), "sid": sid, "tid": int(row["team_id"])},
        )


def _require_user(request: Request, db: Session):
    user = current_user(request, db)
    if not user:
        return None, JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)
    return user, None


def _fallback_generated_posts(lang: str):
    lines = {
        "en": [
            "Small progress bhi important hota hai 🌸",
            "Aaj finally khud ke liye time nikala ✨",
            "Kal se better feel ho raha hai 🌙",
            "Happiness thodi thodi karke bhi aati hai 🤍",
        ],
        "hi": [
            "आज थोड़ा आराम किया, मन हल्का लगा 🤍",
            "छोटी जीत भी बड़ी होती है, खुद पर भरोसा रखो ✨",
            "धीरे चलना भी आगे बढ़ना है 🌸",
            "आज खुद के लिए समय निकाला, अच्छा लगा 🌙",
        ],
    }
    chosen = lines.get(lang, lines["en"])
    now = datetime.utcnow()
    out = []
    for idx, text_line in enumerate(chosen):
        out.append(
            {
                "kind": "generated",
                "language": lang,
                "content": text_line,
                "category": ["self care", "healing", "motivation", "peaceful thoughts"][idx % 4],
                "mood": "calm",
                "anonymous_identity": ["🌸 Soft Soul", "☁️ Quiet Mind", "🤍 Hidden Hug", "✨ Lost Dreamer"][idx % 4],
                "created_at": now - timedelta(minutes=idx * 17),
                "expires_at": now + timedelta(hours=24),
                "engagement_score": 40 + (idx * 9),
                "trending_score": 20 + (idx * 7),
                "reactions": {"relate": 10 + idx, "hug": 8 + idx, "support": 6 + idx, "feltThis": 9 + idx},
                "comment_count": 2 + idx,
            }
        )
    return out


_GENERATED_IDENTITIES = [
    "🌸 Soft Soul",
    "☁️ Quiet Mind",
    "🤍 Hidden Hug",
    "✨ Lost Dreamer",
    "🌙 Midnight Girl",
    "🫧 Gentle Bloom",
    "🌧️ Tender Rain",
    "🕯️ Silent Heart",
]


def _generated_identity_for(day_key: str, lang: str, idx: int, content: str) -> str:
    seed = f"{day_key}|{lang}|{idx}|{content.strip().lower()}"
    digest = hashlib.sha256(seed.encode()).hexdigest()
    offset = int(digest[:8], 16) % len(_GENERATED_IDENTITIES)
    return _GENERATED_IDENTITIES[(idx + offset) % len(_GENERATED_IDENTITIES)]


def _refresh_generated_posts(lang: str):
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return _fallback_generated_posts(lang)
    print(
        f"[OpenRouter.fun] API KEY FOUND model={OPENROUTER_DEFAULT_MODEL} "
        f"candidateCount={len(_openrouter_model_candidates())}"
    )
    prompt = (
        "Generate 6 short emotional community posts for Indian women users. "
        "Language mix based on lang input. Keep simple words, warm tone, under 100 chars. "
        "Return strict JSON array with fields content,category,mood,anonymous_identity."
    )

    import json

    seen = set()
    for model in _openrouter_model_candidates():
        model = (model or "").strip()
        if not model or model in seen:
            continue
        seen.add(model)
        try:
            request_body = {
                "model": model,
                "messages": [{"role": "user", "content": f"{prompt} lang={lang}"}],
                "temperature": 0.8,
                "max_tokens": 420,
            }
            started_at = datetime.utcnow()
            print(
                f"[OpenRouter.fun] OPENROUTER REQUEST START model={model} lang={lang} "
                f"bodyChars={len(json.dumps(request_body, ensure_ascii=False))}"
            )
            r = OPENROUTER_SESSION.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://ahira.app",
                    "X-Title": "Ahira",
                    "X-OpenRouter-Title": "Ahira",
                },
                json=request_body,
                timeout=(OPENROUTER_CONNECT_TIMEOUT_SECONDS, OPENROUTER_TIMEOUT_SECONDS),
            )
            elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            print(f"[OpenRouter.fun] RESPONSE STATUS={r.status_code} RESPONSE TIME={elapsed_ms}ms model={model}")
            if r.status_code < 200 or r.status_code >= 300:
                print(f"[OpenRouter.fun] ERROR DETAILS non_2xx body={(r.text or '')[:240]}")
                continue
            decoded = r.json() if r.content else {}
            content = (((decoded.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            start = content.find("[")
            end = content.rfind("]")
            if start < 0 or end <= start:
                print(f"[OpenRouter.fun] ERROR DETAILS invalid_content model={model}")
                continue
            data = json.loads(content[start : end + 1])
            now = datetime.utcnow()
            out = []
            for idx, row in enumerate(data[:6]):
                content_text = str(row.get("content", "")).strip()
                out.append(
                    {
                        "kind": "generated",
                        "language": lang,
                        "content": content_text,
                        "category": str(row.get("category", "motivation")).strip().lower(),
                        "mood": str(row.get("mood", "calm")).strip().lower(),
                        "anonymous_identity": str(row.get("anonymous_identity", "")).strip(),
                        "created_at": now - timedelta(minutes=idx * 13),
                        "expires_at": now + timedelta(hours=24),
                        "engagement_score": 30 + (idx * 8),
                        "trending_score": 18 + (idx * 6),
                        "reactions": {"relate": 7 + idx, "hug": 5 + idx, "support": 6 + idx, "feltThis": 8 + idx},
                        "comment_count": 1 + idx,
                    }
                )
            items = [x for x in out if x["content"]]
            if items:
                print(f"[generated_posts] OpenRouter model={model} rows={len(items)}")
                return items
        except Exception as exc:
            print(f"[generated_posts] ERROR DETAILS model={model} error={exc}")
            continue
    return _fallback_generated_posts(lang)


def _ensure_generated_posts(lang: str):
    col = mongo.get_collection("generated_daily_posts")
    if col is None:
        return _fallback_generated_posts(lang)
    now = datetime.utcnow()
    day_key = now.strftime("%Y-%m-%d")
    q = {"language": lang, "day_key": day_key, "expires_at": {"$gt": now}}
    rows = list(col.find(q).sort("created_at", -1).limit(20))
    if rows:
        unique_identities = {
            str(r.get("anonymous_identity", "")).strip()
            for r in rows
            if str(r.get("anonymous_identity", "")).strip()
        }
        if len(rows) > 1 and len(unique_identities) <= 1:
            for idx, row in enumerate(rows):
                fixed_identity = _generated_identity_for(
                    day_key,
                    lang,
                    idx,
                    str(row.get("content", "")),
                )
                col.update_one(
                    {"_id": row["_id"]},
                    {"$set": {"anonymous_identity": fixed_identity}},
                )
                row["anonymous_identity"] = fixed_identity
        return rows
    fresh = _refresh_generated_posts(lang)
    if not fresh:
        return []
    docs = []
    for idx, row in enumerate(fresh):
        payload = dict(row)
        payload["day_key"] = day_key
        payload["created_at"] = payload.get("created_at") or now
        payload["expires_at"] = payload.get("expires_at") or (now + timedelta(hours=24))
        payload["anonymous_identity"] = _generated_identity_for(
            day_key,
            lang,
            idx,
            str(payload.get("content", "")),
        )
        docs.append(payload)
    try:
        col.insert_many(docs)
    except Exception:
        pass
    return docs


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _normalize_emoji_value(value: str) -> str:
    normalized = unicodedata.normalize("NFC", (value or "").strip())
    return RECOVERY_EMOJI_ALIASES.get(normalized, normalized)


def _normalize_emoji_sequence(values: list[str]) -> list[str]:
    return [_normalize_emoji_value(value) for value in values]


def _emoji_sequence_preview(sequence: list[str]) -> str:
    return " • ".join(_normalize_emoji_sequence(sequence))


def _emoji_sequence_exact_payload(sequence: list[str]) -> str:
    return "".join(_normalize_emoji_sequence(sequence))


def _emoji_recovery_key(sequence: list[str]) -> tuple[Optional[str], list[str]]:
    normalized = _normalize_emoji_sequence(sequence)
    codes: list[str] = []
    for emoji in normalized:
        code = RECOVERY_EMOJI_MAP.get(emoji)
        if not code:
            return None, normalized
        codes.append(code)
    return "-".join(codes), normalized


def _hash_recovery_key(sequence: list[str]) -> tuple[Optional[str], Optional[str], list[str]]:
    recovery_key, normalized = _emoji_recovery_key(sequence)
    if not recovery_key:
        return None, None, normalized
    return _sha256_text(recovery_key), recovery_key, normalized


def _validate_emoji_sequence(values: list[str]) -> tuple[bool, str, list[str]]:
    if not isinstance(values, list):
        return False, "Emoji sequence is required.", []
    normalized = _normalize_emoji_sequence(values)
    if len(normalized) != RECOVERY_EMOJI_COUNT:
        return False, "Please choose exactly 4 emojis.", []
    if any(not emoji for emoji in normalized):
        return False, "Please choose exactly 4 emojis.", []
    unsupported = [emoji for emoji in normalized if emoji not in RECOVERY_EMOJI_MAP]
    if unsupported:
        return False, "Please choose emojis from the recovery picker.", []
    return True, "", normalized


def _emoji_sequence_payload(sequence: list[str]) -> str:
    normalized = _normalize_emoji_sequence(sequence)
    return _emoji_sequence_exact_payload(normalized)


def _legacy_emoji_sequence_payload(sequence: list[str]) -> str:
    return json.dumps(_normalize_emoji_sequence(sequence), ensure_ascii=False, separators=(",", ":"))


def _legacy_pipe_emoji_sequence_payload(sequence: list[str]) -> str:
    return "|".join(_normalize_emoji_sequence(sequence))


def _hash_emoji_sequence(sequence: list[str], salt: Optional[bytes] = None) -> str:
    normalized = _normalize_emoji_sequence(sequence)
    salt_bytes = salt or secrets.token_bytes(16)
    payload = _emoji_sequence_exact_payload(normalized).encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", payload, salt_bytes, 210000)
    return "pbkdf2_sha256$210000${}${}".format(
        salt_bytes.hex(),
        derived.hex(),
    )


def _verify_emoji_hash(sequence: list[str], stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(iterations)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except Exception:
        return False

    normalized = _normalize_emoji_sequence(sequence)
    payloads = [
        _emoji_sequence_exact_payload(normalized).encode("utf-8"),
        _emoji_sequence_payload(normalized).encode("utf-8"),
        _legacy_pipe_emoji_sequence_payload(normalized).encode("utf-8"),
        _legacy_emoji_sequence_payload(normalized).encode("utf-8"),
    ]
    for payload in payloads:
        actual = hashlib.pbkdf2_hmac("sha256", payload, salt, rounds)
        if hmac.compare_digest(actual, expected):
            return True
    return False


def _verify_recovery_key_hash(sequence: list[str], stored_hash: str) -> tuple[bool, Optional[str], Optional[str]]:
    expected_hash, recovery_key, _ = _hash_recovery_key(sequence)
    stored = (stored_hash or "").strip()
    if not expected_hash or not stored:
        return False, recovery_key, expected_hash
    return hmac.compare_digest(expected_hash, stored), recovery_key, expected_hash


def _recovery_emojis_enabled(db: Session, user_id: int) -> bool:
    row = db.query(UserRecoveryEmoji.id).filter(UserRecoveryEmoji.user_id == user_id).first()
    return row is not None


def _recovery_reset_token_hash(token: str) -> str:
    return _sha256_text(token)


def _recovery_emoji_sequence_from_body(body) -> list[str]:
    sequence = getattr(body, "emoji_sequence", None)
    if sequence is None:
        sequence = getattr(body, "emojis", None)
    if isinstance(sequence, list):
        return sequence
    if isinstance(sequence, tuple):
        return list(sequence)
    return []


def _recovery_reset_token_from_body(body) -> str:
    token = getattr(body, "reset_token", None) or getattr(body, "temporary_reset_token", None)
    return (token or "").strip()


def _ensure_recovery_emoji_schema(db: Session):
    db.execute(
        text(
            """
            ALTER TABLE user_recovery_emojis
            ADD COLUMN IF NOT EXISTS hashed_recovery_key TEXT
            """
        )
    )
    db.execute(
        text(
            """
            ALTER TABLE user_recovery_emojis
            ADD COLUMN IF NOT EXISTS recovery_enabled BOOLEAN NOT NULL DEFAULT TRUE
            """
        )
    )
    db.execute(
        text(
            """
            ALTER TABLE user_recovery_emojis
            ADD COLUMN IF NOT EXISTS emoji_sequence_hash TEXT
            """
        )
    )
    db.execute(
        text(
            """
            ALTER TABLE user_recovery_emojis
            ADD COLUMN IF NOT EXISTS emoji_sequence_preview TEXT
            """
        )
    )
    db.execute(
        text(
            """
            ALTER TABLE user_recovery_emojis
            ADD COLUMN IF NOT EXISTS emoji_hash TEXT
            """
        )
    )
    db.execute(
        text(
            """
            UPDATE user_recovery_emojis
            SET emoji_sequence_hash = COALESCE(emoji_sequence_hash, emoji_hash),
                emoji_hash = COALESCE(emoji_hash, emoji_sequence_hash)
            WHERE emoji_sequence_hash IS NULL OR emoji_hash IS NULL
            """
        )
    )


def _issue_temporary_reset_token(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = _recovery_reset_token_hash(token)
    expires_at = datetime.utcnow() + timedelta(minutes=RECOVERY_TOKEN_TTL_MINUTES)
    db.execute(
        text("UPDATE password_reset_tokens SET used = TRUE WHERE user_id = :uid AND used = FALSE"),
        {"uid": user_id},
    )
    db.execute(
        text(
            """
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, used, created_at)
            VALUES (:uid, :token_hash, :expires_at, FALSE, NOW())
        """
        ),
        {"uid": user_id, "token_hash": token_hash, "expires_at": expires_at},
    )
    return token


def _find_valid_reset_token(db: Session, token: str):
    token_hash = _recovery_reset_token_hash(token)
    return db.execute(
        text(
            """
            SELECT id, user_id, expires_at, used
            FROM password_reset_tokens
            WHERE token_hash = :token_hash
              AND used = FALSE
              AND expires_at > NOW()
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"token_hash": token_hash},
    ).mappings().first()


def _finalize_reset_token(db: Session, token_id: int, user_id: int):
    db.execute(
        text(
            """
            UPDATE password_reset_tokens
            SET used = TRUE
            WHERE id = :token_id OR user_id = :uid
            """
        ),
        {"token_id": token_id, "uid": user_id},
    )


def _session_response_payload(db: Session, user):
    profile, selected_team = _profile_payload(db, user)
    return {
        "status": "ok",
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "profile": profile,
        "selected_team": selected_team,
        "selectedTeam": selected_team,
        "team_change_count": profile["team_change_count"] if profile else 0,
        "teamChangeCount": profile["teamChangeCount"] if profile else 0,
        "recovery_setup_required": not _recovery_emojis_enabled(db, user.id),
    }


def _send_password_reset_email(email: str, token: str):
    app_url = os.getenv("APP_PUBLIC_URL", "https://ahira.app").rstrip("/")
    reset_link = f"{app_url}/reset-password?email={email}&token={token}"
    subject = "Ahira Password Reset"
    body_text = (
        "We received a request to reset your Ahira password.\n\n"
        f"Reset link (valid for 15 minutes): {reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )

    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    if resend_key:
        from_email = os.getenv("RESEND_FROM_EMAIL", "Ahira <no-reply@ahira.app>")
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [email],
                "subject": subject,
                "text": body_text,
            },
            timeout=10,
        )
        if 200 <= r.status_code < 300:
            return
        raise RuntimeError(f"resend_status_{r.status_code}")

    sendgrid_key = os.getenv("SENDGRID_API_KEY", "").strip()
    if sendgrid_key:
        from_email = os.getenv("SENDGRID_FROM_EMAIL", "no-reply@ahira.app")
        r = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {sendgrid_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": email}]}],
                "from": {"email": from_email, "name": "Ahira"},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body_text}],
            },
            timeout=10,
        )
        if 200 <= r.status_code < 300:
            return
        raise RuntimeError(f"sendgrid_status_{r.status_code}")

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_user or "no-reply@ahira.app")
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() == "true"

    if not smtp_host or not smtp_user or not smtp_password:
        raise RuntimeError("email_provider_not_configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = email
    msg.set_content(body_text)

    if smtp_use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ssl.create_default_context(), timeout=10) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(smtp_user, smtp_password)
            server.send_message(msg)


def _openrouter_chat_completion(messages: list[dict], timeout_seconds: int = OPENROUTER_TIMEOUT_SECONDS):
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    failover_history = []
    if not key:
        print("[OpenRouter] ❌ OPENROUTER_API_KEY missing; chat request cannot be sent")
        _set_openrouter_status(
            status="missing_key",
            current_model=OPENROUTER_DEFAULT_MODEL,
            last_provider_error="openrouter_api_key_missing",
            failover_history=failover_history,
        )
        raise RuntimeError("openrouter_api_key_missing")
    print(
        f"[OpenRouter] API KEY FOUND model={OPENROUTER_DEFAULT_MODEL} "
        f"candidateCount={len(_openrouter_model_candidates())} keyLength={len(key)} url={OPENROUTER_CHAT_URL}"
    )

    seen = set()
    last_error = None
    for model in _openrouter_model_candidates():
        model = (model or "").strip()
        if not model or model in seen:
            continue
        seen.add(model)
        request_body = {
            "model": model,
            "messages": messages,
            "temperature": 0.72,
            "max_tokens": 320,
        }
        for attempt in range(2):
            started_at = datetime.utcnow()
            try:
                print(
                    f"[OpenRouter] OPENROUTER REQUEST START MODEL USED={model} attempt={attempt + 1} "
                    f"messages={len(messages)} bodyChars={len(json.dumps(request_body, ensure_ascii=False))}"
                )
                print(
                    f"[OpenRouter] REQUEST BODY model={model} payload={json.dumps(request_body, ensure_ascii=False)[:400]}"
                )
                response = OPENROUTER_SESSION.post(
                    OPENROUTER_CHAT_URL,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.getenv("APP_PUBLIC_URL", "https://ahira.app"),
                        "X-Title": "Ahira",
                        "X-OpenRouter-Title": "Ahira",
                    },
                    json=request_body,
                    timeout=(OPENROUTER_CONNECT_TIMEOUT_SECONDS, min(timeout_seconds, OPENROUTER_TIMEOUT_SECONDS)),
                )
                elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
                print(
                    f"[OpenRouter] RESPONSE STATUS={response.status_code} RESPONSE TIME={elapsed_ms}ms MODEL USED={model}"
                )
                raw_text = response.text or ""
                if response.status_code < 200 or response.status_code >= 300:
                    last_error = RuntimeError(f"openrouter_http_{response.status_code}")
                    failover_history.append(
                        {
                            "model": model,
                            "attempt": attempt + 1,
                            "status_code": response.status_code,
                            "response_time_ms": elapsed_ms,
                            "success": False,
                            "error": f"openrouter_http_{response.status_code}",
                        }
                    )
                    print(
                        f"[OpenRouter] ERROR DETAILS model={model} failed status={response.status_code} "
                        f"afterMs={elapsed_ms} body={raw_text[:1200]}"
                    )
                    if attempt == 0 and response.status_code >= 500:
                        print(f"[OpenRouter] retry triggered model={model} reason=http_{response.status_code}")
                        continue
                    break
                try:
                    decoded = response.json() if response.content else {}
                except Exception as exc:
                    last_error = RuntimeError(f"openrouter_json_parse_failed: {exc}")
                    failover_history.append(
                        {
                            "model": model,
                            "attempt": attempt + 1,
                            "status_code": response.status_code,
                            "response_time_ms": elapsed_ms,
                            "success": False,
                            "error": str(last_error),
                        }
                    )
                    print(
                        f"[OpenRouter] parsing error model={model} error={exc} raw={raw_text[:1200]}"
                    )
                    break
                print(
                    f"[OpenRouter] RAW RESPONSE model={model} payload={json.dumps(decoded, ensure_ascii=False)[:500]}"
                )
                try:
                    content = _extract_openrouter_content(decoded if isinstance(decoded, dict) else {}, model)
                except Exception as exc:
                    last_error = exc
                    failover_history.append(
                        {
                            "model": model,
                            "attempt": attempt + 1,
                            "status_code": response.status_code,
                            "response_time_ms": elapsed_ms,
                            "success": False,
                            "error": str(exc),
                        }
                    )
                    print(
                        f"[OpenRouter] parsing error model={model} error={exc} raw={raw_text[:1200]}"
                    )
                    break
                usage = decoded.get("usage") if isinstance(decoded, dict) else None
                failover_history.append(
                    {
                        "model": model,
                        "attempt": attempt + 1,
                        "status_code": response.status_code,
                        "response_time_ms": elapsed_ms,
                        "success": True,
                        "error": None,
                    }
                )
                print(
                    f"[OpenRouter] model={model} success afterMs={elapsed_ms} usage={usage}"
                )
                _set_openrouter_status(
                    status="connected",
                    current_model=model,
                    last_successful_model=model,
                    last_response_time_ms=elapsed_ms,
                    last_provider_error=None,
                    failover_history=failover_history,
                )
                return {
                    "model": model,
                    "content": content,
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "raw_response": raw_text[:4000],
                    "decoded": decoded,
                    "failover_history": failover_history,
                }
            except Exception as exc:
                last_error = exc
                elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
                failover_history.append(
                    {
                        "model": model,
                        "attempt": attempt + 1,
                        "status_code": None,
                        "response_time_ms": elapsed_ms,
                        "success": False,
                        "error": str(exc),
                    }
                )
                print(
                    f"[OpenRouter] ERROR DETAILS model={model} attempt={attempt + 1} error={exc} "
                    f"stack={traceback.format_exc()}"
                )
                if attempt == 0:
                    print(f"[OpenRouter] retry triggered model={model} reason={exc}")
                    continue
                break

    _set_openrouter_status(
        status="failed",
        current_model=OPENROUTER_DEFAULT_MODEL,
        last_provider_error=str(last_error) if last_error else "all_models_failed",
        failover_history=failover_history,
    )
    raise RuntimeError(f"all_models_failed: {last_error}")


def _fallback_chat_reply(message: str) -> str:
    return "OpenRouter is unavailable right now. Please check AI diagnostics for the exact error."


def _chat_debug_payload(error: Optional[Exception], started_at: datetime):
    return {
        "status": "error",
        "message": "OpenRouter chat failed. Check backend logs or AI diagnostics.",
        "provider": "openrouter",
        "error": "all_models_failed",
        "used_fallback": False,
        "fallback_triggered": False,
        "fallback_reason": str(error) if error else "openrouter_unavailable",
        "models_tried": _openrouter_model_candidates(),
        "openrouter": _openrouter_status_payload(),
        "elapsed_ms": int((datetime.utcnow() - started_at).total_seconds() * 1000),
    }


def _safe_delete_sql(db: Session, sql: str, params: dict, label: str):
    try:
        with db.begin_nested():
            db.execute(text(sql), params)
    except Exception as exc:
        print(f"[account_cleanup] skipped {label}: {exc}")


def _delete_user_owned_postgres(db: Session, user_id: int, *, delete_user: bool = False):
    params = {"uid": user_id}
    user_tables = [
        "medicine_logs",
        "medicines",
        "grocery_items",
        "grocery_lists",
        "habit_logs",
        "user_habits",
        "planner_tasks",
        "water_tracking",
        "habit_tracking",
        "medicine_tracking",
        "daily_task_tracking",
        "wellness_stats",
        "wellness_logs",
        "water_logs",
        "user_goals",
        "user_streaks",
        "season_rewards",
        "scheduled_notifications",
        "ai_generations",
        "analytics_events",
        "notifications_metadata",
        "app_preferences",
        "user_settings",
        "streak_tracking",
        "achievement_progress",
        "user_badges",
        "user_achievements",
        "anti_cheat_flags",
        "game_sessions",
        "game_statistics",
        "user_game_progress",
        "team_contribution_history",
        "contribution_history",
        "game_score_submissions",
        "team_members",
        "sync_queue_receipts",
        "user_devices",
        "user_presence",
        "content_flags",
        "password_reset_tokens",
        "user_recovery_emojis",
        "feed_comments",
        "feed_reactions",
        "feed_user_posts",
        "reminders",
        "sessions",
        "user_profiles",
    ]
    for table in user_tables:
        _safe_delete_sql(db, f"DELETE FROM {table} WHERE user_id = :uid", params, table)
    _safe_delete_sql(
        db,
        "DELETE FROM moderation_logs WHERE moderator_user_id = :uid OR target_user_id = :uid",
        params,
        "moderation_logs",
    )
    db.execute(text("UPDATE teams SET member_count = (SELECT COUNT(*) FROM user_profiles WHERE team_id = teams.id), updated_at = NOW()"))
    if delete_user:
        db.query(User).filter(User.id == user_id).delete()


def _delete_user_owned_mongo(user_id: int):
    try:
        import ai.mongo as mongo_module

        authored_post_ids = []
        posts_col = mongo_module.get_collection("community_posts")
        if posts_col is not None:
            authored_post_ids = [
                row.get("_id")
                for row in posts_col.find({"author_user_id": user_id}, {"_id": 1})
                if row.get("_id") is not None
            ]
            posts_col.delete_many({"author_user_id": user_id})

        cleanup = {
            "reminder_logs": [{"user_id": user_id}],
            "chat_logs": [{"user_id": user_id}],
            "mood_logs": [{"user_id": user_id}],
            "community_comments": [{"user_id": user_id}],
            "community_reactions": [{"user_id": user_id}],
            "activity_feed": [{"user_id": user_id}],
            "generated_content": [{"user_id": user_id}],
            "engagement_tracking": [{"user_id": user_id}],
            "analytics_events": [{"user_id": user_id}],
        }
        if authored_post_ids:
            cleanup["community_comments"].append({"post_id": {"$in": authored_post_ids}})
            cleanup["community_reactions"].append({"post_id": {"$in": authored_post_ids}})

        for collection_name, queries in cleanup.items():
            col = mongo_module.get_collection(collection_name)
            if col is None:
                continue
            for query in queries:
                col.delete_many(query)
    except Exception as e:
        print(f"[account_cleanup] MongoDB cleanup error: {e}")


# ─────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/db-test", response_class=HTMLResponse)
async def db_test_page():
    with open("templates/db_test.html", "r") as f:
        return HTMLResponse(content=f.read())


# ─────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────
@app.post("/register")
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if not body.name.strip() or not body.email.strip() or not body.password:
        return JSONResponse({"status": "error", "message": "All fields are required."}, status_code=400)
    if len(body.password) < 6:
        return JSONResponse({"status": "error", "message": "Password must be at least 6 characters."}, status_code=400)

    user = crud.create_user(db, body.name, body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Email already registered."}, status_code=409)
    db.execute(text("INSERT INTO user_profiles (user_id) VALUES (:uid) ON CONFLICT (user_id) DO NOTHING"), {"uid": user.id})
    db.commit()

    token = crud.create_session(db, user.id)
    resp = JSONResponse(_session_response_payload(db, user))
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
    return resp


@app.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    email = (body.email or "").strip().lower()
    print(f"[Auth] LOGIN REQUEST START email={email or '<missing>'}")
    user = crud.get_user_by_email(db, email)
    print(f"[Auth] LOGIN USER LOOKUP found={bool(user)} email={email or '<missing>'}")
    password_ok = bool(user and user.check_password(body.password))
    print(f"[Auth] LOGIN PASSWORD CHECK ok={password_ok} email={email or '<missing>'}")
    if not password_ok:
        print(f"[Auth] LOGIN FAILED reason=bad_credentials email={email or '<missing>'}")
        return JSONResponse({"status": "error", "message": "Incorrect email or password."}, status_code=401)

    print(f"[Auth] LOGIN SESSION CREATE START user_id={user.id}")
    token = crud.create_session(db, user.id)
    print(f"[Auth] LOGIN SESSION CREATED user_id={user.id} token_issued={bool(token)}")
    resp = JSONResponse(_session_response_payload(db, user))
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
    print(f"[Auth] LOGIN RESPONSE READY user_id={user.id}")
    return resp


@app.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        crud.delete_session(db, token)
    resp = JSONResponse({"status": "ok"})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "guest"})
    return JSONResponse(_session_response_payload(db, user))


@app.get("/users/me")
def users_me(request: Request, db: Session = Depends(get_db)):
    return me(request, db)


@app.get("/users/me/profile")
def users_me_profile(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "guest"}, status_code=401)
    profile, selected_team = _profile_payload(db, user)
    return {
        "status": "ok",
        "profile": profile,
        "selected_team": selected_team,
        "team_change_count": profile["teamChangeCount"] if profile else 0,
    }


@app.post("/auth/setup-recovery-emojis")
def setup_recovery_emojis(body: RecoveryEmojiSetupBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)

    _ensure_recovery_emoji_schema(db)

    ok, message, sequence = _validate_emoji_sequence(body.emoji_sequence)
    if not ok:
        return JSONResponse({"status": "error", "message": message}, status_code=400)

    existing = db.query(UserRecoveryEmoji).filter(UserRecoveryEmoji.user_id == user.id).first()
    password_required = existing is not None
    if password_required:
        current_password = (body.current_password or "").strip()
        if not current_password or not user.check_password(current_password):
            return JSONResponse(
                {"status": "error", "message": "Password confirmation failed."},
                status_code=403,
            )

    hint = (body.recovery_hint or "").strip() or None
    recovery_key_hash, recovery_key, _ = _hash_recovery_key(sequence)
    if not recovery_key_hash:
        return JSONResponse(
            {"status": "error", "message": "Please choose emojis from the recovery picker."},
            status_code=400,
        )
    emoji_hash = _hash_emoji_sequence(sequence)
    emoji_preview = _emoji_sequence_preview(sequence)
    now = datetime.utcnow()
    if existing:
        existing.hashed_recovery_key = recovery_key_hash
        existing.recovery_enabled = True
        existing.emoji_sequence_hash = emoji_hash
        existing.emoji_sequence_preview = emoji_preview
        existing.emoji_hash = emoji_hash
        existing.recovery_hint = hint
        existing.failed_attempts = 0
        existing.locked_until = None
        existing.updated_at = now
    else:
        existing = UserRecoveryEmoji(
            user_id=user.id,
            hashed_recovery_key=recovery_key_hash,
            recovery_enabled=True,
            emoji_sequence_hash=emoji_hash,
            emoji_sequence_preview=emoji_preview,
            emoji_hash=emoji_hash,
            recovery_hint=hint,
            failed_attempts=0,
            locked_until=None,
            created_at=now,
            updated_at=now,
        )
        db.add(existing)
    db.commit()
    print(
        "[Recovery] SETUP SAVED "
        f"user_id={user.id} recovery_key={recovery_key} "
        f"hashed_recovery_key_prefix={recovery_key_hash[:12]}"
    )
    return {
        "status": "ok",
        "message": "Recovery emojis saved.",
        "recovery_setup_required": False,
    }


@app.post("/auth/forgot-password")
def forgot_password(body: ForgotPasswordBody, db: Session = Depends(get_db)):
    return JSONResponse(
        {
            "status": "error",
            "message": "Password recovery now uses emoji phrases.",
        },
        status_code=410,
    )


@app.post("/auth/verify-reset")
def verify_reset(body: VerifyResetBody, db: Session = Depends(get_db)):
    return JSONResponse(
        {
            "status": "error",
            "message": "Password recovery now uses emoji phrases.",
        },
        status_code=410,
    )


@app.post("/auth/reset-password")
def reset_password(body: ResetPasswordBody, db: Session = Depends(get_db)):
    return JSONResponse(
        {
            "status": "error",
            "message": "Password recovery now uses emoji phrases.",
        },
        status_code=410,
    )


@app.post("/auth/verify-recovery-emojis")
def verify_recovery_emojis(body: RecoveryEmojiVerifyBody, db: Session = Depends(get_db)):
    print("[Recovery] RECOVERY VERIFY START")
    try:
        _ensure_recovery_emoji_schema(db)
        email = (body.email or "").strip().lower()
        print(f"[Recovery] REQUEST START email={email or '<missing>'}")
        if not email:
            print("[Recovery] REQUEST FAILED reason=email_missing")
            return JSONResponse(
                {"success": False, "status": "error", "message": "Email is required."},
                status_code=400,
            )

        raw_sequence = _recovery_emoji_sequence_from_body(body)
        ok, message, sequence = _validate_emoji_sequence(raw_sequence)
        if not ok:
            print(
                "[Recovery] REQUEST FAILED reason=invalid_sequence "
                f"received_count={len(raw_sequence) if isinstance(raw_sequence, list) else 0}"
            )
            return JSONResponse(
                {"success": False, "status": "error", "message": message},
                status_code=400,
            )
        print(f"[Recovery] EMOJI SEQUENCE RECEIVED email={email} count={len(sequence)}")
        print(f"[Recovery] NORMALIZED SEQUENCE value={_emoji_sequence_payload(sequence)}")
        generated_hash, generated_key, _ = _hash_recovery_key(sequence)
        print(
            "[Recovery] GENERATED RECOVERY KEY "
            f"key={generated_key or '<invalid>'} "
            f"hash_prefix={(generated_hash or '')[:12]} hash_generated={bool(generated_hash)}"
        )

        user = crud.get_user_by_email(db, email)
        print(f"[Recovery] USER FOUND found={bool(user)} email={email}")
        if not user:
            print("[Recovery] REQUEST FAILED reason=user_not_found")
            return JSONResponse(
                {
                    "success": False,
                    "status": "error",
                    "message": "Incorrect recovery emojis",
                },
                status_code=401,
            )

        recovery = db.query(UserRecoveryEmoji).filter(UserRecoveryEmoji.user_id == user.id).first()
        print(f"[Recovery] RECOVERY ROW FOUND found={bool(recovery)} user_id={user.id}")
        if not recovery:
            print("[Recovery] REQUEST FAILED reason=recovery_not_configured")
            return JSONResponse(
                {
                    "success": False,
                    "status": "error",
                    "message": "Recovery emojis not set up yet.",
                },
                status_code=404,
            )

        now = datetime.utcnow()
        if recovery.locked_until and recovery.locked_until > now:
            remaining = max(1, int((recovery.locked_until - now).total_seconds() // 60) + 1)
            print(
                "[Recovery] LOCK STATUS locked=True "
                f"email={email} locked_until={recovery.locked_until.isoformat()} remaining_minutes={remaining}"
            )
            return JSONResponse(
                {
                    "success": False,
                    "status": "error",
                    "message": f"Recovery temporarily locked. Try again in about {remaining} minute(s).",
                    "locked_until": recovery.locked_until.isoformat(),
                },
                status_code=429,
            )
        print(
            "[Recovery] LOCK STATUS locked=False "
            f"email={email} failed_attempts={int(recovery.failed_attempts or 0)}"
        )

        print("[Recovery] HASH CHECK START")
        stored_key_hash = (recovery.hashed_recovery_key or "").strip()
        legacy_hash = (recovery.emoji_sequence_hash or recovery.emoji_hash or "").strip()
        print(
            "[Recovery] STORED HASH READY "
            f"has_recovery_key_hash={bool(stored_key_hash)} "
            f"has_new_hash={bool((recovery.emoji_sequence_hash or '').strip())} "
            f"has_legacy_hash={bool((recovery.emoji_hash or '').strip())} "
            f"recovery_enabled={bool(getattr(recovery, 'recovery_enabled', True))} "
            f"preview={recovery.emoji_sequence_preview or ''}"
        )
        hash_ok, recovery_key, recovery_key_hash = _verify_recovery_key_hash(sequence, stored_key_hash)
        legacy_hash_ok = False
        if not hash_ok and legacy_hash:
            legacy_hash_ok = _verify_emoji_hash(sequence, legacy_hash)
            hash_ok = legacy_hash_ok
        print(
            "[Recovery] HASH CHECK RESULT "
            f"matched={hash_ok} deterministic_matched={bool(stored_key_hash and hash_ok and not legacy_hash_ok)} "
            f"legacy_matched={legacy_hash_ok}"
        )
        if hash_ok:
            if recovery_key_hash and recovery.hashed_recovery_key != recovery_key_hash:
                recovery.hashed_recovery_key = recovery_key_hash
                recovery.recovery_enabled = True
                print(
                    "[Recovery] LEGACY ROW UPGRADED "
                    f"email={email} recovery_key={recovery_key} hash_prefix={recovery_key_hash[:12]}"
                )
            recovery.failed_attempts = 0
            recovery.locked_until = None
            recovery.updated_at = now
            temp_token = _issue_temporary_reset_token(db, user.id)
            db.commit()
            print(
                "[Recovery] REQUEST SUCCESS token_created=True "
                f"email={email} expires_in_seconds={RECOVERY_TOKEN_TTL_MINUTES * 60}"
            )
            return {
                "success": True,
                "status": "ok",
                "verified": True,
                "reset_token": temp_token,
                "temporary_reset_token": temp_token,
                "expires_in": RECOVERY_TOKEN_TTL_MINUTES * 60,
                "expires_in_seconds": RECOVERY_TOKEN_TTL_MINUTES * 60,
                "expires_in_minutes": RECOVERY_TOKEN_TTL_MINUTES,
            }

        recovery.failed_attempts = int(recovery.failed_attempts or 0) + 1
        if recovery.failed_attempts >= RECOVERY_MAX_FAILED_ATTEMPTS:
            recovery.failed_attempts = RECOVERY_MAX_FAILED_ATTEMPTS
            recovery.locked_until = now + timedelta(minutes=RECOVERY_LOCK_MINUTES)
        recovery.updated_at = now
        db.commit()
        if recovery.locked_until and recovery.locked_until > now:
            print(
                "[Recovery] REQUEST FAILED reason=locked_after_failed_attempts "
                f"email={email} failed_attempts={recovery.failed_attempts}"
            )
            return JSONResponse(
                {
                    "success": False,
                    "status": "error",
                    "message": "Recovery temporarily locked. Try again later.",
                    "failed_attempts": recovery.failed_attempts,
                    "locked_until": recovery.locked_until.isoformat(),
                },
                status_code=429,
            )
        print(
            "[Recovery] REQUEST FAILED reason=incorrect_sequence "
            f"email={email} failed_attempts={recovery.failed_attempts}"
        )
        return JSONResponse(
            {
                "success": False,
                "status": "error",
                "message": "Incorrect recovery emojis",
                "failed_attempts": recovery.failed_attempts,
            },
            status_code=401,
        )
    except Exception as exc:
        db.rollback()
        print(f"[Recovery] verify error={exc}")
        print(traceback.format_exc())
        return JSONResponse(
            {
                "success": False,
                "status": "error",
                "message": "Unable to verify recovery emojis right now.",
            },
            status_code=500,
        )


@app.post("/auth/reset-password-with-emojis")
def reset_password_with_emojis(body: RecoveryEmojiResetBody, db: Session = Depends(get_db)):
    print("[Recovery] PASSWORD RESET START")
    try:
        _ensure_recovery_emoji_schema(db)
        token = _recovery_reset_token_from_body(body)
        new_password = (body.new_password or "").strip()
        print(f"[Recovery] RESET REQUEST START token_present={bool(token)} new_password_len={len(new_password)}")
        if not token or not new_password:
            return JSONResponse(
                {
                    "success": False,
                    "status": "error",
                    "message": "Temporary reset token and new password are required.",
                },
                status_code=400,
            )
        if len(new_password) < 6:
            return JSONResponse(
                {
                    "success": False,
                    "status": "error",
                    "message": "Password must be at least 6 characters.",
                },
                status_code=400,
            )

        row = _find_valid_reset_token(db, token)
        if not row:
            print("[Recovery] RESET REQUEST FAILED reason=invalid_or_expired_token")
            return JSONResponse(
                {"success": False, "status": "error", "message": "Expired token."},
                status_code=400,
            )

        user = db.query(User).filter(User.id == int(row["user_id"])).first()
        if not user:
            print("[Recovery] RESET REQUEST FAILED reason=user_missing_for_token")
            return JSONResponse(
                {"success": False, "status": "error", "message": "Expired token."},
                status_code=400,
            )

        new_hash = User.hash_password(new_password)
        db.execute(
            text(
                """
                UPDATE users
                SET password = :password,
                    password_hash = :password_hash,
                    updated_at = NOW()
                WHERE id = :uid
                """
            ),
            {"uid": user.id, "password": new_hash, "password_hash": new_hash},
        )
        _finalize_reset_token(db, int(row["id"]), user.id)
        db.execute(text("DELETE FROM sessions WHERE user_id = :uid"), {"uid": user.id})
        db.commit()
        print(f"[Recovery] PASSWORD RESET SUCCESS user_id={user.id}")

        fresh_user = db.query(User).filter(User.id == user.id).first() or user
        token = crud.create_session(db, fresh_user.id)
        resp = JSONResponse(_session_response_payload(db, fresh_user))
        resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
        return resp
    except Exception as exc:
        db.rollback()
        print(f"[Recovery] password reset error={exc}")
        print(traceback.format_exc())
        return JSONResponse(
            {
                "success": False,
                "status": "error",
                "message": "Unable to reset your password right now.",
            },
            status_code=500,
        )


@app.post("/session/refresh")
def refresh_session(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)
    token = crud.create_session(db, user.id)
    resp = JSONResponse(_session_response_payload(db, user))
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
    return resp


def _chat_language_from_body(body: ChatBody) -> tuple[str, str, str]:
    raw = (body.language_code or body.languageCode or "en").strip().lower()
    if raw not in {"en", "hi", "mr"}:
        raw = "en"
    names = {
        "en": ("English", "simple, natural English"),
        "hi": ("Hindi", "natural Hindi in Devanagari script"),
        "mr": ("Marathi", "natural Marathi in Devanagari script"),
    }
    name, style = names[raw]
    return raw, name, style


@app.post("/chat")
def chat_proxy(body: ChatBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)

    message = (body.message or "").strip()
    if not message:
        return JSONResponse({"status": "error", "message": "Message is required."}, status_code=400)

    safe_history = []
    for item in (body.history or [])[-16:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user")).strip().lower()
        if role not in {"system", "assistant", "user"}:
            role = "user"
        text_value = str(item.get("content", "")).strip()
        if not text_value:
            continue
        safe_history.append({"role": role, "content": text_value[:900]})

    language_code, language_name, language_style = _chat_language_from_body(body)
    prompt = (
        "You are Ahira, a warm and emotionally supportive companion. "
        f"You MUST respond ONLY in {language_name}. Use {language_style}. "
        "Do not mix languages unless the user explicitly asks you to translate or switch languages. "
        "Use short, clear sentences that an everyday user can understand. "
        "Avoid robotic tone, hard vocabulary, and long lectures. "
        "If the user is upset, acknowledge the feeling first, then give one or two practical next steps."
    )
    messages = [{"role": "system", "content": prompt}, *safe_history, {"role": "user", "content": message}]

    started_at = datetime.utcnow()
    print(
        f"[chat.proxy] OPENROUTER REQUEST START user_id={user.id} language={language_code} history={len(safe_history)} "
        f"messageChars={len(message)}"
    )
    last_error = None
    for attempt in range(2):
        run_started = datetime.utcnow()
        try:
            result = _openrouter_chat_completion(messages)
            elapsed_ms = int((datetime.utcnow() - run_started).total_seconds() * 1000)
            print(
                f"[chat.proxy] attempt={attempt + 1} model={result['model']} "
                f"responseTimeMs={elapsed_ms} status={result['status_code']}"
            )
            content = str(result["content"]).strip()
            total_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            print(f"[chat.proxy] final response delivered user_id={user.id} totalMs={total_ms}")
            return {
                "status": "ok",
                "reply": content,
                "used_fallback": False,
                "provider": "openrouter",
                "model": result["model"],
                "response_time_ms": result["elapsed_ms"],
            }
        except Exception as exc:
            last_error = exc
            elapsed_ms = int((datetime.utcnow() - run_started).total_seconds() * 1000)
            print(
                f"[chat.proxy] ERROR DETAILS attempt={attempt + 1} afterMs={elapsed_ms} "
                f"reason={exc} stack={traceback.format_exc()}"
            )
            if attempt == 0:
                continue

    total_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
    print(
        f"[chat.proxy] OPENROUTER FINAL FAILURE user_id={user.id} totalMs={total_ms} "
        f"reason={last_error}"
    )
    return JSONResponse(_chat_debug_payload(last_error, started_at), status_code=503)


# ─────────────────────────────────────────────────────────────
# REMINDERS — all strictly user-scoped
# ─────────────────────────────────────────────────────────────
@app.get("/reminders")
def list_reminders(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return {"tasks": []}
    rows = crud.get_reminders(db, user.id)
    return {
        "tasks": [
            {
                "id": r.id,
                "task": r.task,
                "date": r.date,
                "time": r.time,
                "priority": r.priority,
                "completed": r.completed,
            }
            for r in rows
        ]
    }


@app.post("/add_reminder")
def create_reminder(body: ReminderBody, request: Request, db: Session = Depends(get_db)):
    if not body.task or not body.task.strip():
        return JSONResponse({"status": "error", "message": "Task cannot be empty"}, status_code=400)
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in to save reminders."}, status_code=401)
    crud.add_reminder(db, user.id, body.task, body.date, body.time, body.priority)
    mongo.log_reminder(user.id, body.task, body.date, body.time, body.priority)
    return {"status": "success"}


@app.delete("/reminder/{reminder_id}")
def delete_task(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in."}, status_code=401)
    crud.delete_reminder(db, reminder_id, user.id)
    return {"status": "deleted"}


@app.post("/reminder/{reminder_id}/toggle")
def toggle_task(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in."}, status_code=401)
    crud.toggle_reminder(db, reminder_id, user.id)
    return {"status": "updated"}


@app.put("/reminder/{reminder_id}")
def update_task(reminder_id: int, body: ReminderUpdateBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in."}, status_code=401)
    task = (body.task or "").strip()
    if not task:
        return JSONResponse({"status": "error", "message": "Task cannot be empty"}, status_code=400)
    row = db.execute(
        text(
            """
            UPDATE reminders
            SET task = :task,
                date = :date,
                time = :time,
                priority = :priority,
                completed = COALESCE(:completed, completed)
            WHERE id = :rid AND user_id = :uid
            RETURNING id
            """
        ),
        {
            "task": task,
            "date": body.date,
            "time": body.time,
            "priority": body.priority or "normal",
            "completed": body.completed,
            "rid": reminder_id,
            "uid": user.id,
        },
    ).mappings().first()
    db.commit()
    if not row:
        return JSONResponse({"status": "error", "message": "Reminder not found."}, status_code=404)
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────
# FEEDS
# ─────────────────────────────────────────────────────────────
@app.get("/feeds")
def get_feeds(
    request: Request,
    db: Session = Depends(get_db),
    language: str = Query("en"),
    limit: int = Query(20),
    offset: int = Query(0),
    cursor: Optional[str] = Query(None),
    activeOnly: bool = Query(True),
    excludeExpired: bool = Query(True),
):
    lang = _safe_language(language)
    lim = _safe_limit(limit)
    user = current_user(request, db)
    current_user_id = user.id if user else None

    if cursor is not None and cursor.strip().isdigit():
        off = _safe_offset(int(cursor.strip()))
    else:
        off = _safe_offset(offset)

    # Primary centralized feed source: MongoDB (global cross-account posts).
    posts_col = mongo.get_collection("community_posts")
    if posts_col is not None:
        q = {"language": {"$in": [lang, "en"]}}
        if activeOnly:
            q["deleted"] = {"$ne": True}
        if excludeExpired:
            q["expires_at"] = {"$gt": datetime.utcnow()}

        fetch_window = min(max(lim + off + 10, 40), 300)
        rows = list(posts_col.find(q).sort("created_at", -1).limit(fetch_window))
        generated = _ensure_generated_posts(lang)
        merged = rows + generated
        merged.sort(key=lambda x: x.get("created_at") or datetime.utcnow(), reverse=True)
        deduped = []
        seen_keys = set()
        for row in merged:
            row_key = str(row.get("post_id") or row.get("_id") or "")
            if not row_key or row_key in seen_keys:
                continue
            seen_keys.add(row_key)
            deduped.append(row)
        merged = deduped[off : off + lim]
        post_ids = []
        for r in merged:
            rid = str(r.get("_id") or "")
            if rid:
                post_ids.append(rid)

        selected_by_post = {}
        reactions_col = mongo.get_collection("community_reactions")
        if current_user_id is not None and reactions_col is not None and post_ids:
            selected_rows = list(
                reactions_col.find(
                    {"post_id": {"$in": post_ids}, "user_id": current_user_id},
                    {"post_id": 1, "reaction": 1},
                )
            )
            for rr in selected_rows:
                rk = _mongo_reaction_key(rr.get("reaction"))
                if rk:
                    selected_by_post[str(rr.get("post_id"))] = rk

        items = []
        for r in merged:
            rid = str(r.get("_id") or uuid.uuid4().hex)
            items.append(
                {
                    "id": f"user_{rid}",
                    "type": "generated_post" if r.get("kind") == "generated" else "user_post",
                    "content": r.get("content", ""),
                    "image_url": None,
                    "source_name": None,
                    "source_url": None,
                    "language": r.get("language", "en"),
                    "category": r.get("category", "Daily Life ☕"),
                    "mood": r.get("mood", "emotional"),
                    "anonymous_identity": r.get("anonymous_identity", "☁️ Quiet Mind"),
                    "createdAt": (r.get("created_at") or datetime.utcnow()).isoformat(),
                    "expiresAt": (r.get("expires_at") or datetime.utcnow()).isoformat(),
                    "is_news_post": False,
                    "engagementScore": int(r.get("engagement_score") or 0),
                    "trendingScore": int(r.get("trending_score") or 0),
                    "reactions": r.get("reactions") or {"relate": 0, "hug": 0, "support": 0, "feltThis": 0},
                    "commentCount": int(r.get("comment_count") or 0),
                    "selected_reaction": selected_by_post.get(rid),
                }
            )
        if items:
            return {"items": items, "nextCursor": str(off + len(items)) if len(items) == lim else None}

    sql = text(
        """
    WITH user_posts AS (
      SELECT
        'user_' || id::text AS id,
        'user_post'::text AS type,
        content,
        NULL::text AS image_url,
        NULL::text AS source_name,
        NULL::text AS source_url,
        language,
        category,
        mood,
        anonymous_identity,
        created_at,
        expires_at,
        4 AS priority,
        CASE WHEN language = :lang THEN 0 WHEN language = 'en' THEN 1 ELSE 2 END AS language_rank,
        created_at AS secondary_order
      FROM feed_user_posts
      WHERE language IN (:lang, 'en')
        AND (:activeOnly = FALSE OR deleted = FALSE)
        AND (:excludeExpired = FALSE OR expires_at IS NULL OR expires_at > NOW())
    ),
    sponsored AS (
      SELECT
        'sponsored_' || id::text AS id,
        'sponsored_post'::text AS type,
        COALESCE(content, title) AS content,
        image_url,
        brand_name AS source_name,
        redirect_url AS source_url,
        target_language AS language,
        'Daily Life ☕'::text AS category,
        'calm'::text AS mood,
        '✨ Lost Dreamer'::text AS anonymous_identity,
        created_at,
        NULL::timestamptz AS expires_at,
        1 AS priority,
        CASE WHEN target_language = :lang THEN 0 WHEN target_language = 'en' THEN 1 ELSE 2 END AS language_rank,
        created_at AS secondary_order
      FROM sponsored_posts
      WHERE is_active = TRUE
        AND CURRENT_DATE BETWEEN start_date AND end_date
        AND target_language IN (:lang, 'en')
    ),
    ahira AS (
      SELECT
        'pick_' || id::text AS id,
        'ahira_pick'::text AS type,
        content,
        NULL::text AS image_url,
        'Ahira Picks'::text AS source_name,
        NULL::text AS source_url,
        language,
        'Soft Thoughts 🤍'::text AS category,
        'healing'::text AS mood,
        '🤍 Hidden Hug'::text AS anonymous_identity,
        created_at,
        NULL::timestamptz AS expires_at,
        5 AS priority,
        CASE WHEN language = :lang THEN 0 WHEN language = 'en' THEN 1 ELSE 2 END AS language_rank,
        created_at AS secondary_order
      FROM ahira_picks
      WHERE language IN (:lang, 'en')
    )
    SELECT
      id,
      type,
      content,
      image_url,
      source_name,
      source_url,
      language,
      category,
      mood,
      anonymous_identity,
      created_at AS "createdAt",
      expires_at AS "expiresAt",
      FALSE AS is_news_post
    FROM (
      SELECT * FROM sponsored
      UNION ALL
      SELECT * FROM user_posts
      UNION ALL
      SELECT * FROM ahira
    ) rows
    ORDER BY priority ASC, language_rank ASC, secondary_order DESC NULLS LAST, "createdAt" DESC
    LIMIT :lim OFFSET :off;
    """
    )

    rows = db.execute(
        sql,
        {
            "lang": lang,
            "lim": lim,
            "off": off,
            "activeOnly": activeOnly,
            "excludeExpired": excludeExpired,
        },
    ).mappings().all()

    data = [dict(r) for r in rows]
    if not data:
        data = _fallback_generated_posts(lang)

    return {"items": data, "nextCursor": str(off + len(data)) if len(data) == lim else None}


@app.post("/feeds")
def create_feed_post(body: FeedCreateBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    content = (body.content or "").strip()
    if not content:
        return JSONResponse({"status": "error", "message": "content is required"}, status_code=400)

    if len(content) > 4000:
        return JSONResponse({"status": "error", "message": "content is too long"}, status_code=400)

    lang = _safe_language(body.languageType or "en")
    category = (body.category or "Daily Life ☕")[:120]
    mood = (body.mood or "emotional")[:64]
    identity = (body.anonymousIdentity or "☁️ Quiet Mind")[:120]
    user_id = user.id if user else None
    client_post_id = (body.postId or "").strip()[:120]
    if not client_post_id:
        client_post_id = f"post_{uuid.uuid4().hex}"
    scoped_post_id = f"{user_id or 'guest'}:{client_post_id}"

    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=24)

    posts_col = mongo.get_collection("community_posts")
    inserted_id = None
    if posts_col is not None:
        existing = posts_col.find_one({"post_id": scoped_post_id})
        if existing:
            existing_id = str(existing.get("_id"))
            return {
                "status": "ok",
                "post": {
                    "id": f"user_{existing_id}",
                    "type": "user_post",
                    "content": existing.get("content", content),
                    "category": existing.get("category", category),
                    "mood": existing.get("mood", mood),
                    "anonymousIdentity": existing.get("anonymous_identity", identity),
                    "createdAt": (existing.get("created_at") or created_at).isoformat(),
                    "expiresAt": (existing.get("expires_at") or expires_at).isoformat(),
                    "is_user_post": True,
                    "is_news_post": False,
                    "commentCount": int(existing.get("comment_count") or 0),
                    "reactions": existing.get("reactions") or {"relate": 0, "hug": 0, "support": 0, "feltThis": 0},
                },
            }
        payload = {
            "post_id": scoped_post_id,
            "author_user_id": user_id,
            "author_name": _feed_actor_name(user),
            "language": lang,
            "content": content,
            "category": category,
            "mood": mood,
            "anonymous_identity": identity,
            "created_at": created_at,
            "expires_at": expires_at,
            "deleted": False,
            "comment_count": 0,
            "comments_count": 0,
            "reactions": {"relate": 0, "hug": 0, "support": 0, "feltThis": 0},
        }
        try:
            inserted = posts_col.insert_one(payload)
            inserted_id = str(inserted.inserted_id)
        except Exception:
            existing = posts_col.find_one({"post_id": scoped_post_id})
            if existing:
                inserted_id = str(existing.get("_id"))
                payload = existing
            else:
                raise
    else:
        existing = None
        if client_post_id:
            existing = db.execute(
                text(
                    """
                    SELECT id, content, category, mood, anonymous_identity, created_at, expires_at
                    FROM feed_user_posts
                    WHERE client_post_id = :client_post_id
                    LIMIT 1
                    """
                ),
                {"client_post_id": scoped_post_id},
            ).mappings().first()
        if existing:
            return {
                "status": "ok",
                "post": {
                    "id": f"user_{existing['id']}",
                    "type": "user_post",
                    "content": existing["content"],
                    "category": existing["category"],
                    "mood": existing["mood"],
                    "anonymousIdentity": existing["anonymous_identity"],
                    "createdAt": existing["created_at"].isoformat(),
                    "expiresAt": (existing["expires_at"] or expires_at).isoformat(),
                    "is_user_post": True,
                    "is_news_post": False,
                    "commentCount": 0,
                    "reactions": {"relate": 0, "hug": 0, "support": 0, "feltThis": 0},
                },
            }
        inserted = db.execute(
            text(
                """
                INSERT INTO feed_user_posts (user_id, language, content, category, mood, anonymous_identity, client_post_id)
                VALUES (:user_id, :language, :content, :category, :mood, :anonymous_identity, :client_post_id)
                RETURNING id
                """
            ),
            {
                "user_id": user_id,
                "language": lang,
                "content": content,
                "category": category,
                "mood": mood,
                "anonymous_identity": identity,
                "client_post_id": scoped_post_id,
            },
        ).mappings().first()
        db.commit()
        inserted_id = str(inserted["id"])

    return {
        "status": "ok",
        "post": {
            "id": f"user_{inserted_id}",
            "type": "user_post",
            "content": content,
            "category": category,
            "mood": mood,
            "anonymousIdentity": identity,
            "createdAt": created_at.isoformat(),
            "expiresAt": expires_at.isoformat(),
            "is_user_post": True,
            "is_news_post": False,
            "commentCount": 0,
            "reactions": {"relate": 0, "hug": 0, "support": 0, "feltThis": 0},
        },
    }


@app.get("/feeds/{post_id}/comments")
def get_feed_comments(post_id: str, db: Session = Depends(get_db)):
    key = _normalized_post_id(post_id)
    mongo_post_id = key.replace("user_", "", 1)
    comments_col = mongo.get_collection("community_comments")
    if comments_col is not None:
        rows = list(comments_col.find({"post_id": mongo_post_id}).sort("created_at", 1))
        items = [
            {
                "id": str(r["_id"]),
                "post_id": key,
                "content": r.get("content", ""),
                "anonymousIdentity": r.get("anonymous_identity", "☁️ Quiet Mind"),
                "createdAt": (r.get("created_at") or datetime.utcnow()).isoformat(),
                "deleted": bool(r.get("deleted", False)),
            }
            for r in rows
        ]
        return {"comments": items}

    rows = db.execute(
        text(
            """
            SELECT
              id,
              post_id,
              content,
              anonymous_identity,
              created_at,
              deleted
            FROM feed_comments
            WHERE post_id = :post_id
            ORDER BY created_at ASC
            """
        ),
        {"post_id": key},
    ).mappings().all()

    items = [
        {
            "id": str(r["id"]),
            "post_id": r["post_id"],
            "content": r["content"],
            "anonymousIdentity": r["anonymous_identity"],
            "createdAt": r["created_at"].isoformat(),
            "deleted": r["deleted"],
        }
        for r in rows
    ]
    return {"comments": items}


@app.post("/feeds/{post_id}/comments")
def create_feed_comment(post_id: str, body: FeedCommentCreateBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    key = _normalized_post_id(post_id)
    mongo_post_id = key.replace("user_", "", 1)
    content = (body.content or "").strip()
    if not content:
        return JSONResponse({"status": "error", "message": "content is required"}, status_code=400)

    created_at = datetime.utcnow()
    identity = (body.anonymousIdentity or "☁️ Quiet Mind")[:120]
    comments_col = mongo.get_collection("community_comments")
    inserted_id = None
    if comments_col is not None:
        inserted = comments_col.insert_one(
            {
                "post_id": mongo_post_id,
                "user_id": user.id if user else None,
                "author_name": _feed_actor_name(user),
                "content": content,
                "anonymous_identity": identity,
                "deleted": False,
                "created_at": created_at,
            }
        )
        inserted_id = str(inserted.inserted_id)
        _sync_post_counters_mongo(key)
        _log_social_activity(
            key,
            user.id if user else None,
            "Someone commented on your post 🌸",
            "Your post is getting attention.",
        )
    else:
        inserted = db.execute(
            text(
                """
                INSERT INTO feed_comments (post_id, user_id, content, anonymous_identity)
                VALUES (:post_id, :user_id, :content, :anonymous_identity)
                RETURNING id, created_at
                """
            ),
            {
                "post_id": key,
                "user_id": user.id if user else None,
                "content": content,
                "anonymous_identity": identity,
            },
        ).mappings().first()
        db.commit()
        inserted_id = str(inserted["id"])
        created_at = inserted["created_at"]

    return {
        "status": "ok",
        "comment": {
            "id": inserted_id,
            "post_id": key,
            "content": content,
            "anonymousIdentity": identity,
            "createdAt": created_at.isoformat(),
            "deleted": False,
        },
        "postSummary": _sync_post_counters_mongo(key) if comments_col is not None else None,
    }


@app.post("/feeds/{post_id}/reactions")
@app.post("/feeds/{post_id}/react")
def react_feed(post_id: str, body: FeedReactionBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)

    key = _normalized_post_id(post_id)
    mongo_post_id = key.replace("user_", "", 1)
    reaction = _mongo_reaction_key(body.reaction)
    allowed = {"relate", "hug", "support", "feltThis"}
    if reaction is not None and reaction not in allowed:
        return JSONResponse({"status": "error", "message": "invalid reaction"}, status_code=400)

    reactions_col = mongo.get_collection("community_reactions")
    if reactions_col is not None:
        if reaction is None:
            reactions_col.delete_one({"post_id": mongo_post_id, "user_id": user.id})
        else:
            reactions_col.update_one(
                {"post_id": mongo_post_id, "user_id": user.id},
                {
                    "$set": {
                        "reaction": reaction,
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()},
                },
                upsert=True,
            )
        summary = _sync_post_counters_mongo(key) or {"commentCount": 0, "reactions": {"relate": 0, "hug": 0, "support": 0, "feltThis": 0}}
        if reaction is not None:
            _log_social_activity(
                key,
                user.id,
                "Someone liked your post 🌸",
                "Your post is getting attention.",
            )
        return {"status": "ok", "reactions": summary["reactions"], "commentCount": summary["commentCount"], "selectedReaction": reaction}
    if reaction is None:
        db.execute(text("DELETE FROM feed_reactions WHERE post_id = :post_id AND user_id = :user_id"), {"post_id": key, "user_id": user.id})
    else:
        db.execute(text("INSERT INTO feed_reactions (post_id, user_id, reaction) VALUES (:post_id, :user_id, :reaction) ON CONFLICT (post_id, user_id) DO UPDATE SET reaction = EXCLUDED.reaction, updated_at = NOW()"), {"post_id": key, "user_id": user.id, "reaction": reaction})

    stats = db.execute(
        text(
            """
            SELECT
              COUNT(*) FILTER (WHERE reaction = 'relate') AS relate,
              COUNT(*) FILTER (WHERE reaction = 'hug') AS hug,
              COUNT(*) FILTER (WHERE reaction = 'support') AS support,
              COUNT(*) FILTER (WHERE reaction = 'feltthis') AS felt_this
            FROM feed_reactions
            WHERE post_id = :post_id
            """
        ),
        {"post_id": key},
    ).mappings().first()
    db.commit()

    return {
        "status": "ok",
        "reactions": {
            "relate": int(stats["relate"] or 0),
            "hug": int(stats["hug"] or 0),
            "support": int(stats["support"] or 0),
            "feltThis": int(stats["felt_this"] or 0),
        },
    }


@app.delete("/feeds/{post_id}")
def delete_feed_post(post_id: str, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    key = _normalized_post_id(post_id)
    post_oid = _mongo_oid(_mongo_post_id_from_any(key))
    posts_col = mongo.get_collection("community_posts")
    if posts_col is not None and post_oid is not None:
        row = posts_col.find_one({"_id": post_oid})
        if not row:
            return JSONResponse({"status": "error", "message": "Post not found"}, status_code=404)
        if int(row.get("author_user_id") or -1) != int(user.id):
            return JSONResponse({"status": "error", "message": "Not allowed"}, status_code=403)
        posts_col.update_one({"_id": post_oid}, {"$set": {"deleted": True, "updated_at": datetime.utcnow()}})
        return {"status": "ok"}
    deleted = db.execute(
        text("UPDATE feed_user_posts SET deleted = TRUE WHERE id::text = :pid AND user_id = :uid RETURNING id"),
        {"pid": key.replace("user_", "", 1), "uid": user.id},
    ).mappings().first()
    db.commit()
    if not deleted:
        return JSONResponse({"status": "error", "message": "Post not found"}, status_code=404)
    return {"status": "ok"}


@app.get("/feeds/summaries")
def feed_summaries(
    request: Request,
    db: Session = Depends(get_db),
    postIds: str = Query(""),
):
    user = current_user(request, db)
    user_id = user.id if user else None
    ids = [x.strip() for x in (postIds or "").split(",") if x.strip()]
    ids = ids[:80]
    if not ids:
        return {"items": []}
    out = []
    reactions_col = mongo.get_collection("community_reactions")
    for pid in ids:
        comments_count, counts = _post_counts_from_mongo(pid)
        selected = None
        if user_id is not None and reactions_col is not None:
            rr = reactions_col.find_one({"post_id": _mongo_post_id_from_any(pid), "user_id": user_id}, {"reaction": 1})
            selected = _mongo_reaction_key((rr or {}).get("reaction"))
        out.append(
            {
                "postId": _normalized_post_id(pid),
                "commentCount": comments_count,
                "reactions": counts,
                "selectedReaction": selected,
            }
        )
    return {"items": out}


@app.get("/comments")
def list_comments_alias(postId: Optional[str] = Query(None), post_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    pid = postId or post_id
    if not pid:
        return {"comments": []}
    return get_feed_comments(pid, db)


@app.post("/comments")
def create_comments_alias(body: dict, request: Request, db: Session = Depends(get_db)):
    pid = (body.get("postId") or body.get("post_id") or "").strip()
    content = (body.get("content") or "").strip()
    if not pid or not content:
        return JSONResponse({"status": "error", "message": "postId/post_id and content are required"}, status_code=400)
    return create_feed_comment(
        pid,
        FeedCommentCreateBody(
            content=content,
            anonymousIdentity=(body.get("anonymousIdentity") or "☁️ Quiet Mind"),
        ),
        request,
        db,
    )


@app.post("/feed/report")
def report_feed_post(body: FeedReportBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    reporter_user_id = str(user.id) if user else None

    post_id = (body.post_id or "").strip()
    post_type = (body.post_type or "").strip().lower()
    reason = (body.reason or "").strip()
    details = (body.details or "").strip() or None

    if not post_id or not post_type or not reason:
        return JSONResponse({"status": "error", "message": "post_id, post_type, reason are required"}, status_code=400)

    db.execute(
        text(
            """
            INSERT INTO feed_reports (post_id, post_type, reason, details, reporter_user_id)
            VALUES (:post_id, :post_type, :reason, :details, :reporter_user_id)
            """
        ),
        {
            "post_id": post_id,
            "post_type": post_type,
            "reason": reason,
            "details": details,
            "reporter_user_id": reporter_user_id,
        },
    )
    db.commit()
    return {"status": "ok"}


@app.post("/feeds/generated/refresh")
def refresh_generated_posts(language: str = Query("en")):
    lang = _safe_language(language)
    rows = _ensure_generated_posts(lang)
    return {"status": "ok", "language": lang, "count": len(rows)}


def run_feed_migrations(db: Session):
    migration_sql = """
    CREATE TABLE IF NOT EXISTS ahira_picks (
      id BIGSERIAL PRIMARY KEY,
      language VARCHAR(10) NOT NULL DEFAULT 'en',
      content TEXT NOT NULL,
      sub_type VARCHAR(64) NOT NULL,
      quality_score NUMERIC(5,2) NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_ahira_picks_created_at ON ahira_picks (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_ahira_picks_language_created ON ahira_picks (language, created_at DESC);

    CREATE TABLE IF NOT EXISTS sponsored_posts (
      id BIGSERIAL PRIMARY KEY,
      brand_name TEXT NOT NULL,
      title TEXT NOT NULL,
      content TEXT,
      image_url TEXT,
      redirect_url TEXT NOT NULL,
      start_date DATE NOT NULL,
      end_date DATE NOT NULL,
      target_language VARCHAR(10) NOT NULL DEFAULT 'en',
      is_active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CHECK (end_date >= start_date)
    );

    CREATE INDEX IF NOT EXISTS idx_sponsored_posts_active_window ON sponsored_posts (is_active, start_date, end_date);
    CREATE INDEX IF NOT EXISTS idx_sponsored_posts_target_language ON sponsored_posts (target_language);

    CREATE TABLE IF NOT EXISTS feed_reports (
      id BIGSERIAL PRIMARY KEY,
      post_id TEXT NOT NULL,
      post_type VARCHAR(32) NOT NULL,
      reason TEXT NOT NULL,
      details TEXT,
      reporter_user_id TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_feed_reports_created_at ON feed_reports (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_feed_reports_post_lookup ON feed_reports (post_id, post_type);

    CREATE TABLE IF NOT EXISTS feed_user_posts (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT,
      client_post_id VARCHAR(120),
      language VARCHAR(10) NOT NULL DEFAULT 'en',
      content TEXT NOT NULL,
      category VARCHAR(120) NOT NULL DEFAULT 'Daily Life ☕',
      mood VARCHAR(64) NOT NULL DEFAULT 'emotional',
      anonymous_identity VARCHAR(120) NOT NULL DEFAULT '☁️ Quiet Mind',
      deleted BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      expires_at TIMESTAMPTZ NULL DEFAULT NOW() + INTERVAL '24 hours'
    );

    CREATE INDEX IF NOT EXISTS idx_feed_user_posts_created_at ON feed_user_posts (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_feed_user_posts_language_created ON feed_user_posts (language, created_at DESC);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_feed_user_posts_client_post_id
      ON feed_user_posts (client_post_id) WHERE client_post_id IS NOT NULL;

    CREATE TABLE IF NOT EXISTS feed_comments (
      id BIGSERIAL PRIMARY KEY,
      post_id TEXT NOT NULL,
      user_id BIGINT,
      content TEXT NOT NULL,
      anonymous_identity VARCHAR(120) NOT NULL DEFAULT '☁️ Quiet Mind',
      deleted BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_feed_comments_post_created ON feed_comments (post_id, created_at ASC);

    CREATE TABLE IF NOT EXISTS feed_reactions (
      id BIGSERIAL PRIMARY KEY,
      post_id TEXT NOT NULL,
      user_id BIGINT NOT NULL,
      reaction VARCHAR(20) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(post_id, user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_feed_reactions_post ON feed_reactions (post_id);

    CREATE TABLE IF NOT EXISTS password_reset_tokens (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      token_hash TEXT NOT NULL,
      expires_at TIMESTAMPTZ NOT NULL,
      used BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_created
      ON password_reset_tokens (user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_lookup
      ON password_reset_tokens (user_id, token_hash, used, expires_at);

    CREATE TABLE IF NOT EXISTS user_recovery_emojis (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
      hashed_recovery_key TEXT,
      recovery_enabled BOOLEAN NOT NULL DEFAULT TRUE,
      emoji_sequence_hash TEXT NOT NULL,
      emoji_sequence_preview TEXT,
      emoji_hash TEXT,
      recovery_hint TEXT,
      failed_attempts INT NOT NULL DEFAULT 0,
      locked_until TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_user_recovery_emojis_user
      ON user_recovery_emojis (user_id, updated_at DESC);

    CREATE TABLE IF NOT EXISTS teams (
      id BIGSERIAL PRIMARY KEY,
      name VARCHAR(64) UNIQUE NOT NULL,
      logo_url TEXT,
      banner_url TEXT,
      total_points BIGINT NOT NULL DEFAULT 0,
      season_wins BIGINT NOT NULL DEFAULT 0,
      badges JSONB NOT NULL DEFAULT '[]'::jsonb,
      member_count BIGINT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS user_profiles (
      user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
      team_id BIGINT REFERENCES teams(id),
      selected_team_id VARCHAR(64),
      selected_team_name VARCHAR(64),
      team_change_count INT NOT NULL DEFAULT 0,
      team_selected_at TIMESTAMPTZ,
      xp BIGINT NOT NULL DEFAULT 0,
      streak_days INT NOT NULL DEFAULT 0,
      season_wins BIGINT NOT NULL DEFAULT 0,
      contribution_points BIGINT NOT NULL DEFAULT 0,
      badge_count BIGINT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    ALTER TABLE teams ADD COLUMN IF NOT EXISTS logo_url TEXT;
    ALTER TABLE teams ADD COLUMN IF NOT EXISTS banner_url TEXT;
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS selected_team_id VARCHAR(64);
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS selected_team_name VARCHAR(64);
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS team_selected_at TIMESTAMPTZ;

    CREATE TABLE IF NOT EXISTS game_score_submissions (
      id BIGSERIAL PRIMARY KEY,
      idempotency_key VARCHAR(128) NOT NULL,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      username VARCHAR(120) NOT NULL,
      team_id BIGINT REFERENCES teams(id),
      season_id VARCHAR(7) NOT NULL,
      game_id VARCHAR(64) NOT NULL,
      score BIGINT NOT NULL,
      xp_earned BIGINT NOT NULL DEFAULT 0,
      contribution_points BIGINT NOT NULL DEFAULT 0,
      anti_cheat_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      anti_cheat_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
      is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, idempotency_key)
    );
    CREATE INDEX IF NOT EXISTS idx_gss_season_game ON game_score_submissions (season_id, game_id, score DESC);
    CREATE INDEX IF NOT EXISTS idx_gss_user_created ON game_score_submissions (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS team_contribution_history (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      team_id BIGINT REFERENCES teams(id),
      season_id VARCHAR(7) NOT NULL,
      game_score_submission_id BIGINT REFERENCES game_score_submissions(id) ON DELETE SET NULL,
      points BIGINT NOT NULL,
      source VARCHAR(64) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_team_contrib_season_team ON team_contribution_history (season_id, team_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS season_stats (
      season_id VARCHAR(7) PRIMARY KEY,
      winner_team_id BIGINT REFERENCES teams(id),
      standings JSONB NOT NULL DEFAULT '[]'::jsonb,
      mvp_players JSONB NOT NULL DEFAULT '[]'::jsonb,
      badges_awarded JSONB NOT NULL DEFAULT '[]'::jsonb,
      finalized BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS user_badges (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      season_id VARCHAR(7),
      badge_code VARCHAR(64) NOT NULL,
      badge_label VARCHAR(120) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_user_badges_user_created ON user_badges (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS user_achievements (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      code VARCHAR(64) NOT NULL,
      label VARCHAR(120) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS sync_queue_receipts (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      idempotency_key VARCHAR(128) NOT NULL,
      action_type VARCHAR(64) NOT NULL,
      request_hash VARCHAR(128) NOT NULL,
      response_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, idempotency_key)
    );
    CREATE INDEX IF NOT EXISTS idx_sync_queue_user_created ON sync_queue_receipts (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS team_members (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
      active BOOLEAN NOT NULL DEFAULT TRUE,
      joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      left_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, team_id, joined_at)
    );
    CREATE INDEX IF NOT EXISTS idx_team_members_user_active ON team_members (user_id, active);

    CREATE TABLE IF NOT EXISTS leaderboard_cache (
      id BIGSERIAL PRIMARY KEY,
      scope VARCHAR(32) NOT NULL,
      season_id VARCHAR(7),
      game_id VARCHAR(64),
      payload JSONB NOT NULL DEFAULT '[]'::jsonb,
      generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(scope, season_id, game_id)
    );

    CREATE TABLE IF NOT EXISTS game_sessions (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id VARCHAR(64) NOT NULL,
      season_id VARCHAR(7) NOT NULL,
      team_id BIGINT REFERENCES teams(id),
      started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      ended_at TIMESTAMPTZ,
      duration_ms BIGINT NOT NULL DEFAULT 0,
      attempts INT NOT NULL DEFAULT 1,
      deaths INT NOT NULL DEFAULT 0,
      powerups INT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_game_sessions_user_created ON game_sessions (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS game_statistics (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id VARCHAR(64) NOT NULL,
      season_id VARCHAR(7) NOT NULL,
      total_score BIGINT NOT NULL DEFAULT 0,
      total_sessions BIGINT NOT NULL DEFAULT 0,
      total_duration_ms BIGINT NOT NULL DEFAULT 0,
      total_deaths BIGINT NOT NULL DEFAULT 0,
      total_powerups BIGINT NOT NULL DEFAULT 0,
      best_score BIGINT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, game_id, season_id)
    );

    CREATE TABLE IF NOT EXISTS achievements (
      id BIGSERIAL PRIMARY KEY,
      code VARCHAR(64) UNIQUE NOT NULL,
      label VARCHAR(120) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS achievement_progress (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      achievement_id BIGINT NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
      progress NUMERIC(10,2) NOT NULL DEFAULT 0,
      completed BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, achievement_id)
    );

    CREATE TABLE IF NOT EXISTS notifications_metadata (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      category VARCHAR(64) NOT NULL,
      state VARCHAR(32) NOT NULL DEFAULT 'scheduled',
      payload JSONB NOT NULL DEFAULT '{}'::jsonb,
      scheduled_for TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_notifications_meta_user ON notifications_metadata (user_id, updated_at DESC);

    CREATE TABLE IF NOT EXISTS user_settings (
      user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
      settings JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS app_preferences (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
      pref_key VARCHAR(120) NOT NULL,
      pref_value JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, pref_key)
    );

    CREATE TABLE IF NOT EXISTS streak_tracking (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      streak_type VARCHAR(64) NOT NULL,
      streak_days INT NOT NULL DEFAULT 0,
      last_active_date DATE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, streak_type)
    );

    CREATE TABLE IF NOT EXISTS contribution_history (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      team_id BIGINT REFERENCES teams(id),
      season_id VARCHAR(7) NOT NULL,
      points BIGINT NOT NULL DEFAULT 0,
      source VARCHAR(64) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS user_activity_summary (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      day_key DATE NOT NULL,
      metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, day_key)
    );

    CREATE TABLE IF NOT EXISTS diagnostics_logs (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      event_name VARCHAR(120) NOT NULL,
      payload JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS anti_cheat_flags (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      submission_id BIGINT REFERENCES game_score_submissions(id) ON DELETE SET NULL,
      flag VARCHAR(120) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS user_devices (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      device_id VARCHAR(200) NOT NULL,
      platform VARCHAR(32),
      app_version VARCHAR(64),
      last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, device_id)
    );

    CREATE TABLE IF NOT EXISTS user_presence (
      user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
      status VARCHAR(32) NOT NULL DEFAULT 'offline',
      last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS app_versions (
      id BIGSERIAL PRIMARY KEY,
      version VARCHAR(64) UNIQUE NOT NULL,
      min_supported BOOLEAN NOT NULL DEFAULT FALSE,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS content_flags (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      content_id VARCHAR(120) NOT NULL,
      content_type VARCHAR(64) NOT NULL,
      reason TEXT NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS moderation_logs (
      id BIGSERIAL PRIMARY KEY,
      moderator_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      target_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      action VARCHAR(64) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS water_tracking (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      amount_ml INT NOT NULL CHECK (amount_ml > 0),
      consumed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      day_key DATE NOT NULL,
      source VARCHAR(40) NOT NULL DEFAULT 'manual',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_water_tracking_user_day ON water_tracking (user_id, day_key, consumed_at DESC);

    CREATE TABLE IF NOT EXISTS habit_tracking (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      habit_code VARCHAR(120) NOT NULL,
      value INT NOT NULL DEFAULT 1,
      day_key DATE NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, habit_code, day_key)
    );
    CREATE INDEX IF NOT EXISTS idx_habit_tracking_user_day ON habit_tracking (user_id, day_key, updated_at DESC);

    CREATE TABLE IF NOT EXISTS medicine_tracking (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      medicine_name VARCHAR(200) NOT NULL,
      dosage VARCHAR(80),
      timing VARCHAR(80),
      timings JSONB NOT NULL DEFAULT '[]'::jsonb,
      taken BOOLEAN NOT NULL DEFAULT FALSE,
      day_key DATE NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, medicine_name, day_key)
    );
    CREATE INDEX IF NOT EXISTS idx_medicine_tracking_user_day ON medicine_tracking (user_id, day_key, updated_at DESC);

    CREATE TABLE IF NOT EXISTS daily_task_tracking (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      task_code VARCHAR(120) NOT NULL,
      title VARCHAR(240) NOT NULL,
      completed BOOLEAN NOT NULL DEFAULT FALSE,
      day_key DATE NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, task_code, day_key)
    );
    CREATE INDEX IF NOT EXISTS idx_daily_task_tracking_user_day ON daily_task_tracking (user_id, day_key, updated_at DESC);

    CREATE TABLE IF NOT EXISTS wellness_stats (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      day_key DATE NOT NULL,
      water_ml BIGINT NOT NULL DEFAULT 0,
      habits_done INT NOT NULL DEFAULT 0,
      medicines_taken INT NOT NULL DEFAULT 0,
      tasks_completed INT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, day_key)
    );
    CREATE INDEX IF NOT EXISTS idx_wellness_stats_user_day ON wellness_stats (user_id, day_key DESC);

    CREATE TABLE IF NOT EXISTS user_streaks (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      streak_type VARCHAR(64) NOT NULL,
      streak_days INT NOT NULL DEFAULT 0,
      last_active_date DATE,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, streak_type)
    );

    CREATE TABLE IF NOT EXISTS season_rewards (
      id BIGSERIAL PRIMARY KEY,
      season_id VARCHAR(7) NOT NULL,
      user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
      team_id BIGINT REFERENCES teams(id) ON DELETE SET NULL,
      reward_code VARCHAR(80) NOT NULL,
      reward_label VARCHAR(200) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_season_rewards_user_season ON season_rewards (user_id, season_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS analytics_events (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      event_name VARCHAR(120) NOT NULL,
      event_group VARCHAR(64) NOT NULL DEFAULT 'general',
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_analytics_events_user_created ON analytics_events (user_id, created_at DESC);

    ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
    UPDATE users SET password_hash = password WHERE password_hash IS NULL;
    ALTER TABLE sessions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days');
    ALTER TABLE feed_user_posts ADD COLUMN IF NOT EXISTS client_post_id VARCHAR(120);
    ALTER TABLE user_recovery_emojis ADD COLUMN IF NOT EXISTS hashed_recovery_key TEXT;
    ALTER TABLE user_recovery_emojis ADD COLUMN IF NOT EXISTS recovery_enabled BOOLEAN NOT NULL DEFAULT TRUE;
    ALTER TABLE user_recovery_emojis ADD COLUMN IF NOT EXISTS emoji_sequence_hash TEXT;
    ALTER TABLE user_recovery_emojis ADD COLUMN IF NOT EXISTS emoji_sequence_preview TEXT;
    ALTER TABLE user_recovery_emojis ADD COLUMN IF NOT EXISTS emoji_hash TEXT;
    UPDATE user_recovery_emojis
      SET emoji_sequence_hash = COALESCE(emoji_sequence_hash, emoji_hash)
      WHERE emoji_sequence_hash IS NULL;
    UPDATE user_recovery_emojis
      SET emoji_hash = COALESCE(emoji_hash, emoji_sequence_hash)
      WHERE emoji_hash IS NULL;
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) NOT NULL DEFAULT 'en';
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS total_xp BIGINT NOT NULL DEFAULT 0;
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS current_streak INT NOT NULL DEFAULT 0;
    UPDATE user_profiles SET total_xp = xp WHERE total_xp = 0 AND xp > 0;
    UPDATE user_profiles SET current_streak = streak_days WHERE current_streak = 0 AND streak_days > 0;

    CREATE TABLE IF NOT EXISTS seasons (
      id BIGSERIAL PRIMARY KEY,
      season_code VARCHAR(20) UNIQUE NOT NULL,
      start_date DATE NOT NULL,
      end_date DATE NOT NULL,
      is_active BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_seasons_active ON seasons (is_active, start_date, end_date);

    CREATE TABLE IF NOT EXISTS season_team_stats (
      id BIGSERIAL PRIMARY KEY,
      season_id BIGINT NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
      team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
      total_points BIGINT NOT NULL DEFAULT 0,
      wins BIGINT NOT NULL DEFAULT 0,
      rank INT,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(season_id, team_id)
    );
    CREATE INDEX IF NOT EXISTS idx_season_team_stats_rank ON season_team_stats (season_id, rank);

    CREATE TABLE IF NOT EXISTS user_game_progress (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      game_id VARCHAR(64) NOT NULL,
      current_level INT NOT NULL DEFAULT 1,
      high_score BIGINT NOT NULL DEFAULT 0,
      total_score BIGINT NOT NULL DEFAULT 0,
      last_played_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, game_id)
    );
    CREATE INDEX IF NOT EXISTS idx_user_game_progress_user ON user_game_progress (user_id, updated_at DESC);

    CREATE TABLE IF NOT EXISTS planner_tasks (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title TEXT NOT NULL,
      description TEXT,
      priority VARCHAR(32) NOT NULL DEFAULT 'normal',
      due_date DATE,
      due_time VARCHAR(16),
      completed BOOLEAN NOT NULL DEFAULT FALSE,
      completed_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_planner_tasks_user_created ON planner_tasks (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS user_habits (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      habit_name VARCHAR(200) NOT NULL,
      frequency VARCHAR(32) NOT NULL DEFAULT 'daily',
      target_count INT NOT NULL DEFAULT 1,
      current_streak INT NOT NULL DEFAULT 0,
      best_streak INT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_user_habits_user_created ON user_habits (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS habit_logs (
      id BIGSERIAL PRIMARY KEY,
      habit_id BIGINT NOT NULL REFERENCES user_habits(id) ON DELETE CASCADE,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_completed ON habit_logs (habit_id, completed_at DESC);

    CREATE TABLE IF NOT EXISTS wellness_logs (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      mood VARCHAR(64),
      sleep_hours NUMERIC(4,2),
      stress_level INT,
      energy_level INT,
      notes TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_wellness_logs_user_created ON wellness_logs (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS water_logs (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      amount_ml INT NOT NULL CHECK (amount_ml > 0),
      logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_water_logs_user_logged ON water_logs (user_id, logged_at DESC);

    CREATE TABLE IF NOT EXISTS medicines (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      medicine_name VARCHAR(200) NOT NULL,
      dosage VARCHAR(80),
      first_time VARCHAR(32),
      second_time VARCHAR(32),
      third_time VARCHAR(32),
      is_combined BOOLEAN NOT NULL DEFAULT FALSE,
      notes TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_medicines_user_created ON medicines (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS medicine_logs (
      id BIGSERIAL PRIMARY KEY,
      medicine_id BIGINT NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      taken_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      status VARCHAR(32) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_medicine_logs_med_taken ON medicine_logs (medicine_id, taken_at DESC);

    CREATE TABLE IF NOT EXISTS user_goals (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      goal_title VARCHAR(240) NOT NULL,
      goal_description TEXT,
      target_value BIGINT NOT NULL DEFAULT 0,
      current_progress BIGINT NOT NULL DEFAULT 0,
      completed BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_user_goals_user_created ON user_goals (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS grocery_lists (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      list_name VARCHAR(240) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_grocery_lists_user_created ON grocery_lists (user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS grocery_items (
      id BIGSERIAL PRIMARY KEY,
      list_id BIGINT NOT NULL REFERENCES grocery_lists(id) ON DELETE CASCADE,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      item_name VARCHAR(240) NOT NULL,
      quantity VARCHAR(64),
      completed BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_grocery_items_list_created ON grocery_items (list_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS scheduled_notifications (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      notification_type VARCHAR(64) NOT NULL,
      title VARCHAR(240) NOT NULL,
      body TEXT NOT NULL,
      scheduled_for TIMESTAMPTZ NOT NULL,
      status VARCHAR(32) NOT NULL DEFAULT 'scheduled',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_scheduled_notifications_user_sched ON scheduled_notifications (user_id, scheduled_for DESC);

    CREATE TABLE IF NOT EXISTS ai_generations (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      feature_type VARCHAR(80) NOT NULL,
      prompt TEXT NOT NULL,
      generated_text TEXT NOT NULL,
      language VARCHAR(10) NOT NULL DEFAULT 'en',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_ai_generations_user_created ON ai_generations (user_id, created_at DESC);

    INSERT INTO seasons (season_code, start_date, end_date, is_active)
    VALUES ('2026-01', DATE '2026-01-01', DATE '2026-01-31', TRUE)
    ON CONFLICT (season_code) DO NOTHING;
    """
    db.execute(text(migration_sql))
    for team_name in TEAM_NAMES:
        team_slug = _team_slug(team_name)
        db.execute(
            text(
                """
                INSERT INTO teams (name, logo_url, banner_url)
                VALUES (:name, :logo, :banner)
                ON CONFLICT (name)
                DO UPDATE SET
                  logo_url = COALESCE(teams.logo_url, EXCLUDED.logo_url),
                  banner_url = COALESCE(teams.banner_url, EXCLUDED.banner_url),
                  updated_at = NOW()
                """
            ),
            {
                "name": team_name,
                "logo": f"ahira://team/{team_slug}/logo",
                "banner": f"ahira://team/{team_slug}/banner",
            },
        )
    db.commit()


# ─────────────────────────────────────────────────────────────
# TEAM / SCORE / LEADERBOARD / SEASON / SYNC APIs
# ─────────────────────────────────────────────────────────────
@app.get("/teams")
def list_teams(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name, logo_url, banner_url, total_points, season_wins, member_count FROM teams ORDER BY name ASC")).mappings().all()
    teams = []
    for row in rows:
        slug = _team_slug(row["name"])
        teams.append({
            "id": slug,
            "teamId": slug,
            "numericId": row["id"],
            "name": row["name"],
            "teamName": row["name"],
            "logoUrl": row["logo_url"] or f"ahira://team/{slug}/logo",
            "logo_url": row["logo_url"] or f"ahira://team/{slug}/logo",
            "bannerUrl": row["banner_url"] or f"ahira://team/{slug}/banner",
            "banner_url": row["banner_url"] or f"ahira://team/{slug}/banner",
            "totalPoints": int(row["total_points"] or 0),
            "seasonWins": int(row["season_wins"] or 0),
            "memberCount": int(row["member_count"] or 0),
        })
    return {"teams": teams}


@app.get("/teams/membership")
def get_team_membership(request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    profile, selected_team = _profile_payload(db, user)
    if not profile or not selected_team:
        return {
            "membership": None,
            "profile": profile,
            "selected_team": None,
            "team_change_count": profile["teamChangeCount"] if profile else 0,
            "teamChangeCount": profile["teamChangeCount"] if profile else 0,
        }
    return {
        "membership": {
            "teamId": selected_team["teamId"],
            "teamName": selected_team["teamName"],
            "teamChangeCount": profile["teamChangeCount"],
            "joinedAtIso": profile["team_selected_at"] or profile["updated_at"] or datetime.utcnow().isoformat(),
            "changeHistory": [],
        },
        "profile": profile,
        "selected_team": selected_team,
    }


@app.post("/teams/membership")
def post_team_membership(body: dict, request: Request, db: Session = Depends(get_db)):
    team_id_raw = (body.get("teamId") or "").strip().lower()
    if not team_id_raw:
        return JSONResponse({"status": "error", "message": "teamId required"}, status_code=400)
    return select_team(TeamSelectBody(teamId=team_id_raw), request, db)


@app.post("/teams/select")
def select_team(body: TeamSelectBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    team_name = _team_name_from_payload(body.teamName, body.teamId)
    if not team_name:
        return JSONResponse({"status": "error", "message": "Invalid team name."}, status_code=400)
    team = db.execute(text("SELECT id, name FROM teams WHERE name = :name"), {"name": team_name}).mappings().first()
    if not team:
        return JSONResponse({"status": "error", "message": "Invalid team name."}, status_code=400)

    profile = db.execute(text("SELECT team_id, team_change_count FROM user_profiles WHERE user_id = :uid"), {"uid": user.id}).mappings().first()
    if profile and profile["team_id"] is not None and int(profile["team_id"]) == int(team["id"]):
        profile_payload, selected_team = _profile_payload(db, user)
        return {
            "status": "ok",
            "message": "Team unchanged",
            "teamName": team["name"],
            "teamId": _team_slug(team["name"]),
            "membership": {
                "teamId": _team_slug(team["name"]),
                "teamName": team["name"],
                "teamChangeCount": profile_payload["teamChangeCount"] if profile_payload else 0,
                "joinedAtIso": profile_payload["team_selected_at"] if profile_payload else datetime.utcnow().isoformat(),
                "changeHistory": [],
            },
            "profile": profile_payload,
            "selected_team": selected_team,
            "team_change_count": profile_payload["teamChangeCount"] if profile_payload else 0,
            "teamChangeCount": profile_payload["teamChangeCount"] if profile_payload else 0,
        }
    if profile and profile["team_id"] is not None and int(profile["team_change_count"] or 0) >= 3:
        return JSONResponse({"status": "error", "message": "Team change limit reached (3 lifetime)."}, status_code=400)

    db.execute(
        text(
            """
            INSERT INTO user_profiles (user_id, team_id, selected_team_id, selected_team_name, team_change_count, team_selected_at)
            VALUES (:uid, :tid, :selected_team_id, :selected_team_name, 0, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
              team_id = EXCLUDED.team_id,
              selected_team_id = EXCLUDED.selected_team_id,
              selected_team_name = EXCLUDED.selected_team_name,
              team_change_count = CASE WHEN user_profiles.team_id IS NULL THEN user_profiles.team_change_count ELSE user_profiles.team_change_count + 1 END,
              team_selected_at = COALESCE(user_profiles.team_selected_at, NOW()),
              updated_at = NOW()
            """
        ),
        {
            "uid": user.id,
            "tid": team["id"],
            "selected_team_id": team["name"].strip().lower().replace(" ", "_"),
            "selected_team_name": team["name"].strip(),
        },
    )
    db.execute(text("UPDATE teams SET member_count = (SELECT COUNT(*) FROM user_profiles WHERE team_id = teams.id), updated_at = NOW()"))
    db.execute(text("UPDATE team_members SET active = FALSE, left_at = NOW(), updated_at = NOW() WHERE user_id = :uid AND active = TRUE"), {"uid": user.id})
    db.execute(text("INSERT INTO team_members (user_id, team_id, active) VALUES (:uid, :tid, TRUE)"), {"uid": user.id, "tid": team["id"]})
    db.commit()
    profile, selected_team = _profile_payload(db, user)
    return {
        "status": "ok",
        "teamName": team["name"],
        "teamId": _team_slug(team["name"]),
        "membership": {
            "teamId": _team_slug(team["name"]),
            "teamName": team["name"],
            "teamChangeCount": profile["teamChangeCount"] if profile else 0,
            "joinedAtIso": profile["team_selected_at"] if profile else datetime.utcnow().isoformat(),
            "changeHistory": [],
        },
        "profile": profile,
        "selected_team": selected_team,
        "team_change_count": profile["teamChangeCount"] if profile else 0,
        "teamChangeCount": profile["teamChangeCount"] if profile else 0,
    }


@app.post("/teams/change")
def change_team(body: TeamChangeBody, request: Request, db: Session = Depends(get_db)):
    return select_team(TeamSelectBody(teamName=body.teamName, teamId=body.teamId), request, db)


@app.get("/teams/leaderboard")
def teams_leaderboard_alias(seasonId: Optional[str] = Query(None), limit: int = Query(20), db: Session = Depends(get_db)):
    return team_leaderboard(seasonId, limit, db)


@app.get("/teams/me")
def teams_me(request: Request, db: Session = Depends(get_db)):
    return get_team_membership(request, db)


@app.post("/scores/submit")
def submit_score(body: GameScoreBody, request: Request, db: Session = Depends(get_db)):
    user = None
    try:
        user, err = _require_user(request, db)
        if err:
            return err
        game_id = (body.gameId or "").strip().lower()
        if not game_id:
            return JSONResponse({"status": "error", "message": "gameId required"}, status_code=400)

        started_at = datetime.utcnow()
        sid = body.seasonId or _season_id()
        _ensure_season_row(db, sid)
        idempotency_key = (body.idempotencyKey or f"{game_id}_{uuid.uuid4().hex}")[:128]
        score = int(body.score or 0)
        contribution_points = int(body.contributionPoints or 0)
        if contribution_points <= 0 and score > 0:
            contribution_points = max(1, round(score * 0.7))
        xp_earned = int(body.xpEarned or 0)
        if xp_earned <= 0 and score > 0:
            xp_earned = max(1, round(score * 0.12))

        flags = _anti_cheat_flags(db, user.id, game_id, score, idempotency_key)
        resolved_team = _resolve_submission_team(db, user.id)
        if resolved_team is None:
            db.rollback()
            print(
                f"[scores.submit] rejected user_id={user.id} game_id={game_id} "
                f"reason=no_valid_team score={score}"
            )
            return JSONResponse(
                {"status": "error", "message": "Please select a team before submitting scores."},
                status_code=400,
            )
        team_id, team_name = resolved_team

        print(
            f"[scores.submit] begin user_id={user.id} game_id={game_id} score={score} "
            f"team_id={team_id} team_name={team_name} contribution_points={contribution_points} xp={xp_earned}"
        )

        team_points_before = db.execute(
            text("SELECT COALESCE(total_points, 0) AS total_points FROM teams WHERE id = :tid"),
            {"tid": team_id},
        ).mappings().first()
        team_points_before = int((team_points_before or {}).get("total_points") or 0)

        inserted = db.execute(
            text(
                """
                INSERT INTO game_score_submissions
                  (idempotency_key, user_id, username, team_id, season_id, game_id, score, xp_earned, contribution_points, anti_cheat_metadata, anti_cheat_flags, is_suspicious)
                VALUES
                  (:idempotency_key, :user_id, :username, :team_id, :season_id, :game_id, :score, :xp_earned, :contribution_points, CAST(:anti_cheat_metadata AS JSONB), CAST(:anti_cheat_flags AS JSONB), :is_suspicious)
                RETURNING id, created_at
                """
            ),
            {
                "idempotency_key": idempotency_key,
                "user_id": user.id,
                "username": user.name,
                "team_id": team_id,
                "season_id": sid,
                "game_id": game_id,
                "score": score,
                "xp_earned": xp_earned,
                "contribution_points": contribution_points,
                "anti_cheat_metadata": json.dumps(body.antiCheatMetadata or {}),
                "anti_cheat_flags": json.dumps(flags),
                "is_suspicious": len(flags) > 0,
            },
        ).mappings().first()

        db.execute(text("INSERT INTO user_profiles (user_id) VALUES (:uid) ON CONFLICT (user_id) DO NOTHING"), {"uid": user.id})
        db.execute(
            text(
                """
                UPDATE user_profiles
                SET xp = xp + :xp,
                    contribution_points = contribution_points + :cp,
                    team_id = COALESCE(team_id, :tid),
                    selected_team_id = COALESCE(selected_team_id, :selected_team_id),
                    selected_team_name = COALESCE(selected_team_name, :selected_team_name),
                    updated_at = NOW()
                WHERE user_id = :uid
                """
            ),
            {
                "uid": user.id,
                "xp": xp_earned,
                "cp": contribution_points,
                "tid": team_id,
                "selected_team_id": _team_slug(team_name),
                "selected_team_name": team_name,
            },
        )

        if contribution_points > 0:
            db.execute(
                text("UPDATE teams SET total_points = total_points + :cp, updated_at = NOW() WHERE id = :tid"),
                {"cp": contribution_points, "tid": team_id},
            )
            db.execute(
                text(
                    """
                    INSERT INTO team_contribution_history (user_id, team_id, season_id, game_score_submission_id, points, source)
                    VALUES (:uid, :tid, :sid, :gid, :points, 'game_score')
                    """
                ),
                {"uid": user.id, "tid": team_id, "sid": sid, "gid": inserted["id"], "points": contribution_points},
            )
            db.execute(
                text(
                    """
                    INSERT INTO contribution_history (user_id, team_id, season_id, points, source, metadata)
                    VALUES (:uid, :tid, :sid, :points, 'game_score', CAST(:meta AS JSONB))
                    """
                ),
                {
                    "uid": user.id,
                    "tid": team_id,
                    "sid": sid,
                    "points": contribution_points,
                    "meta": json.dumps({"game": game_id, "submissionId": inserted["id"]}),
                },
            )
            db.execute(
                text(
                    """
                    INSERT INTO season_team_stats (season_id, team_id, total_points, wins, rank, updated_at, created_at)
                    SELECT s.id, :tid, :cp, 0, NULL, NOW(), NOW()
                    FROM seasons s
                    WHERE s.season_code = :sid
                    ON CONFLICT (season_id, team_id)
                    DO UPDATE SET total_points = season_team_stats.total_points + EXCLUDED.total_points, updated_at = NOW()
                    """
                ),
                {"sid": sid, "tid": team_id, "cp": contribution_points},
            )

        db.execute(
            text(
                """
                INSERT INTO game_sessions (user_id, game_id, season_id, team_id, ended_at, duration_ms, attempts, deaths, powerups)
                VALUES (:uid, :gid, :sid, :tid, NOW(), :dur, :attempts, :deaths, :powerups)
                """
            ),
            {
                "uid": user.id,
                "gid": game_id,
                "sid": sid,
                "tid": team_id,
                "dur": int(body.durationMs or 0),
                "attempts": int(body.attempts or 1),
                "deaths": int(body.deaths or 0),
                "powerups": int(body.powerups or 0),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO game_statistics (user_id, game_id, season_id, total_score, total_sessions, total_duration_ms, total_deaths, total_powerups, best_score)
                VALUES (:uid, :gid, :sid, :score, 1, :dur, :deaths, :powerups, :score)
                ON CONFLICT (user_id, game_id, season_id)
                DO UPDATE SET
                  total_score = game_statistics.total_score + EXCLUDED.total_score,
                  total_sessions = game_statistics.total_sessions + 1,
                  total_duration_ms = game_statistics.total_duration_ms + EXCLUDED.total_duration_ms,
                  total_deaths = game_statistics.total_deaths + EXCLUDED.total_deaths,
                  total_powerups = game_statistics.total_powerups + EXCLUDED.total_powerups,
                  best_score = GREATEST(game_statistics.best_score, EXCLUDED.best_score),
                  updated_at = NOW()
                """
            ),
            {
                "uid": user.id,
                "gid": game_id,
                "sid": sid,
                "score": score,
                "dur": int(body.durationMs or 0),
                "deaths": int(body.deaths or 0),
                "powerups": int(body.powerups or 0),
            },
        )
        for flag in flags:
            db.execute(
                text(
                    """
                    INSERT INTO anti_cheat_flags (user_id, submission_id, flag, metadata)
                    VALUES (:uid, :sidb, :flag, CAST(:meta AS JSONB))
                    """
                ),
                {"uid": user.id, "sidb": inserted["id"], "flag": flag, "meta": json.dumps({"game": game_id})},
            )

        _refresh_season_team_stats(db, sid)
        leaderboard_payload = _refresh_team_leaderboard_cache(db, sid, 20)

        team_points_after = db.execute(
            text("SELECT COALESCE(total_points, 0) AS total_points FROM teams WHERE id = :tid"),
            {"tid": team_id},
        ).mappings().first()
        team_points_after = int((team_points_after or {}).get("total_points") or 0)

        db.commit()
        elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        print(
            f"[scores.submit] committed user_id={user.id} game_id={game_id} team_id={team_id} "
            f"score={score} points={contribution_points} before={team_points_before} after={team_points_after} "
            f"rows={len(leaderboard_payload)} elapsed_ms={elapsed_ms} submission_id={inserted['id']}"
        )

        return {
            "status": "ok",
            "submissionId": inserted["id"],
            "suspicious": len(flags) > 0,
            "antiCheatFlags": flags,
            "seasonId": sid,
            "teamId": team_id,
            "teamName": team_name,
            "teamTotalBefore": team_points_before,
            "teamTotalAfter": team_points_after,
            "leaderboard": leaderboard_payload,
        }
    except Exception as exc:
        db.rollback()
        print(f"[scores.submit] rollback user_id={getattr(user, 'id', 'unknown')} error={exc}")
        raise


@app.post("/game-scores")
def submit_score_compat(body: GameScoreBody, request: Request, db: Session = Depends(get_db)):
    return submit_score(body, request, db)


@app.get("/game-scores")
def list_game_scores(limit: int = Query(50), request: Request = None, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(
        text(
            """
            SELECT id, game_id, score, season_id, team_id, xp_earned, contribution_points, is_suspicious, created_at
            FROM game_score_submissions
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        {"uid": user.id, "lim": min(max(1, limit), 200)},
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.get("/leaderboard/personal")
def personal_leaderboard(
    request: Request,
    period: str = Query("all"),
    gameId: Optional[str] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    lim = _safe_limit(limit)
    if period == "weekly":
        where_time = "AND created_at > NOW() - INTERVAL '7 days'"
    elif period == "monthly":
        where_time = "AND season_id = :sid"
    else:
        where_time = ""
    game_clause = "AND game_id = :gid" if gameId else ""
    sql = f"""
      SELECT user_id, username, SUM(score) AS total_score, SUM(xp_earned) AS total_xp
      FROM game_score_submissions
      WHERE 1=1 {where_time} {game_clause}
      GROUP BY user_id, username
      ORDER BY total_score DESC, total_xp DESC
      LIMIT :lim
    """
    params = {"lim": lim, "sid": _season_id(), "gid": (gameId or "").strip().lower()}
    rows = db.execute(text(sql), params).mappings().all()
    items = []
    for index, row in enumerate(rows, start=1):
        items.append({
            "rank": index,
            "userId": row["user_id"],
            "username": row["username"],
            "totalScore": int(row["total_score"] or 0),
            "total_score": int(row["total_score"] or 0),
            "personalPoints": int(row["total_score"] or 0),
            "totalXp": int(row["total_xp"] or 0),
        })

    player = None
    user = current_user(request, db)
    if user:
        total_row = db.execute(
            text(
                f"""
                SELECT
                  COALESCE(SUM(score), 0) AS personal_points,
                  COALESCE(SUM(contribution_points), 0) AS contribution_points
                FROM game_score_submissions
                WHERE user_id = :uid {where_time} {game_clause}
                """
            ),
            {**params, "uid": user.id},
        ).mappings().first()
        rank_row = db.execute(
            text(
                f"""
                WITH totals AS (
                  SELECT user_id, COALESCE(SUM(score), 0) AS total_score
                  FROM game_score_submissions
                  WHERE 1=1 {where_time} {game_clause}
                  GROUP BY user_id
                ),
                ranked AS (
                  SELECT user_id, RANK() OVER (ORDER BY total_score DESC) AS rank
                  FROM totals
                )
                SELECT rank FROM ranked WHERE user_id = :uid
                """
            ),
            {**params, "uid": user.id},
        ).mappings().first()
        badge_rows = db.execute(
            text(
                """
                SELECT badge_id, unlocked_at
                FROM user_badges
                WHERE user_id = :uid
                ORDER BY unlocked_at DESC
                LIMIT 12
                """
            ),
            {"uid": user.id},
        ).mappings().all()
        player = {
            "playerRank": int(rank_row["rank"]) if rank_row and rank_row["rank"] is not None else None,
            "rank": int(rank_row["rank"]) if rank_row and rank_row["rank"] is not None else None,
            "personalPoints": int(total_row["personal_points"] or 0) if total_row else 0,
            "contributionPoints": int(total_row["contribution_points"] or 0) if total_row else 0,
            "badges": [dict(r) for r in badge_rows],
        }
    return {"items": items, "player": player}


@app.get("/leaderboard/team")
def team_leaderboard(seasonId: Optional[str] = Query(None), limit: int = Query(20), db: Session = Depends(get_db)):
    sid = seasonId or _season_id()
    _ensure_season_row(db, sid)
    lim = min(max(1, limit), 20)
    started_at = datetime.utcnow()
    _refresh_season_team_stats(db, sid)
    items, cache_hit = _get_team_leaderboard(db, sid, lim)
    db.commit()
    elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
    print(
        f"[leaderboard.team] season_id={sid} limit={lim} cache_hit={cache_hit} "
        f"rows={len(items)} elapsed_ms={elapsed_ms}"
    )
    return {"seasonId": sid, "items": items, "leaderboard": items, "cacheHit": cache_hit}


@app.get("/leaderboard/teams")
def team_leaderboard_plural(seasonId: Optional[str] = Query(None), limit: int = Query(20), db: Session = Depends(get_db)):
    return team_leaderboard(seasonId, limit, db)


@app.get("/seasons/{season_id}")
def season_stats(season_id: str, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM season_stats WHERE season_id = :sid"), {"sid": season_id}).mappings().first()
    if row:
        return {"status": "ok", "season": dict(row)}
    standings = db.execute(
        text(
            """
            SELECT t.id, t.name, COALESCE(SUM(h.points), 0) AS points
            FROM teams t
            LEFT JOIN contribution_history h ON h.team_id = t.id AND h.season_id = :sid
            GROUP BY t.id, t.name
            ORDER BY points DESC
            """
        ),
        {"sid": season_id},
    ).mappings().all()
    return {"status": "ok", "season": {"season_id": season_id, "standings": [dict(r) for r in standings], "finalized": False}}


@app.post("/sync/queue")
def sync_queue(body: SyncQueueBatchBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)
    results = []
    for item in body.items:
        action = (item.actionType or "").strip().lower()
        idem = (item.idempotencyKey or "").strip()
        raw = f"{action}|{item.payload}|{idem}"
        req_hash = hashlib.sha256(raw.encode()).hexdigest()
        existing = db.execute(
            text("SELECT response_payload FROM sync_queue_receipts WHERE user_id = :uid AND idempotency_key = :k"),
            {"uid": user.id, "k": idem},
        ).mappings().first()
        if existing:
            results.append({"idempotencyKey": idem, "status": "deduplicated", "response": existing["response_payload"]})
            continue
        resp_payload = {"accepted": True, "actionType": action}
        db.execute(
            text(
                """
                INSERT INTO sync_queue_receipts (user_id, idempotency_key, action_type, request_hash, response_payload)
                VALUES (:uid, :k, :a, :h, CAST(:r AS JSONB))
                """
            ),
            {"uid": user.id, "k": idem, "a": action, "h": req_hash, "r": str(resp_payload).replace("'", '"')},
        )
        results.append({"idempotencyKey": idem, "status": "accepted", "response": resp_payload})
    db.commit()
    return {"status": "ok", "results": results}


@app.post("/sync/batch")
def sync_batch(body: SyncQueueBatchBody, request: Request, db: Session = Depends(get_db)):
    return sync_queue(body, request, db)


@app.get("/sync/status")
def sync_status(request: Request, limit: int = Query(100), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(
        text(
            """
            SELECT idempotency_key, action_type, created_at, response_payload
            FROM sync_queue_receipts
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        {"uid": user.id, "lim": min(max(1, limit), 300)},
    ).mappings().all()
    return {"status": "ok", "items": [dict(r) for r in rows]}


@app.get("/teams/season")
def team_season_snapshot(seasonId: Optional[str] = Query(None), db: Session = Depends(get_db)):
    sid = seasonId or _season_id()
    data = team_leaderboard(sid, 20, db)
    return {"seasonId": sid, "leaderboard": data.get("items", [])}


@app.get("/teams/snapshot")
def team_snapshot_alias(seasonId: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return team_season_snapshot(seasonId, db)


@app.get("/activity")
def activity_feed(request: Request, limit: int = Query(20), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    lim = min(max(1, limit), 100)
    col = mongo.get_collection("activity_feed")
    if col is not None:
        rows = list(col.find({"$or": [{"user_id": user.id}, {"visibility": "global"}]}).sort("created_at", -1).limit(lim))
        if rows:
            return {
                "items": [
                    {
                        "title": r.get("title", "Activity"),
                        "subtitle": r.get("subtitle", ""),
                        "createdAt": (r.get("created_at") or datetime.utcnow()).isoformat(),
                    }
                    for r in rows
                ]
            }
    pg_rows = db.execute(
        text(
            """
            SELECT source AS title, CONCAT('Points: ', points) AS subtitle, created_at
            FROM contribution_history
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        {"uid": user.id, "lim": lim},
    ).mappings().all()
    return {"items": [{"title": r["title"], "subtitle": r["subtitle"], "createdAt": r["created_at"].isoformat()} for r in pg_rows]}


@app.get("/feeds/activity")
def activity_feed_alias(request: Request, limit: int = Query(20), db: Session = Depends(get_db)):
    return activity_feed(request, limit, db)


@app.post("/events")
def create_event(body: dict, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    title = str(body.get("title") or body.get("event") or "Activity").strip()[:160]
    subtitle = str(body.get("subtitle") or body.get("description") or "").strip()[:300]
    visibility = str(body.get("visibility") or "private").strip().lower()
    if visibility not in {"private", "global"}:
        visibility = "private"
    col = mongo.get_collection("activity_feed")
    created_at = datetime.utcnow()
    if col is not None:
        col.insert_one(
            {
                "user_id": user.id,
                "visibility": visibility,
                "title": title,
                "subtitle": subtitle,
                "kind": str(body.get("kind") or "event"),
                "created_at": created_at,
            }
        )
    db.execute(
        text(
            """
            INSERT INTO analytics_events (user_id, event_name, event_group, metadata, created_at)
            VALUES (:uid, :name, :grp, CAST(:meta AS JSONB), :created)
            """
        ),
        {"uid": user.id, "name": title or "event", "grp": "activity", "meta": json.dumps(body), "created": created_at},
    )
    db.commit()
    return {"status": "ok"}


@app.get("/users/me/stats")
def my_stats(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)
    row = db.execute(
        text(
            """
            SELECT u.user_id, u.xp, u.streak_days, u.contribution_points, u.season_wins, u.team_change_count, t.name AS team_name
            FROM user_profiles u
            LEFT JOIN teams t ON t.id = u.team_id
            WHERE u.user_id = :uid
            """
        ),
        {"uid": user.id},
    ).mappings().first()
    badges = db.execute(text("SELECT badge_code, badge_label, season_id, created_at FROM user_badges WHERE user_id = :uid ORDER BY created_at DESC LIMIT 100"), {"uid": user.id}).mappings().all()
    return {"status": "ok", "profile": dict(row) if row else None, "badges": [dict(r) for r in badges]}


@app.get("/users/me/contributions")
def my_contributions(request: Request, seasonId: Optional[str] = Query(None), limit: int = Query(100), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)
    sid = seasonId or _season_id()
    rows = db.execute(
        text(
            """
            SELECT id, team_id, season_id, game_score_submission_id, points, source, created_at
            FROM team_contribution_history
            WHERE user_id = :uid AND season_id = :sid
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        {"uid": user.id, "sid": sid, "lim": min(max(1, limit), 200)},
    ).mappings().all()
    return {"seasonId": sid, "items": [dict(r) for r in rows]}


def _refresh_wellness_stats(db: Session, user_id: int, day_key: str):
    water_total = db.execute(
        text("SELECT COALESCE(SUM(amount_ml), 0) AS total_ml FROM water_tracking WHERE user_id = :uid AND day_key = :dk"),
        {"uid": user_id, "dk": day_key},
    ).mappings().first()
    habits_done = db.execute(
        text("SELECT COUNT(*) AS c FROM habit_tracking WHERE user_id = :uid AND day_key = :dk AND value > 0"),
        {"uid": user_id, "dk": day_key},
    ).mappings().first()
    meds_taken = db.execute(
        text("SELECT COUNT(*) AS c FROM medicine_tracking WHERE user_id = :uid AND day_key = :dk AND taken = TRUE"),
        {"uid": user_id, "dk": day_key},
    ).mappings().first()
    tasks_done = db.execute(
        text("SELECT COUNT(*) AS c FROM daily_task_tracking WHERE user_id = :uid AND day_key = :dk AND completed = TRUE"),
        {"uid": user_id, "dk": day_key},
    ).mappings().first()
    db.execute(
        text(
            """
            INSERT INTO wellness_stats (user_id, day_key, water_ml, habits_done, medicines_taken, tasks_completed, updated_at)
            VALUES (:uid, :dk, :water, :habits, :meds, :tasks, NOW())
            ON CONFLICT (user_id, day_key)
            DO UPDATE SET
              water_ml = EXCLUDED.water_ml,
              habits_done = EXCLUDED.habits_done,
              medicines_taken = EXCLUDED.medicines_taken,
              tasks_completed = EXCLUDED.tasks_completed,
              updated_at = NOW()
            """
        ),
        {
            "uid": user_id,
            "dk": day_key,
            "water": int((water_total or {}).get("total_ml") or 0),
            "habits": int((habits_done or {}).get("c") or 0),
            "meds": int((meds_taken or {}).get("c") or 0),
            "tasks": int((tasks_done or {}).get("c") or 0),
        },
    )


@app.get("/wellness/water")
def list_water_tracking(request: Request, dayKey: Optional[str] = Query(None), limit: int = Query(100), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    dk = (dayKey or _day_key()).strip()
    rows = db.execute(
        text(
            """
            SELECT id, amount_ml, consumed_at, day_key, source, created_at
            FROM water_tracking
            WHERE user_id = :uid AND day_key = :dk
            ORDER BY consumed_at DESC
            LIMIT :lim
            """
        ),
        {"uid": user.id, "dk": dk, "lim": min(max(1, limit), 300)},
    ).mappings().all()
    return {"dayKey": dk, "items": [dict(r) for r in rows]}


@app.post("/wellness/water")
def create_water_tracking(body: WaterTrackBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    if int(body.amountMl or 0) <= 0 or int(body.amountMl) > 5000:
        return JSONResponse({"status": "error", "message": "invalid amountMl"}, status_code=400)
    consumed = _safe_iso_datetime(body.consumedAt, datetime.utcnow())
    dk = (body.dayKey or consumed.strftime("%Y-%m-%d")).strip()
    row = db.execute(
        text(
            """
            INSERT INTO water_tracking (user_id, amount_ml, consumed_at, day_key, source)
            VALUES (:uid, :amt, :consumed, :dk, :source)
            RETURNING id, amount_ml, consumed_at, day_key, source, created_at
            """
        ),
        {"uid": user.id, "amt": int(body.amountMl), "consumed": consumed, "dk": dk, "source": (body.source or "manual")[:40]},
    ).mappings().first()
    _refresh_wellness_stats(db, user.id, dk)
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/wellness/habits")
def list_habit_tracking(request: Request, dayKey: Optional[str] = Query(None), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    dk = (dayKey or _day_key()).strip()
    rows = db.execute(
        text(
            """
            SELECT id, habit_code, value, metadata, day_key, created_at, updated_at
            FROM habit_tracking
            WHERE user_id = :uid AND day_key = :dk
            ORDER BY updated_at DESC
            """
        ),
        {"uid": user.id, "dk": dk},
    ).mappings().all()
    return {"dayKey": dk, "items": [dict(r) for r in rows]}


@app.post("/wellness/habits")
def upsert_habit_tracking(body: HabitTrackBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    code = (body.habitCode or "").strip().lower()
    if not code:
        return JSONResponse({"status": "error", "message": "habitCode required"}, status_code=400)
    dk = (body.dayKey or _day_key()).strip()
    row = db.execute(
        text(
            """
            INSERT INTO habit_tracking (user_id, habit_code, value, day_key, metadata)
            VALUES (:uid, :code, :value, :dk, CAST(:meta AS JSONB))
            ON CONFLICT (user_id, habit_code, day_key)
            DO UPDATE SET value = EXCLUDED.value, metadata = EXCLUDED.metadata, updated_at = NOW()
            RETURNING id, habit_code, value, metadata, day_key, created_at, updated_at
            """
        ),
        {"uid": user.id, "code": code, "value": int(body.value or 0), "dk": dk, "meta": json.dumps(body.metadata or {})},
    ).mappings().first()
    _refresh_wellness_stats(db, user.id, dk)
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/wellness/medicines")
def list_medicine_tracking(request: Request, dayKey: Optional[str] = Query(None), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    dk = (dayKey or _day_key()).strip()
    rows = db.execute(
        text(
            """
            SELECT id, medicine_name, dosage, timing, timings, taken, metadata, day_key, created_at, updated_at
            FROM medicine_tracking
            WHERE user_id = :uid AND day_key = :dk
            ORDER BY updated_at DESC
            """
        ),
        {"uid": user.id, "dk": dk},
    ).mappings().all()
    return {"dayKey": dk, "items": [dict(r) for r in rows]}


@app.post("/wellness/medicines")
def upsert_medicine_tracking(body: MedicineTrackBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    name = (body.medicineName or "").strip()
    if not name:
        return JSONResponse({"status": "error", "message": "medicineName required"}, status_code=400)
    dk = (body.dayKey or _day_key()).strip()
    times = [x.strip() for x in (body.timings or []) if str(x).strip()]
    if not times and (body.timing or "").strip():
        times = [(body.timing or "").strip()]
    row = db.execute(
        text(
            """
            INSERT INTO medicine_tracking (user_id, medicine_name, dosage, timing, timings, taken, day_key, metadata)
            VALUES (:uid, :name, :dosage, :timing, CAST(:timings AS JSONB), :taken, :dk, CAST(:meta AS JSONB))
            ON CONFLICT (user_id, medicine_name, day_key)
            DO UPDATE SET
              dosage = EXCLUDED.dosage,
              timing = EXCLUDED.timing,
              timings = EXCLUDED.timings,
              taken = EXCLUDED.taken,
              metadata = EXCLUDED.metadata,
              updated_at = NOW()
            RETURNING id, medicine_name, dosage, timing, timings, taken, metadata, day_key, created_at, updated_at
            """
        ),
        {
            "uid": user.id,
            "name": name,
            "dosage": body.dosage,
            "timing": body.timing,
            "timings": json.dumps(times),
            "taken": bool(body.taken),
            "dk": dk,
            "meta": json.dumps(body.metadata or {}),
        },
    ).mappings().first()
    _refresh_wellness_stats(db, user.id, dk)
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/wellness/tasks")
def list_daily_tasks(request: Request, dayKey: Optional[str] = Query(None), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    dk = (dayKey or _day_key()).strip()
    rows = db.execute(
        text(
            """
            SELECT id, task_code, title, completed, metadata, day_key, created_at, updated_at
            FROM daily_task_tracking
            WHERE user_id = :uid AND day_key = :dk
            ORDER BY updated_at DESC
            """
        ),
        {"uid": user.id, "dk": dk},
    ).mappings().all()
    return {"dayKey": dk, "items": [dict(r) for r in rows]}


@app.post("/wellness/tasks")
def upsert_daily_task(body: DailyTaskTrackBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    code = (body.taskCode or "").strip().lower()
    title = (body.title or "").strip()
    if not code or not title:
        return JSONResponse({"status": "error", "message": "taskCode and title required"}, status_code=400)
    dk = (body.dayKey or _day_key()).strip()
    row = db.execute(
        text(
            """
            INSERT INTO daily_task_tracking (user_id, task_code, title, completed, day_key, metadata)
            VALUES (:uid, :code, :title, :completed, :dk, CAST(:meta AS JSONB))
            ON CONFLICT (user_id, task_code, day_key)
            DO UPDATE SET
              title = EXCLUDED.title,
              completed = EXCLUDED.completed,
              metadata = EXCLUDED.metadata,
              updated_at = NOW()
            RETURNING id, task_code, title, completed, metadata, day_key, created_at, updated_at
            """
        ),
        {"uid": user.id, "code": code, "title": title, "completed": bool(body.completed), "dk": dk, "meta": json.dumps(body.metadata or {})},
    ).mappings().first()
    _refresh_wellness_stats(db, user.id, dk)
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/wellness/stats")
def get_wellness_stats(request: Request, dayKey: Optional[str] = Query(None), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    dk = (dayKey or _day_key()).strip()
    _refresh_wellness_stats(db, user.id, dk)
    row = db.execute(
        text(
            """
            SELECT user_id, day_key, water_ml, habits_done, medicines_taken, tasks_completed, created_at, updated_at
            FROM wellness_stats
            WHERE user_id = :uid AND day_key = :dk
            """
        ),
        {"uid": user.id, "dk": dk},
    ).mappings().first()
    db.commit()
    return {"status": "ok", "stats": dict(row) if row else {"user_id": user.id, "day_key": dk, "water_ml": 0, "habits_done": 0, "medicines_taken": 0, "tasks_completed": 0}}


@app.get("/planner/tasks")
def list_planner_tasks(request: Request, limit: int = Query(100), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(
        text("SELECT * FROM planner_tasks WHERE user_id = :uid ORDER BY created_at DESC LIMIT :lim"),
        {"uid": user.id, "lim": min(max(1, limit), 500)},
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.post("/planner/tasks")
def create_planner_task(body: PlannerTaskBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    title = (body.title or "").strip()
    if not title:
        return JSONResponse({"status": "error", "message": "title required"}, status_code=400)
    completed_at = datetime.utcnow() if bool(body.completed) else None
    row = db.execute(
        text(
            """
            INSERT INTO planner_tasks (user_id, title, description, priority, due_date, due_time, completed, completed_at)
            VALUES (:uid, :title, :description, :priority, :due_date, :due_time, :completed, :completed_at)
            RETURNING *
            """
        ),
        {
            "uid": user.id,
            "title": title,
            "description": body.description,
            "priority": (body.priority or "normal")[:32],
            "due_date": body.dueDate,
            "due_time": body.dueTime,
            "completed": bool(body.completed),
            "completed_at": completed_at,
        },
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.post("/games/progress")
def upsert_game_progress(body: GameProgressBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    gid = (body.gameId or "").strip().lower()
    if not gid:
        return JSONResponse({"status": "error", "message": "gameId required"}, status_code=400)
    row = db.execute(
        text(
            """
            INSERT INTO user_game_progress (user_id, game_id, current_level, high_score, total_score, last_played_at)
            VALUES (:uid, :gid, :level, :high_score, :total_score, NOW())
            ON CONFLICT (user_id, game_id)
            DO UPDATE SET
              current_level = GREATEST(user_game_progress.current_level, EXCLUDED.current_level),
              high_score = GREATEST(user_game_progress.high_score, EXCLUDED.high_score),
              total_score = GREATEST(user_game_progress.total_score, EXCLUDED.total_score),
              last_played_at = NOW(),
              updated_at = NOW()
            RETURNING *
            """
        ),
        {
            "uid": user.id,
            "gid": gid,
            "level": int(body.currentLevel or 1),
            "high_score": int(body.highScore or 0),
            "total_score": int(body.totalScore or 0),
        },
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/games/progress")
def list_game_progress(request: Request, gameId: Optional[str] = Query(None), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    if gameId:
        row = db.execute(
            text("SELECT * FROM user_game_progress WHERE user_id = :uid AND game_id = :gid"),
            {"uid": user.id, "gid": gameId.strip().lower()},
        ).mappings().first()
        return {"item": dict(row) if row else None}
    rows = db.execute(
        text("SELECT * FROM user_game_progress WHERE user_id = :uid ORDER BY updated_at DESC"),
        {"uid": user.id},
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.get("/habits")
def list_user_habits(request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(text("SELECT * FROM user_habits WHERE user_id = :uid ORDER BY created_at DESC"), {"uid": user.id}).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.post("/habits")
def create_user_habit(body: UserHabitBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    name = (body.habitName or "").strip()
    if not name:
        return JSONResponse({"status": "error", "message": "habitName required"}, status_code=400)
    row = db.execute(
        text(
            """
            INSERT INTO user_habits (user_id, habit_name, frequency, target_count)
            VALUES (:uid, :name, :frequency, :target)
            RETURNING *
            """
        ),
        {"uid": user.id, "name": name, "frequency": (body.frequency or "daily")[:32], "target": max(1, int(body.targetCount or 1))},
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.post("/habits/{habit_id}/logs")
def create_habit_log(habit_id: int, body: HabitLogBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    habit = db.execute(text("SELECT id FROM user_habits WHERE id = :hid AND user_id = :uid"), {"hid": habit_id, "uid": user.id}).first()
    if not habit:
        return JSONResponse({"status": "error", "message": "Habit not found"}, status_code=404)
    completed_at = _safe_iso_datetime(body.completedAt, datetime.utcnow())
    row = db.execute(
        text("INSERT INTO habit_logs (habit_id, user_id, completed_at) VALUES (:hid, :uid, :completed_at) RETURNING *"),
        {"hid": habit_id, "uid": user.id, "completed_at": completed_at},
    ).mappings().first()
    db.execute(text("UPDATE user_habits SET current_streak = current_streak + 1, best_streak = GREATEST(best_streak, current_streak + 1), updated_at = NOW() WHERE id = :hid"), {"hid": habit_id})
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/wellness/logs")
def list_wellness_logs(request: Request, limit: int = Query(100), db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(text("SELECT * FROM wellness_logs WHERE user_id = :uid ORDER BY created_at DESC LIMIT :lim"), {"uid": user.id, "lim": min(max(1, limit), 500)}).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.post("/wellness/logs")
def create_wellness_log(body: WellnessLogBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    row = db.execute(
        text(
            """
            INSERT INTO wellness_logs (user_id, mood, sleep_hours, stress_level, energy_level, notes)
            VALUES (:uid, :mood, :sleep_hours, :stress_level, :energy_level, :notes)
            RETURNING *
            """
        ),
        {
            "uid": user.id,
            "mood": body.mood,
            "sleep_hours": body.sleepHours,
            "stress_level": body.stressLevel,
            "energy_level": body.energyLevel,
            "notes": body.notes,
        },
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/medicines")
def list_medicines(request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(text("SELECT * FROM medicines WHERE user_id = :uid ORDER BY created_at DESC"), {"uid": user.id}).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.post("/medicines")
def create_medicine(body: MedicineBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    name = (body.medicineName or "").strip()
    if not name:
        return JSONResponse({"status": "error", "message": "medicineName required"}, status_code=400)
    row = db.execute(
        text(
            """
            INSERT INTO medicines (user_id, medicine_name, dosage, first_time, second_time, third_time, is_combined, notes)
            VALUES (:uid, :name, :dosage, :first_time, :second_time, :third_time, :is_combined, :notes)
            RETURNING *
            """
        ),
        {
            "uid": user.id,
            "name": name,
            "dosage": body.dosage,
            "first_time": body.firstTime,
            "second_time": body.secondTime,
            "third_time": body.thirdTime,
            "is_combined": bool(body.isCombined),
            "notes": body.notes,
        },
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.post("/medicines/{medicine_id}/logs")
def create_medicine_log(medicine_id: int, body: MedicineLogBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    med = db.execute(text("SELECT id FROM medicines WHERE id = :mid AND user_id = :uid"), {"mid": medicine_id, "uid": user.id}).first()
    if not med:
        return JSONResponse({"status": "error", "message": "Medicine not found"}, status_code=404)
    status = (body.status or "").strip().lower()
    if status not in {"taken", "skipped", "snoozed"}:
        return JSONResponse({"status": "error", "message": "invalid status"}, status_code=400)
    taken_at = _safe_iso_datetime(body.takenAt, datetime.utcnow())
    row = db.execute(
        text("INSERT INTO medicine_logs (medicine_id, user_id, taken_at, status) VALUES (:mid, :uid, :taken_at, :status) RETURNING *"),
        {"mid": medicine_id, "uid": user.id, "taken_at": taken_at, "status": status},
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.put("/medicines/{medicine_id}")
def update_medicine(medicine_id: int, body: MedicineUpdateBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    exists = db.execute(text("SELECT id FROM medicines WHERE id = :mid AND user_id = :uid"), {"mid": medicine_id, "uid": user.id}).first()
    if not exists:
        return JSONResponse({"status": "error", "message": "Medicine not found"}, status_code=404)
    row = db.execute(
        text(
            """
            UPDATE medicines
            SET medicine_name = COALESCE(:name, medicine_name),
                dosage = COALESCE(:dosage, dosage),
                first_time = COALESCE(:first_time, first_time),
                second_time = COALESCE(:second_time, second_time),
                third_time = COALESCE(:third_time, third_time),
                is_combined = COALESCE(:is_combined, is_combined),
                notes = COALESCE(:notes, notes),
                updated_at = NOW()
            WHERE id = :mid AND user_id = :uid
            RETURNING *
            """
        ),
        {
            "name": body.medicineName,
            "dosage": body.dosage,
            "first_time": body.firstTime,
            "second_time": body.secondTime,
            "third_time": body.thirdTime,
            "is_combined": body.isCombined,
            "notes": body.notes,
            "mid": medicine_id,
            "uid": user.id,
        },
    ).mappings().first()
    if body.taken is not None:
        db.execute(
            text("INSERT INTO medicine_logs (medicine_id, user_id, taken_at, status) VALUES (:mid, :uid, NOW(), :status)"),
            {"mid": medicine_id, "uid": user.id, "status": "taken" if body.taken else "skipped"},
        )
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.delete("/medicines/{medicine_id}")
def delete_medicine_row(medicine_id: int, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    row = db.execute(text("DELETE FROM medicines WHERE id = :mid AND user_id = :uid RETURNING id"), {"mid": medicine_id, "uid": user.id}).mappings().first()
    db.commit()
    if not row:
        return JSONResponse({"status": "error", "message": "Medicine not found"}, status_code=404)
    return {"status": "ok"}


@app.get("/goals")
def list_goals(request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(text("SELECT * FROM user_goals WHERE user_id = :uid ORDER BY created_at DESC"), {"uid": user.id}).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.post("/goals")
def create_goal(body: GoalBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    title = (body.goalTitle or "").strip()
    if not title:
        return JSONResponse({"status": "error", "message": "goalTitle required"}, status_code=400)
    row = db.execute(
        text(
            """
            INSERT INTO user_goals (user_id, goal_title, goal_description, target_value, current_progress, completed)
            VALUES (:uid, :title, :description, :target_value, :current_progress, :completed)
            RETURNING *
            """
        ),
        {
            "uid": user.id,
            "title": title,
            "description": body.goalDescription,
            "target_value": int(body.targetValue or 0),
            "current_progress": int(body.currentProgress or 0),
            "completed": bool(body.completed),
        },
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/grocery/lists")
def list_grocery_lists(request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(text("SELECT * FROM grocery_lists WHERE user_id = :uid ORDER BY created_at DESC"), {"uid": user.id}).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.post("/grocery/lists")
def create_grocery_list(body: GroceryListBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    name = (body.listName or "").strip()
    if not name:
        return JSONResponse({"status": "error", "message": "listName required"}, status_code=400)
    row = db.execute(text("INSERT INTO grocery_lists (user_id, list_name) VALUES (:uid, :name) RETURNING *"), {"uid": user.id, "name": name}).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.get("/grocery/lists/{list_id}/items")
def list_grocery_items(list_id: int, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    rows = db.execute(text("SELECT * FROM grocery_items WHERE user_id = :uid AND list_id = :lid ORDER BY created_at DESC"), {"uid": user.id, "lid": list_id}).mappings().all()
    return {"items": [dict(r) for r in rows]}


@app.post("/grocery/lists/{list_id}/items")
def create_grocery_item(list_id: int, body: GroceryItemBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    parent = db.execute(text("SELECT id FROM grocery_lists WHERE id = :lid AND user_id = :uid"), {"lid": list_id, "uid": user.id}).first()
    if not parent:
        return JSONResponse({"status": "error", "message": "List not found"}, status_code=404)
    name = (body.itemName or "").strip()
    if not name:
        return JSONResponse({"status": "error", "message": "itemName required"}, status_code=400)
    row = db.execute(
        text(
            """
            INSERT INTO grocery_items (list_id, user_id, item_name, quantity, completed)
            VALUES (:lid, :uid, :name, :quantity, :completed)
            RETURNING *
            """
        ),
        {"lid": list_id, "uid": user.id, "name": name, "quantity": body.quantity, "completed": bool(body.completed)},
    ).mappings().first()
    db.commit()
    return {"status": "ok", "item": dict(row)}


@app.put("/grocery/items/{item_id}")
def update_grocery_item(item_id: int, body: GroceryItemUpdateBody, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    row = db.execute(
        text(
            """
            UPDATE grocery_items
            SET item_name = COALESCE(:name, item_name),
                quantity = COALESCE(:quantity, quantity),
                completed = COALESCE(:completed, completed),
                updated_at = NOW()
            WHERE id = :iid AND user_id = :uid
            RETURNING *
            """
        ),
        {"name": body.itemName, "quantity": body.quantity, "completed": body.completed, "iid": item_id, "uid": user.id},
    ).mappings().first()
    db.commit()
    if not row:
        return JSONResponse({"status": "error", "message": "Item not found"}, status_code=404)
    return {"status": "ok", "item": dict(row)}


@app.delete("/grocery/items/{item_id}")
def delete_grocery_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    user, err = _require_user(request, db)
    if err:
        return err
    row = db.execute(text("DELETE FROM grocery_items WHERE id = :iid AND user_id = :uid RETURNING id"), {"iid": item_id, "uid": user.id}).mappings().first()
    db.commit()
    if not row:
        return JSONResponse({"status": "error", "message": "Item not found"}, status_code=404)
    return {"status": "ok"}

# ─────────────────────────────────────────────────────────────
# DELETE MY DATA — wipes all user data from PostgreSQL
# ─────────────────────────────────────────────────────────────
@app.delete("/delete_my_data")
def delete_my_data(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in."}, status_code=401)

    _delete_user_owned_postgres(db, user.id, delete_user=False)
    db.commit()
    _delete_user_owned_mongo(user.id)

    resp = JSONResponse({"status": "ok", "message": "All data deleted."})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.delete("/delete_account")
def delete_account(body: DeleteAccountBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in."}, status_code=401)
    if not user.check_password(body.password):
        return JSONResponse({"status": "error", "message": "Password confirmation failed."}, status_code=403)

    user_id = user.id

    _delete_user_owned_postgres(db, user_id, delete_user=True)
    db.commit()
    _delete_user_owned_mongo(user_id)

    resp = JSONResponse({"status": "ok", "message": "Account permanently deleted."})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


# ─────────────────────────────────────────────────────────────
# STATUS ENDPOINTS
# ─────────────────────────────────────────────────────────────
@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "PostgreSQL connected ✅"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/db-status")
def db_status(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        pg = {
            "backend": "postgresql",
            "postgres_url_set": True,
            "psycopg2_available": True,
            "status": "connected",
            "user_count": db.query(User).count(),
            "reminder_count": db.query(ReminderModel).count(),
            "session_count": db.query(UserSession).count(),
        }
    except Exception as e:
        pg = {"backend": "postgresql", "status": "error", "error": str(e)}

    return {"postgresql": pg, "mongodb": mongo.get_status()}


@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = crud.list_users(db)
    return {"users": [{"id": u.id, "name": u.name, "email": u.email} for u in users]}


@app.get("/health")
def health():
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    return {
        "status": "ok",
        "services": {"postgresql": True, "mongodb": True},
        "openrouter": {
            "enabled": bool(openrouter_key),
            "model": OPENROUTER_DEFAULT_MODEL,
            "candidate_count": len(_openrouter_model_candidates()),
            **_openrouter_status_payload(),
        },
    }


@app.post("/openrouter/test")
def test_openrouter_connectivity(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)

    model_hint = OPENROUTER_DEFAULT_MODEL
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        print(f"[OpenRouter.test] API KEY MISSING user_id={user.id} model={model_hint}")
        return {
            "status": "ok",
            "enabled": False,
            "reachable": False,
            "model": model_hint,
            "candidate_count": len(_openrouter_model_candidates()),
            "models": _openrouter_model_candidates(),
            "openrouter": _openrouter_status_payload(),
            "key_loaded": False,
            "key_length": 0,
            "request_url": OPENROUTER_CHAT_URL,
            "message": "OPENROUTER_API_KEY is missing from the backend environment.",
        }

    print(f"[OpenRouter.test] OPENROUTER REQUEST START user_id={user.id} model={model_hint}")
    started_at = datetime.utcnow()
    try:
        test_messages = [
            {
                "role": "system",
                "content": "Reply with exactly one word: ok.",
            },
            {
                "role": "user",
                "content": "hello",
            },
        ]
        result = _openrouter_chat_completion(test_messages, timeout_seconds=12)
        elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        content = str(result["content"]).strip()
        reachable = bool(content)
        print(
            f"[OpenRouter.test] RESPONSE STATUS={result['status_code']} RESPONSE TIME={elapsed_ms}ms "
            f"MODEL USED={result['model']} reachable={reachable}"
        )
        return {
            "status": "ok",
            "enabled": True,
            "reachable": reachable,
            "model": result["model"],
            "candidate_count": len(_openrouter_model_candidates()),
            "models": _openrouter_model_candidates(),
            "current_model": result["model"],
            "last_successful_model": result["model"],
            "last_response_time_ms": result["elapsed_ms"],
            "last_provider_error": None,
            "failover_history": result.get("failover_history") or [],
            "openrouter": _openrouter_status_payload(),
            "key_loaded": True,
            "key_length": len(key),
            "request_url": OPENROUTER_CHAT_URL,
            "response_time_ms": elapsed_ms,
            "reply": content[:80],
            "raw_response": result["raw_response"],
            "message": "OpenRouter responded successfully." if reachable else "OpenRouter returned an empty response.",
        }
    except Exception as exc:
        elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        print(f"[OpenRouter.test] ERROR DETAILS user_id={user.id} elapsedMs={elapsed_ms} error={exc}")
        return {
            "status": "ok",
            "enabled": True,
            "reachable": False,
            "model": model_hint,
            "candidate_count": len(_openrouter_model_candidates()),
            "models": _openrouter_model_candidates(),
            "current_model": OPENROUTER_DEFAULT_MODEL,
            "last_successful_model": OPENROUTER_LAST_STATUS.get("last_successful_model"),
            "last_response_time_ms": OPENROUTER_LAST_STATUS.get("last_response_time_ms"),
            "last_provider_error": str(exc),
            "failover_history": OPENROUTER_LAST_STATUS.get("failover_history") or [],
            "openrouter": _openrouter_status_payload(),
            "key_loaded": True,
            "key_length": len(key),
            "request_url": OPENROUTER_CHAT_URL,
            "response_time_ms": elapsed_ms,
            "error": str(exc),
            "stack": traceback.format_exc()[:2000],
            "message": "OpenRouter connectivity test failed.",
        }
