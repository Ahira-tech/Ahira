"""
reminders.py — Ahira
Reminders stored in PostgreSQL via SQLAlchemy.
Chat logs and analytics stored in MongoDB.
"""

import os
from datetime import datetime
from ai.database import SessionLocal
from ai.models import Reminder

MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb+srv://ghastejyoti_db_user:cojVhpnUYP6xy22q@cluster0.yl8d8av.mongodb.net/?appName=Cluster0"
)

_mongo_client = None


def _get_mongo_client():
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client
    try:
        from pymongo import MongoClient
        client = MongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
        )
        client.admin.command("ping")
        _mongo_client = client
        print("[MongoDB] ✅ Connected")
        return client
    except Exception as e:
        print(f"[MongoDB] ❌ {e}")
        return None


def _mongo_col(name: str):
    client = _get_mongo_client()
    if client is None:
        return None
    return client["ahira_db"][name]


def get_mongo_status() -> dict:
    global _mongo_client
    _mongo_client = None
    try:
        from pymongo import MongoClient
        client = MongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
        )
        client.admin.command("ping")
        cols = client["ahira_db"].list_collection_names()
        return {"connected": True, "collections": cols}
    except Exception as e:
        return {"connected": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────
# REMINDERS — PostgreSQL via SQLAlchemy
# ─────────────────────────────────────────────────────────────

def add_reminder(task, date=None, time=None, priority="normal", user_id=1):
    db = SessionLocal()
    try:
        reminder = Reminder(
            user_id=user_id,
            task=task,
            date=date,
            time=time,
            priority=priority,
        )
        db.add(reminder)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[reminders.py] add_reminder failed: {e}")
    finally:
        db.close()

    try:
        col = _mongo_col("reminder_logs")
        if col is not None:
            col.insert_one({
                "user_id":    user_id,
                "task":       task,
                "date":       date,
                "time":       time,
                "priority":   priority,
                "created_at": datetime.utcnow(),
            })
    except Exception as e:
        print(f"[MongoDB] reminder log failed: {e}")


def get_reminders(user_id=1):
    db = SessionLocal()
    try:
        rows = (
            db.query(Reminder)
            .filter(Reminder.user_id == user_id)
            .order_by(Reminder.completed.asc(), Reminder.id.desc())
            .all()
        )
        return [
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
    finally:
        db.close()


def delete_reminder(reminder_id, user_id=1):
    db = SessionLocal()
    try:
        db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[reminders.py] delete_reminder failed: {e}")
    finally:
        db.close()


def toggle_reminder(reminder_id, user_id=1):
    db = SessionLocal()
    try:
        reminder = db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        ).first()
        if reminder:
            reminder.completed = 0 if reminder.completed == 1 else 1
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"[reminders.py] toggle_reminder failed: {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# CHAT LOGS — MongoDB
# ─────────────────────────────────────────────────────────────

def save_chat_log(user_id: int, user_message: str, bot_reply: str):
    try:
        col = _mongo_col("chat_logs")
        if col is not None:
            col.insert_one({
                "user_id":    user_id,
                "user_msg":   user_message,
                "bot_reply":  bot_reply,
                "created_at": datetime.utcnow(),
            })
    except Exception as e:
        print(f"[MongoDB] chat log failed: {e}")
