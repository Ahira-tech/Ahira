"""
mongo.py — Ahira
MongoDB connection for chat logs and analytics.
Place this file inside your ai/ folder.
"""

import os
from datetime import datetime

MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb+srv://ghastejyoti_db_user:cojVhpnUYP6xy22q@cluster0.yl8d8av.mongodb.net/?appName=Cluster0"
)

_client = None


def get_client():
    global _client
    if _client is not None:
        return _client
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        client = MongoClient(
            MONGODB_URL,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True,
        )
        client.admin.command("ping")
        _client = client
        print("[MongoDB] ✅ Connected")
        return _client
    except Exception as e:
        print(f"[MongoDB] ❌ {e}")
        return None


def get_collection(name: str):
    client = get_client()
    if client is None:
        return None
    return client["ahira_db"][name]


def get_status() -> dict:
    global _client
    _client = None
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        client = MongoClient(
            MONGODB_URL,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True,
        )
        client.admin.command("ping")
        cols = client["ahira_db"].list_collection_names()
        return {"connected": True, "collections": cols}
    except Exception as e:
        return {"connected": False, "error": str(e)}


def log_reminder(user_id, task, date=None, time=None, priority="normal"):
    try:
        col = get_collection("reminder_logs")
        if col is not None:
            col.insert_one({
                "user_id": user_id, "task": task,
                "date": date, "time": time,
                "priority": priority, "created_at": datetime.utcnow()
            })
    except Exception as e:
        print(f"[MongoDB] log_reminder failed: {e}")


def save_chat_log(user_id: int, user_message: str, bot_reply: str):
    try:
        col = get_collection("chat_logs")
        if col is not None:
            col.insert_one({
                "user_id": user_id, "user_msg": user_message,
                "bot_reply": bot_reply, "created_at": datetime.utcnow()
            })
    except Exception as e:
        print(f"[MongoDB] save_chat_log failed: {e}")


def log_mood(user_id: int, mood: str, emoji: str):
    try:
        col = get_collection("mood_logs")
        if col is not None:
            col.insert_one({
                "user_id": user_id, "mood": mood,
                "emoji": emoji, "created_at": datetime.utcnow()
            })
    except Exception as e:
        print(f"[MongoDB] log_mood failed: {e}")
