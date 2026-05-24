"""
main.py — Ahira
PostgreSQL + MongoDB. All data is user-scoped.
Sessions expire after 30 days. Guests see empty data.
"""

import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional

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
from ai.models import User, UserSession
import ai.crud as crud
import ai.mongo as mongo

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SESSION_COOKIE = "ahira_session"
SESSION_MAX_DAYS = 30
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"


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
    }


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
            LEFT JOIN team_contribution_history h
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


def _fetch_news_for_language(lang: str):
    api_key = os.getenv("NEWS_API_KEY", "").strip()
    if not api_key:
        return []

    country = "in" if lang in {"hi", "mr"} else "us"
    try:
        r = requests.get(
            NEWS_API_URL,
            params={
                "apiKey": api_key,
                "country": country,
                "pageSize": 20,
            },
            timeout=12,
        )
        if r.status_code != 200:
            return []
        payload = r.json()
        articles = payload.get("articles") or []
        rows = []
        for idx, article in enumerate(articles):
            title = (article.get("title") or "").strip()
            desc = (article.get("description") or "").strip()
            content = (desc or title)[:1200]
            if not content:
                continue
            published_raw = article.get("publishedAt")
            published_at = None
            if published_raw:
                try:
                    published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                except Exception:
                    published_at = None

            rows.append(
                {
                    "id": f"news_ext_{idx}",
                    "type": "news_post",
                    "content": content,
                    "image_url": article.get("urlToImage"),
                    "source_name": (article.get("source") or {}).get("name") or "News",
                    "source_url": article.get("url"),
                    "language": lang,
                    "createdAt": (published_at or datetime.utcnow()).isoformat(),
                }
            )
        return rows
    except Exception:
        return []


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


def _refresh_generated_posts(lang: str):
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return _fallback_generated_posts(lang)
    prompt = (
        "Generate 6 short emotional community posts for Indian women users. "
        "Language mix based on lang input. Keep simple words, warm tone, under 100 chars. "
        "Return strict JSON array with fields content,category,mood,anonymous_identity."
    )
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ahira.app",
                "X-Title": "Ahira",
            },
            json={
                "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
                "messages": [{"role": "user", "content": f"{prompt} lang={lang}"}],
                "temperature": 0.8,
                "max_tokens": 420,
            },
            timeout=18,
        )
        if r.status_code < 200 or r.status_code >= 300:
            return _fallback_generated_posts(lang)
        content = (((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        start = content.find("[")
        end = content.rfind("]")
        if start < 0 or end <= start:
            return _fallback_generated_posts(lang)
        import json

        data = json.loads(content[start : end + 1])
        now = datetime.utcnow()
        out = []
        for idx, row in enumerate(data[:6]):
            out.append(
                {
                    "kind": "generated",
                    "language": lang,
                    "content": str(row.get("content", "")).strip(),
                    "category": str(row.get("category", "motivation")).strip().lower(),
                    "mood": str(row.get("mood", "calm")).strip().lower(),
                    "anonymous_identity": str(row.get("anonymous_identity", "☁️ Quiet Mind")).strip(),
                    "created_at": now - timedelta(minutes=idx * 13),
                    "expires_at": now + timedelta(hours=24),
                    "engagement_score": 30 + (idx * 8),
                    "trending_score": 18 + (idx * 6),
                    "reactions": {"relate": 7 + idx, "hug": 5 + idx, "support": 6 + idx, "feltThis": 8 + idx},
                    "comment_count": 1 + idx,
                }
            )
        return [x for x in out if x["content"]]
    except Exception:
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
        return rows
    fresh = _refresh_generated_posts(lang)
    if not fresh:
        return []
    docs = []
    for row in fresh:
        payload = dict(row)
        payload["day_key"] = day_key
        payload["created_at"] = payload.get("created_at") or now
        payload["expires_at"] = payload.get("expires_at") or (now + timedelta(hours=24))
        docs.append(payload)
    try:
        col.insert_many(docs)
    except Exception:
        pass
    return docs


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
    profile, selected_team = _profile_payload(db, user)
    resp = JSONResponse({
        "status": "ok",
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "profile": profile,
        "selected_team": selected_team,
        "selectedTeam": selected_team,
        "team_change_count": profile["team_change_count"] if profile else 0,
        "teamChangeCount": profile["teamChangeCount"] if profile else 0,
    })
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
    return resp


@app.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Incorrect email or password."}, status_code=401)

    token = crud.create_session(db, user.id)
    profile, selected_team = _profile_payload(db, user)
    resp = JSONResponse({
        "status": "ok",
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "profile": profile,
        "selected_team": selected_team,
        "selectedTeam": selected_team,
        "team_change_count": profile["team_change_count"] if profile else 0,
        "teamChangeCount": profile["teamChangeCount"] if profile else 0,
    })
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
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
    profile, selected_team = _profile_payload(db, user)
    return JSONResponse({
        "status": "ok",
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "profile": profile,
        "selected_team": selected_team,
        "selectedTeam": selected_team,
        "team_change_count": profile["team_change_count"] if profile else 0,
        "teamChangeCount": profile["teamChangeCount"] if profile else 0,
    })


@app.get("/users/me")
def users_me(request: Request, db: Session = Depends(get_db)):
    return me(request, db)


@app.post("/session/refresh")
def refresh_session(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)
    token = crud.create_session(db, user.id)
    resp = JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
    return resp


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

        rows = list(posts_col.find(q).sort("created_at", -1).skip(off).limit(lim))
        generated = _ensure_generated_posts(lang)
        merged = rows + generated
        merged.sort(key=lambda x: x.get("created_at") or datetime.utcnow(), reverse=True)
        merged = merged[off : off + lim]
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
        created_at AS secondary_order,
        FALSE AS is_news
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
        created_at AS secondary_order,
        TRUE AS is_news
      FROM sponsored_posts
      WHERE is_active = TRUE
        AND CURRENT_DATE BETWEEN start_date AND end_date
        AND target_language IN (:lang, 'en')
    ),
    important_news AS (
      SELECT
        'news_' || id::text AS id,
        'news_post'::text AS type,
        short_summary AS content,
        image_url,
        source_name,
        source_url,
        language,
        'Daily Life ☕'::text AS category,
        'calm'::text AS mood,
        '🌙 Midnight Girl'::text AS anonymous_identity,
        created_at,
        NULL::timestamptz AS expires_at,
        2 AS priority,
        CASE WHEN language = :lang THEN 0 WHEN language = 'en' THEN 1 ELSE 2 END AS language_rank,
        published_at AS secondary_order,
        TRUE AS is_news
      FROM news_posts
      WHERE language IN (:lang, 'en') AND is_important = TRUE
    ),
    regular_news AS (
      SELECT
        'news_' || id::text AS id,
        'news_post'::text AS type,
        short_summary AS content,
        image_url,
        source_name,
        source_url,
        language,
        'Daily Life ☕'::text AS category,
        'calm'::text AS mood,
        '🌙 Midnight Girl'::text AS anonymous_identity,
        created_at,
        NULL::timestamptz AS expires_at,
        3 AS priority,
        CASE WHEN language = :lang THEN 0 WHEN language = 'en' THEN 1 ELSE 2 END AS language_rank,
        COALESCE(published_at, created_at) AS secondary_order,
        TRUE AS is_news
      FROM news_posts
      WHERE language IN (:lang, 'en') AND COALESCE(is_important, FALSE) = FALSE
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
        created_at AS secondary_order,
        TRUE AS is_news
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
      is_news AS is_news_post
    FROM (
      SELECT * FROM sponsored
      UNION ALL
      SELECT * FROM important_news
      UNION ALL
      SELECT * FROM regular_news
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
        data = _fetch_news_for_language(lang)

    return {"items": data, "nextCursor": str(off + len(data)) if len(data) == lim else None}


@app.post("/feeds")
def create_feed_post(body: FeedCreateBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    content = (body.content or "").strip()
    if not content:
        return JSONResponse({"status": "error", "message": "content is required"}, status_code=400)

    if len(content) > 4000:
        return JSONResponse({"status": "error", "message": "content is too long"}, status_code=400)

    lang = "en"
    category = (body.category or "Daily Life ☕")[:120]
    mood = (body.mood or "emotional")[:64]
    identity = (body.anonymousIdentity or "☁️ Quiet Mind")[:120]
    user_id = user.id if user else None

    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=24)

    posts_col = mongo.get_collection("community_posts")
    inserted_id = None
    if posts_col is not None:
        post_uuid = uuid.uuid4().hex
        payload = {
            "post_id": post_uuid,
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
        inserted = posts_col.insert_one(payload)
        inserted_id = str(inserted.inserted_id)
    else:
        inserted = db.execute(
            text(
                """
                INSERT INTO feed_user_posts (user_id, language, content, category, mood, anonymous_identity)
                VALUES (:user_id, :language, :content, :category, :mood, :anonymous_identity)
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
    DO $$
    BEGIN
      IF to_regclass('public.news_posts') IS NOT NULL THEN
        ALTER TABLE news_posts
          ALTER COLUMN language TYPE VARCHAR(10);
        ALTER TABLE news_posts
          ADD COLUMN IF NOT EXISTS is_important BOOLEAN NOT NULL DEFAULT FALSE;
        CREATE INDEX IF NOT EXISTS idx_news_posts_created_at ON news_posts (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_news_posts_language_created ON news_posts (language, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_news_posts_type_language_created ON news_posts (language, is_important, created_at DESC);
      END IF;
    END $$;

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
    user, err = _require_user(request, db)
    if err:
        return err
    game_id = (body.gameId or "").strip().lower()
    if not game_id:
        return JSONResponse({"status": "error", "message": "gameId required"}, status_code=400)

    sid = body.seasonId or _season_id()
    idempotency_key = (body.idempotencyKey or f"{game_id}_{uuid.uuid4().hex}")[:128]
    flags = _anti_cheat_flags(db, user.id, game_id, int(body.score), idempotency_key)
    team_row = db.execute(text("SELECT team_id FROM user_profiles WHERE user_id = :uid"), {"uid": user.id}).mappings().first()
    team_id = team_row["team_id"] if team_row else None

    try:
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
                "score": int(body.score),
                "xp_earned": int(body.xpEarned or 0),
                "contribution_points": int(body.contributionPoints or 0),
                "anti_cheat_metadata": str((body.antiCheatMetadata or {})).replace("'", '"'),
                "anti_cheat_flags": str(flags).replace("'", '"'),
                "is_suspicious": len(flags) > 0,
            },
        ).mappings().first()
    except Exception:
        db.rollback()
        existing = db.execute(
            text("SELECT id, created_at FROM game_score_submissions WHERE user_id = :uid AND idempotency_key = :k"),
            {"uid": user.id, "k": idempotency_key},
        ).mappings().first()
        if existing:
            return {"status": "ok", "deduplicated": True, "submissionId": existing["id"], "createdAt": existing["created_at"].isoformat()}
        raise

    db.execute(text("INSERT INTO user_profiles (user_id) VALUES (:uid) ON CONFLICT (user_id) DO NOTHING"), {"uid": user.id})
    db.execute(
        text(
            """
            UPDATE user_profiles
            SET xp = xp + :xp,
                contribution_points = contribution_points + :cp,
                updated_at = NOW()
            WHERE user_id = :uid
            """
        ),
        {"uid": user.id, "xp": int(body.xpEarned or 0), "cp": int(body.contributionPoints or 0)},
    )
    if team_id is not None and int(body.contributionPoints or 0) > 0:
        db.execute(text("UPDATE teams SET total_points = total_points + :cp, updated_at = NOW() WHERE id = :tid"), {"cp": int(body.contributionPoints or 0), "tid": team_id})
        db.execute(
            text(
                """
                INSERT INTO team_contribution_history (user_id, team_id, season_id, game_score_submission_id, points, source)
                VALUES (:uid, :tid, :sid, :gid, :points, 'game_score')
                """
            ),
            {"uid": user.id, "tid": team_id, "sid": sid, "gid": inserted["id"], "points": int(body.contributionPoints or 0)},
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
                "points": int(body.contributionPoints or 0),
                "meta": '{"game":"%s"}' % game_id,
            },
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
            "score": int(body.score),
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
            {"uid": user.id, "sidb": inserted["id"], "flag": flag, "meta": '{"game":"%s"}' % game_id},
        )
    _refresh_season_team_stats(db, sid)
    db.commit()

    return {"status": "ok", "submissionId": inserted["id"], "suspicious": len(flags) > 0, "antiCheatFlags": flags}


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
    lim = min(max(1, limit), 20)
    _refresh_season_team_stats(db, sid)
    rows = db.execute(
        text(
            """
            SELECT
              t.id,
              t.name,
              t.logo_url,
              t.banner_url,
              t.season_wins,
              COALESCE(st.total_points, 0) AS season_points,
              COALESCE(st.rank, 0) AS cached_rank
            FROM teams t
            LEFT JOIN seasons s ON s.season_code = :sid
            LEFT JOIN season_team_stats st
              ON st.team_id = t.id AND st.season_id = s.id
            ORDER BY season_points DESC, t.name ASC
            LIMIT :lim
            """
        ),
        {"sid": sid, "lim": lim},
    ).mappings().all()
    items = []
    for index, row in enumerate(rows, start=1):
        slug = _team_slug(row["name"])
        contributors = db.execute(
            text(
                """
                SELECT user_id, username, COALESCE(SUM(contribution_points), 0) AS points
                FROM game_score_submissions
                WHERE season_id = :sid AND team_id = :tid
                GROUP BY user_id, username
                ORDER BY points DESC, username ASC
                LIMIT 3
                """
            ),
            {"sid": sid, "tid": row["id"]},
        ).mappings().all()
        points = int(row["season_points"] or 0)
        item = {
            "rank": index,
            "id": slug,
            "teamId": slug,
            "team_id": slug,
            "numericId": row["id"],
            "name": row["name"],
            "teamName": row["name"],
            "points": points,
            "totalPoints": points,
            "seasonPoints": points,
            "season_points": points,
            "wins": int(row["season_wins"] or 0),
            "seasonWins": int(row["season_wins"] or 0),
            "logoUrl": row["logo_url"] or f"ahira://team/{slug}/logo",
            "logo_url": row["logo_url"] or f"ahira://team/{slug}/logo",
            "bannerUrl": row["banner_url"] or f"ahira://team/{slug}/banner",
            "banner_url": row["banner_url"] or f"ahira://team/{slug}/banner",
            "topContributors": [
                {
                    "userId": r["user_id"],
                    "username": r["username"],
                    "points": int(r["points"] or 0),
                }
                for r in contributors
            ],
        }
        items.append(item)
    db.execute(
        text(
            """
            INSERT INTO leaderboard_cache (scope, season_id, game_id, payload, generated_at)
            VALUES ('team', :sid, NULL, CAST(:payload AS JSONB), NOW())
            ON CONFLICT (scope, season_id, game_id)
            DO UPDATE SET payload = EXCLUDED.payload, generated_at = NOW(), updated_at = NOW()
            """
        ),
        {"sid": sid, "payload": json.dumps(items)},
    )
    db.commit()
    return {"seasonId": sid, "items": items, "leaderboard": items}


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
            LEFT JOIN team_contribution_history h ON h.team_id = t.id AND h.season_id = :sid
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
    return {"status": "ok", "services": {"postgresql": True, "mongodb": True}}
