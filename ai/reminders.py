"""
reminders.py — Ahira
Reminders stored in PostgreSQL.
Chat logs and analytics stored in MongoDB.
"""

import os
from datetime import datetime
import psycopg2.extras
from ai.database import get_connection

# ─────────────────────────────────────────────────────────────
# MONGODB
# ─────────────────────────────────────────────────────────────

MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb+srv://ghastejyoti_db_user:cojVhpnUYP6xy22q@cluster0.yl8d8av.mongodb.net/?appName=Cluster0"
)

_mongo_client = None


def _get_mongo_client():
    """Returns a cached MongoDB client, or None if unavailable."""
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
    """Called by /db-status endpoint."""
    global _mongo_client
    _mongo_client = None          # force fresh check
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
# REMINDERS — PostgreSQL
# ─────────────────────────────────────────────────────────────

def add_reminder(task, date=None, time=None, priority="normal", user_id=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO reminders (user_id, task, date, time, priority, completed) VALUES (%s,%s,%s,%s,%s,0)",
        (user_id, task, date, time, priority)
    )
    conn.commit()
    conn.close()

    # Log to MongoDB (non-blocking)
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
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, task, date, time, priority, completed FROM reminders WHERE user_id=%s ORDER BY completed ASC, id DESC",
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_reminder(reminder_id, user_id=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "DELETE FROM reminders WHERE id=%s AND user_id=%s",
        (reminder_id, user_id)
    )
    conn.commit()
    conn.close()


def toggle_reminder(reminder_id, user_id=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE reminders SET completed = CASE WHEN completed=1 THEN 0 ELSE 1 END WHERE id=%s AND user_id=%s",
        (reminder_id, user_id)
    )
    conn.commit()
    conn.close()


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
