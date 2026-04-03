import os
from datetime import datetime
from ai.database import get_connection, _placeholder, _fetchrow, _fetchall, USE_POSTGRES

# ─────────────────────────────────────────────────────────────
# MONGODB CONFIG — for storing chat logs / analytics
# Set MONGODB_URL env var in Render dashboard
# Replace <db_password> with your actual MongoDB password
# ─────────────────────────────────────────────────────────────

MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb+srv://ahira_db_user:q21CDcVJZXZhIfGBqT7V6E8ibnM33dse@cluster0.yl8d8av.mongodb.net/?appName=Cluster0"
)


def _get_mongo_collection(collection_name: str):
    """Returns a MongoDB collection or None if unavailable."""
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        # Ping to confirm connection
        client.admin.command("ping")
        db = client["ahira_db"]
        return db[collection_name]
    except Exception as e:
        print(f"[MongoDB] Could not connect: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# REMINDERS — stored in PostgreSQL / SQLite
# ─────────────────────────────────────────────────────────────

def add_reminder(task, date=None, time=None, priority="normal", user_id=1):
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    c.execute(f"""
        INSERT INTO reminders (user_id, task, date, time, priority, completed)
        VALUES ({p}, {p}, {p}, {p}, {p}, 0)
    """, (user_id, task, date, time, priority))
    conn.commit()
    conn.close()

    # Also log to MongoDB for analytics (non-blocking)
    try:
        col = _get_mongo_collection("reminder_logs")
        if col is not None:
            col.insert_one({
                "user_id":    user_id,
                "task":       task,
                "date":       date,
                "time":       time,
                "priority":   priority,
                "created_at": datetime.utcnow()
            })
    except Exception as e:
        print(f"[MongoDB] reminder log failed: {e}")


def get_reminders(user_id=1):
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    c.execute(f"""
        SELECT id, task, date, time, priority, completed
        FROM reminders
        WHERE user_id = {p}
        ORDER BY completed ASC, id DESC
    """, (user_id,))
    rows = _fetchall(c)
    conn.close()
    return rows


def delete_reminder(reminder_id, user_id=1):
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    c.execute(f"DELETE FROM reminders WHERE id={p} AND user_id={p}", (reminder_id, user_id))
    conn.commit()
    conn.close()


def toggle_reminder(reminder_id, user_id=1):
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    if USE_POSTGRES:
        c.execute(f"""
            UPDATE reminders
            SET completed = CASE WHEN completed=1 THEN 0 ELSE 1 END
            WHERE id={p} AND user_id={p}
        """, (reminder_id, user_id))
    else:
        c.execute(f"""
            UPDATE reminders
            SET completed = CASE WHEN completed=1 THEN 0 ELSE 1 END
            WHERE id={p} AND user_id={p}
        """, (reminder_id, user_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# CHAT LOGS — stored in MongoDB
# ─────────────────────────────────────────────────────────────

def save_chat_log(user_id: int, user_message: str, bot_reply: str):
    """Save a chat exchange to MongoDB."""
    try:
        col = _get_mongo_collection("chat_logs")
        if col is not None:
            col.insert_one({
                "user_id":     user_id,
                "user_msg":    user_message,
                "bot_reply":   bot_reply,
                "created_at":  datetime.utcnow()
            })
    except Exception as e:
        print(f"[MongoDB] chat log failed: {e}")


def get_mongo_status() -> dict:
    """Check MongoDB connectivity — used by test page."""
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client["ahira_db"]
        collections = db.list_collection_names()
        return {"connected": True, "collections": collections}
    except Exception as e:
        return {"connected": False, "error": str(e)}
