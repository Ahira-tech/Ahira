"""
reminders.py — Auto-detects environment.
Tries MongoDB first (Render), falls back to SQLite (local).
"""

import os

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://ghastejyoti_db_user:OBnYk68HFeJlzbNo@cluster0.yl8d8av.mongodb.net/ahira?retryWrites=true&w=majority&appName=Cluster0"
)

USE_MONGO = False

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from bson import ObjectId
    from datetime import datetime

    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    _client.admin.command("ping")
    USE_MONGO = True
    print("[Reminders] Connected to MongoDB ✓")
except Exception as _e:
    print(f"[Reminders] MongoDB unavailable ({_e}), falling back to SQLite")


# ── MONGO IMPLEMENTATION ──────────────────────────────────────
if USE_MONGO:

    def _col():
        return _client["ahira"]["reminders"]

    def add_reminder(task, date=None, time=None, priority="normal", user_id=1):
        _col().insert_one({
            "user_id":    user_id,
            "task":       task,
            "date":       date,
            "time":       time,
            "priority":   priority,
            "completed":  0,
            "created_at": datetime.utcnow()
        })

    def get_reminders(user_id=1):
        docs = _col().find(
            {"user_id": user_id},
            sort=[("completed", ASCENDING), ("_id", DESCENDING)]
        )
        result = []
        for doc in docs:
            result.append({
                "id":        str(doc["_id"]),
                "task":      doc.get("task", ""),
                "date":      doc.get("date"),
                "time":      doc.get("time"),
                "priority":  doc.get("priority", "normal"),
                "completed": doc.get("completed", 0),
            })
        return result

    def delete_reminder(reminder_id, user_id=1):
        try:
            _col().delete_one({"_id": ObjectId(str(reminder_id)), "user_id": user_id})
        except Exception as e:
            print(f"[delete_reminder] {e}")

    def toggle_reminder(reminder_id, user_id=1):
        try:
            doc = _col().find_one({"_id": ObjectId(str(reminder_id)), "user_id": user_id})
            if doc:
                new_val = 0 if doc.get("completed") == 1 else 1
                _col().update_one(
                    {"_id": ObjectId(str(reminder_id))},
                    {"$set": {"completed": new_val}}
                )
        except Exception as e:
            print(f"[toggle_reminder] {e}")


# ── SQLITE FALLBACK ───────────────────────────────────────────
else:
    import sqlite3
    import os as _os

    DB_PATH = "data/ahira.db"

    def _get_conn():
        _os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table():
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER DEFAULT 1,
                task      TEXT NOT NULL,
                date      TEXT,
                time      TEXT,
                priority  TEXT DEFAULT 'normal',
                completed INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    _ensure_table()

    def add_reminder(task, date=None, time=None, priority="normal", user_id=1):
        conn = _get_conn()
        conn.execute(
            "INSERT INTO reminders (user_id,task,date,time,priority,completed) VALUES (?,?,?,?,?,0)",
            (user_id, task, date, time, priority)
        )
        conn.commit()
        conn.close()

    def get_reminders(user_id=1):
        conn = _get_conn()
        rows = conn.execute(
            "SELECT id,task,date,time,priority,completed FROM reminders WHERE user_id=? ORDER BY completed ASC, id DESC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_reminder(reminder_id, user_id=1):
        conn = _get_conn()
        conn.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (reminder_id, user_id))
        conn.commit()
        conn.close()

    def toggle_reminder(reminder_id, user_id=1):
        conn = _get_conn()
        conn.execute("""
            UPDATE reminders SET completed = CASE WHEN completed=1 THEN 0 ELSE 1 END
            WHERE id=? AND user_id=?
        """, (reminder_id, user_id))
        conn.commit()
        conn.close()
