"""
main.py — Ahira
PostgreSQL + MongoDB. All data is user-scoped.
Sessions expire after 30 days. Guests see empty data.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

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

    token = crud.create_session(db, user.id)
    resp = JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=SESSION_MAX_DAYS * 24 * 3600)
    return resp


@app.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Incorrect email or password."}, status_code=401)

    token = crud.create_session(db, user.id)
    resp = JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})
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
    return JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})


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

    if cursor is not None and cursor.strip().isdigit():
        off = _safe_offset(int(cursor.strip()))
    else:
        off = _safe_offset(offset)

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

    inserted = db.execute(
        text(
            """
            INSERT INTO feed_user_posts (user_id, language, content, category, mood, anonymous_identity)
            VALUES (:user_id, :language, :content, :category, :mood, :anonymous_identity)
            RETURNING id, created_at, expires_at
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

    return {
        "status": "ok",
        "post": {
            "id": f"user_{inserted['id']}",
            "type": "user_post",
            "content": content,
            "category": category,
            "mood": mood,
            "anonymousIdentity": identity,
            "createdAt": inserted["created_at"].isoformat(),
            "expiresAt": inserted["expires_at"].isoformat() if inserted["expires_at"] else None,
            "is_user_post": True,
            "is_news_post": False,
            "commentCount": 0,
            "reactions": {"relate": 0, "hug": 0, "support": 0, "feltThis": 0},
        },
    }


@app.get("/feeds/{post_id}/comments")
def get_feed_comments(post_id: str, db: Session = Depends(get_db)):
    key = _normalized_post_id(post_id)
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
    content = (body.content or "").strip()
    if not content:
        return JSONResponse({"status": "error", "message": "content is required"}, status_code=400)

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
            "anonymous_identity": (body.anonymousIdentity or "☁️ Quiet Mind")[:120],
        },
    ).mappings().first()
    db.commit()

    return {
        "status": "ok",
        "comment": {
            "id": str(inserted["id"]),
            "post_id": key,
            "content": content,
            "anonymousIdentity": (body.anonymousIdentity or "☁️ Quiet Mind")[:120],
            "createdAt": inserted["created_at"].isoformat(),
            "deleted": False,
        },
    }


@app.post("/feeds/{post_id}/reactions")
@app.post("/feeds/{post_id}/react")
def react_feed(post_id: str, body: FeedReactionBody, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Please log in."}, status_code=401)

    key = _normalized_post_id(post_id)
    reaction = (body.reaction or "").strip().lower() or None
    allowed = {"relate", "hug", "support", "feltThis".lower()}
    if reaction is not None and reaction not in allowed:
        return JSONResponse({"status": "error", "message": "invalid reaction"}, status_code=400)

    if reaction is None:
        db.execute(
            text("DELETE FROM feed_reactions WHERE post_id = :post_id AND user_id = :user_id"),
            {"post_id": key, "user_id": user.id},
        )
    else:
        db.execute(
            text(
                """
                INSERT INTO feed_reactions (post_id, user_id, reaction)
                VALUES (:post_id, :user_id, :reaction)
                ON CONFLICT (post_id, user_id)
                DO UPDATE SET reaction = EXCLUDED.reaction, updated_at = NOW()
                """
            ),
            {"post_id": key, "user_id": user.id, "reaction": reaction},
        )

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


def run_feed_migrations(db: Session):
    migration_sql = """
    ALTER TABLE news_posts
      ALTER COLUMN language TYPE VARCHAR(10);

    ALTER TABLE news_posts
      ADD COLUMN IF NOT EXISTS is_important BOOLEAN NOT NULL DEFAULT FALSE;

    CREATE INDEX IF NOT EXISTS idx_news_posts_created_at ON news_posts (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_news_posts_language_created ON news_posts (language, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_news_posts_type_language_created ON news_posts (language, is_important, created_at DESC);

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
    """
    db.execute(text(migration_sql))
    db.commit()


# ─────────────────────────────────────────────────────────────
# DELETE MY DATA — wipes all user data from PostgreSQL
# ─────────────────────────────────────────────────────────────
@app.delete("/delete_my_data")
def delete_my_data(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in."}, status_code=401)

    db.query(ReminderModel).filter(ReminderModel.user_id == user.id).delete()
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    db.commit()

    try:
        import ai.mongo as mongo_module

        col = mongo_module.get_collection("reminder_logs")
        if col is not None:
            col.delete_many({"user_id": user.id})
        col2 = mongo_module.get_collection("chat_logs")
        if col2 is not None:
            col2.delete_many({"user_id": user.id})
        col3 = mongo_module.get_collection("mood_logs")
        if col3 is not None:
            col3.delete_many({"user_id": user.id})
    except Exception as e:
        print(f"[delete_my_data] MongoDB cleanup error: {e}")

    resp = JSONResponse({"status": "ok", "message": "All data deleted."})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.delete("/delete_account")
def delete_account(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in."}, status_code=401)

    user_id = user.id

    db.query(ReminderModel).filter(ReminderModel.user_id == user_id).delete()
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    db.query(User).filter(User.id == user_id).delete()

    db.commit()

    try:
        import ai.mongo as mongo_module

        for collection_name in ["reminder_logs", "chat_logs", "mood_logs"]:
            col = mongo_module.get_collection(collection_name)
            if col is not None:
                col.delete_many({"user_id": user_id})
    except Exception as e:
        print(f"[delete_account] MongoDB cleanup error: {e}")

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
