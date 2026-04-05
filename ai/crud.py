"""
crud.py
-------
All database read/write operations.
Routes call these functions — keeps routes clean.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ai.models import User, UserSession, Reminder


# ── Users ─────────────────────────────────────────────────────

def create_user(db: Session, name: str, email: str, password: str):
    """Create a new user. Returns user or None if email exists."""
    user = User(
        name     = name.strip(),
        email    = email.strip().lower(),
        password = User.hash_password(password)
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        return None   # email already taken


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email.strip().lower()).first()


def authenticate_user(db: Session, email: str, password: str):
    """Returns user if credentials are correct, else None."""
    user = get_user_by_email(db, email)
    if user and user.check_password(password):
        return user
    return None


def list_users(db: Session):
    """List all users — for testing only."""
    return db.query(User).all()


# ── Sessions ──────────────────────────────────────────────────

def create_session(db: Session, user_id: int) -> str:
    token = UserSession.generate_token()
    session = UserSession(token=token, user_id=user_id)
    db.add(session)
    db.commit()
    return token


def get_user_from_token(db: Session, token: str):
    if not token:
        return None
    session = db.query(UserSession).filter(UserSession.token == token).first()
    return session.user if session else None


def delete_session(db: Session, token: str):
    db.query(UserSession).filter(UserSession.token == token).delete()
    db.commit()


# ── Reminders ─────────────────────────────────────────────────

def add_reminder(db: Session, user_id: int, task: str,
                 date=None, time=None, priority="normal"):
    reminder = Reminder(
        user_id  = user_id,
        task     = task,
        date     = date,
        time     = time,
        priority = priority,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def get_reminders(db: Session, user_id: int):
    return (
        db.query(Reminder)
        .filter(Reminder.user_id == user_id)
        .order_by(Reminder.completed.asc(), Reminder.id.desc())
        .all()
    )


def delete_reminder(db: Session, reminder_id: int, user_id: int):
    db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == user_id
    ).delete()
    db.commit()


def toggle_reminder(db: Session, reminder_id: int, user_id: int):
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == user_id
    ).first()
    if reminder:
        reminder.completed = 0 if reminder.completed == 1 else 1
        db.commit()
