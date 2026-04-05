"""
main.py — Ahira
FastAPI app using SQLAlchemy + PostgreSQL.
All existing UI and API routes preserved exactly.
"""

from fastapi import FastAPI, Request, Response, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

# ── Internal imports ──────────────────────────────────────────
from ai.database import engine, get_db, test_connection, Base
from ai.models   import User, UserSession, Reminder as ReminderModel
import ai.crud   as crud

# ── App setup ─────────────────────────────────────────────────
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SESSION_COOKIE = "ahira_session"


# ── Create all tables on startup ──────────────────────────────
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ok = test_connection()
    if ok:
        print("[Ahira] ✅ PostgreSQL connected and tables ready")
    else:
        print("[Ahira] ❌ PostgreSQL connection failed — check DATABASE_URL")


# ── Helper: get current user from cookie ─────────────────────
def current_user(request: Request, db: Session = None):
    token = request.cookies.get(SESSION_COOKIE)
    if not token or db is None:
        return None
    return crud.get_user_from_token(db, token)


# ── Pydantic schemas ──────────────────────────────────────────
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
# AUTH ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.post("/register")
def register(body: RegisterBody, response: Response, db: Session = Depends(get_db)):
    if not body.name.strip() or not body.email.strip() or not body.password:
        return JSONResponse({"status": "error", "message": "All fields are required."}, status_code=400)
    if len(body.password) < 6:
        return JSONResponse({"status": "error", "message": "Password must be at least 6 characters."}, status_code=400)

    user = crud.create_user(db, body.name, body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Email already registered."}, status_code=409)

    token = crud.create_session(db, user.id)
    resp  = JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=30*24*3600)
    return resp


@app.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Incorrect email or password."}, status_code=401)

    token = crud.create_session(db, user.id)
    resp  = JSONResponse({"status": "ok", "user": {"name": user.name, "email": user.email}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=30*24*3600)
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
# REMINDER ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/reminders")
def list_reminders(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    uid  = user.id if user else 1
    rows = crud.get_reminders(db, uid)
    tasks = [
        {
            "id":        r.id,
            "task":      r.task,
            "date":      r.date,
            "time":      r.time,
            "priority":  r.priority,
            "completed": r.completed,
        }
        for r in rows
    ]
    return {"tasks": tasks}


@app.post("/add_reminder")
def create_reminder(body: ReminderBody, request: Request, db: Session = Depends(get_db)):
    if not body.task or not body.task.strip():
        return {"status": "error", "message": "Task cannot be empty"}
    user = current_user(request, db)
    uid  = user.id if user else 1
    crud.add_reminder(db, uid, body.task, body.date, body.time, body.priority)
    return {"status": "success"}


@app.delete("/reminder/{reminder_id}")
def delete_task(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    uid  = user.id if user else 1
    crud.delete_reminder(db, reminder_id, uid)
    return {"status": "deleted"}


@app.post("/reminder/{reminder_id}/toggle")
def toggle_task(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    uid  = user.id if user else 1
    crud.toggle_reminder(db, reminder_id, uid)
    return {"status": "updated"}


# ─────────────────────────────────────────────────────────────
# TEST / STATUS ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    """Simple connectivity test — returns PostgreSQL status."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "PostgreSQL connected ✅"}
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/db-status")
def db_status(db: Session = Depends(get_db)):
    """Detailed status — used by /db-test page."""
    try:
        db.execute(text("SELECT 1"))
        user_count     = db.query(User).count()
        reminder_count = db.query(ReminderModel).count()
        return {
            "postgresql": {
                "backend":            "postgresql",
                "postgres_url_set":   True,
                "psycopg2_available": True,
                "status":             "connected",
                "user_count":         user_count,
                "reminder_count":     reminder_count,
            },
            "mongodb": {
                "connected": False,
                "error":     "MongoDB not configured yet"
            }
        }
    except Exception as e:
        return {
            "postgresql": {
                "backend":            "postgresql",
                "postgres_url_set":   True,
                "psycopg2_available": True,
                "status":             "error",
                "error":              str(e),
            },
            "mongodb": {"connected": False, "error": "MongoDB not configured yet"}
        }


@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    """List all users — for testing only."""
    users = crud.list_users(db)
    return {"users": [{"id": u.id, "name": u.name, "email": u.email} for u in users]}


@app.get("/health")
def health():
    return {"status": "ok"}
