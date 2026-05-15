"""
main.py — Ahira
PostgreSQL + MongoDB. All data is user-scoped.
Sessions expire after 30 days. Guests see empty data.
"""

from fastapi import FastAPI, Request, Response, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from fastapi import Query

from ai.database import engine, get_db, test_connection, Base
from ai.models   import User, UserSession, Reminder as ReminderModel
import ai.crud   as crud
import ai.mongo  as mongo

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SESSION_COOKIE   = "ahira_session"
SESSION_MAX_DAYS = 30


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
    """
    Returns the User object if the session cookie is valid and not expired.
    Returns None for guests or expired sessions.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None

    session = db.query(UserSession).filter(UserSession.token == token).first()
    if not session:
        return None

    # Check expiry — sessions older than 30 days are invalid
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


def _safe_language(value: Optional[str]) -> str:
    v = (value or "en").strip().lower()
    return v if v in {"en", "hi", "mr"} else "en"


def _safe_limit(value: int) -> int:
    return max(1, min(value, 50))


def _safe_offset(value: int) -> int:
    return max(0, value)


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
    resp  = JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax",
                    max_age=SESSION_MAX_DAYS * 24 * 3600)
    return resp


@app.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Incorrect email or password."}, status_code=401)

    token = crud.create_session(db, user.id)
    resp  = JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax",
                    max_age=SESSION_MAX_DAYS * 24 * 3600)
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
        return {"tasks": []}   # guests see nothing
    rows = crud.get_reminders(db, user.id)
    return {"tasks": [
        {"id": r.id, "task": r.task, "date": r.date,
         "time": r.time, "priority": r.priority, "completed": r.completed}
        for r in rows
    ]}


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



@app.get("/feeds")
def get_feeds(
    request: Request,
    db: Session = Depends(get_db),
    language: str = Query("en"),
    limit: int = Query(20),
    offset: int = Query(0),
):
    lang = _safe_language(language)
    lim = _safe_limit(limit)
    off = _safe_offset(offset)

    # unified + ranked feed: sponsored -> important news -> regular news -> ahira picks
    sql = text("""
    WITH sponsored AS (
      SELECT
        'sponsored_' || id::text AS id,
        'sponsored_post'::text AS type,
        COALESCE(content, title) AS content,
        image_url,
        brand_name AS source_name,
        redirect_url AS source_url,
        target_language AS language,
        created_at,
        1 AS priority,
        CASE
          WHEN target_language = :lang THEN 0
          WHEN target_language = 'en' THEN 1
          ELSE 2
        END AS language_rank,
        created_at AS secondary_order
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
        created_at,
        2 AS priority,
        CASE
          WHEN language = :lang THEN 0
          WHEN language = 'en' THEN 1
          ELSE 2
        END AS language_rank,
        published_at AS secondary_order
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
        created_at,
        3 AS priority,
        CASE
          WHEN language = :lang THEN 0
          WHEN language = 'en' THEN 1
          ELSE 2
        END AS language_rank,
        COALESCE(published_at, created_at) AS secondary_order
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
        created_at,
        5 AS priority,
        CASE
          WHEN language = :lang THEN 0
          WHEN language = 'en' THEN 1
          ELSE 2
        END AS language_rank,
        created_at AS secondary_order
      FROM ahira_picks
      WHERE language IN (:lang, 'en')
    )
    SELECT id, type, content, image_url, source_name, source_url, language, created_at AS "createdAt"
    FROM (
      SELECT * FROM sponsored
      UNION ALL
      SELECT * FROM important_news
      UNION ALL
      SELECT * FROM regular_news
      UNION ALL
      SELECT * FROM ahira
    ) rows
    ORDER BY priority ASC, language_rank ASC, secondary_order DESC NULLS LAST, "createdAt" DESC
    LIMIT :lim OFFSET :off;
    """)

    rows = db.execute(sql, {"lang": lang, "lim": lim, "off": off}).mappings().all()
    return [dict(r) for r in rows]


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
        text("""
            INSERT INTO feed_reports (post_id, post_type, reason, details, reporter_user_id)
            VALUES (:post_id, :post_type, :reason, :details, :reporter_user_id)
        """),
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

    CREATE INDEX IF NOT EXISTS idx_sponsored_posts_active_window
      ON sponsored_posts (is_active, start_date, end_date);

    CREATE INDEX IF NOT EXISTS idx_sponsored_posts_target_language
      ON sponsored_posts (target_language);

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
    """
    db.execute(text(migration_sql))
    db.commit()


# ─────────────────────────────────────────────────────────────
# DELETE MY DATA — wipes all user data from PostgreSQL
# ─────────────────────────────────────────────────────────────

@app.delete("/delete_my_data")
def delete_my_data(request: Request, db: Session = Depends(get_db)):
    """
    Deletes all data belonging to the authenticated user:
    - All reminders
    - All sessions (forces re-login on all devices)
    The user account itself is NOT deleted (they can sign back in).
    To also delete the account, use /delete_account instead.
    """
    user = current_user(request, db)
    if not user:
        return JSONResponse(
            {"status": "error", "message": "Not logged in."},
            status_code=401
        )

    # Delete all reminders for this user
    db.query(ReminderModel).filter(
        ReminderModel.user_id == user.id
    ).delete()

    # Delete all sessions (forces re-login everywhere)
    db.query(UserSession).filter(
        UserSession.user_id == user.id
    ).delete()

    db.commit()

    # Also try to clear MongoDB logs for this user
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
    """
    Permanently deletes the user account and ALL associated data.
    This is irreversible.
    """
    user = current_user(request, db)
    if not user:
        return JSONResponse(
            {"status": "error", "message": "Not logged in."},
            status_code=401
        )

    user_id = user.id

    # Delete all reminders (cascade should handle this but explicit is safer)
    db.query(ReminderModel).filter(ReminderModel.user_id == user_id).delete()

    # Delete all sessions
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()

    # Delete the user account itself
    db.query(User).filter(User.id == user_id).delete()

    db.commit()

    # Clear MongoDB data
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
            "backend": "postgresql", "postgres_url_set": True,
            "psycopg2_available": True, "status": "connected",
            "user_count":     db.query(User).count(),
            "reminder_count": db.query(ReminderModel).count(),
            "session_count":  db.query(UserSession).count(),
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
    return {"status": "ok"}

@app.delete("/delete_my_data")
def delete_my_data(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return JSONResponse({"status":"error","message":"Not logged in."}, status_code=401)
    # Delete all reminders
    db.query(ReminderModel).filter(ReminderModel.user_id == user.id).delete()
    # Delete all sessions (forces re-login)
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    db.commit()
    resp = JSONResponse({"status":"ok"})
    resp.delete_cookie(SESSION_COOKIE)
    return resp
