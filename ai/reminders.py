import os
from datetime import datetime
from ai.database import get_connection, _p, _all, _row, USE_POSTGRES

# ─────────────────────────────────────────────────────────────
# MONGODB — for chat logs and analytics only
# Core app data (reminders, users) stays in PostgreSQL/SQLite
# ─────────────────────────────────────────────────────────────

MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb+srv://ghastejyoti_db_user:cojVhpnUYP6xy22q@cluster0.yl8d8av.mongodb.net/?appName=Cluster0"
)


def _mongo(collection: str):
    """Returns MongoDB collection or None if unavailable."""
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
        return client["ahira_db"][collection]
    except Exception as e:
        print(f"[MongoDB] {e}")
        return None


def get_mongo_status() -> dict:
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
# REMINDERS — PostgreSQL / SQLite
# ─────────────────────────────────────────────────────────────

def add_reminder(task, date=None, time=None, priority="normal", user_id=1):
    ph   = _p()
    conn = get_connection()
    c    = conn.cursor()
    c.execute(
        f"INSERT INTO reminders (user_id,task,date,time,priority,completed) VALUES ({ph},{ph},{ph},{ph},{ph},0)",
        (user_id, task, date, time, priority)
    )
    conn.commit()
    conn.close()

    # Also log to MongoDB (best-effort, non-blocking)
    try:
        col = _mongo("reminder_logs")
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
    ph   = _p()
    conn = get_connection()
    c    = conn.cursor()
    c.execute(
        f"SELECT id,task,date,time,priority,completed FROM reminders WHERE user_id={ph} ORDER BY completed ASC, id DESC",
        (user_id,)
    )
    rows = _all(c)
    conn.close()
    return rows


def delete_reminder(reminder_id, user_id=1):
    ph   = _p()
    conn = get_connection()
    c    = conn.cursor()
    c.execute(f"DELETE FROM reminders WHERE id={ph} AND user_id={ph}", (reminder_id, user_id))
    conn.commit()
    conn.close()


def toggle_reminder(reminder_id, user_id=1):
    ph   = _p()
    conn = get_connection()
    c    = conn.cursor()
    c.execute(
        f"UPDATE reminders SET completed = CASE WHEN completed=1 THEN 0 ELSE 1 END WHERE id={ph} AND user_id={ph}",
        (reminder_id, user_id)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# CHAT LOGS — MongoDB only
# ─────────────────────────────────────────────────────────────

def save_chat_log(user_id: int, user_message: str, bot_reply: str):
    try:
        col = _mongo("chat_logs")
        if col is not None:
            col.insert_one({
                "user_id":    user_id,
                "user_msg":   user_message,
                "bot_reply":  bot_reply,
                "created_at": datetime.utcnow(),
            })
    except Exception as e:
        print(f"[MongoDB] chat log failed: {e}")
