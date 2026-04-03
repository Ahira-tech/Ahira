from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from database import (
    init_db, create_user, authenticate_user,
    create_session, get_user_from_token, delete_session
)
from reminders import get_reminders, add_reminder, delete_reminder, toggle_reminder

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SESSION_COOKIE = "ahira_session"


def current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    return get_user_from_token(token)


class RegisterBody(BaseModel):
    name: str
    email: str
    password: str


class LoginBody(BaseModel):
    email: str
    password: str


class Reminder(BaseModel):
    task: str
    date: Optional[str] = None
    time: Optional[str] = None
    priority: str = "normal"


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/register")
def register(body: RegisterBody):
    if not body.name.strip() or not body.email.strip() or not body.password:
        return JSONResponse({"status": "error", "message": "All fields are required."}, status_code=400)
    if len(body.password) < 6:
        return JSONResponse({"status": "error", "message": "Password must be at least 6 characters."}, status_code=400)
    user = create_user(body.name, body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Email already registered."}, status_code=409)
    token = create_session(user["id"])
    resp  = JSONResponse({"status": "ok", "user": {"name": user["name"], "email": user["email"]}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=30*24*3600)
    return resp


@app.post("/login")
def login(body: LoginBody):
    user = authenticate_user(body.email, body.password)
    if not user:
        return JSONResponse({"status": "error", "message": "Incorrect email or password."}, status_code=401)
    token = create_session(user["id"])
    resp  = JSONResponse({"status": "ok", "user": {"name": user["name"], "email": user["email"]}})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=30*24*3600)
    return resp


@app.post("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        delete_session(token)
    resp = JSONResponse({"status": "ok"})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.get("/me")
def me(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"status": "guest"})
    return JSONResponse({"status": "ok", "user": {"name": user["name"], "email": user["email"]}})


@app.get("/reminders")
def list_reminders(request: Request):
    user = current_user(request)
    uid  = user["id"] if user else 1
    return {"tasks": get_reminders(uid)}


@app.post("/add_reminder")
def create_reminder(reminder: Reminder, request: Request):
    if not reminder.task or not reminder.task.strip():
        return {"status": "error", "message": "Task cannot be empty"}
    user = current_user(request)
    uid  = user["id"] if user else 1
    add_reminder(reminder.task, reminder.date, reminder.time, reminder.priority, uid)
    return {"status": "success"}


@app.delete("/reminder/{reminder_id}")
def delete_task(reminder_id: str, request: Request):
    user = current_user(request)
    uid  = user["id"] if user else 1
    # Try int (SQLite) else keep string (MongoDB ObjectId)
    try:
        rid = int(reminder_id)
    except ValueError:
        rid = reminder_id
    delete_reminder(rid, uid)
    return {"status": "deleted"}


@app.post("/reminder/{reminder_id}/toggle")
def toggle_task(reminder_id: str, request: Request):
    user = current_user(request)
    uid  = user["id"] if user else 1
    try:
        rid = int(reminder_id)
    except ValueError:
        rid = reminder_id
    toggle_reminder(rid, uid)
    return {"status": "updated"}


@app.get("/health")
def health():
    return {"status": "ok"}
