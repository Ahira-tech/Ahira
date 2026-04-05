"""
database.py — Ahira
Uses PostgreSQL (Supabase) exclusively.
No SQLite fallback — if connection fails, startup fails loudly.
"""

import os
import hashlib
import secrets
import psycopg2
import psycopg2.extras

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

POSTGRES_URL = os.environ.get(
    "POSTGRES_URL",
    "postgresql://postgres.vshbubcofxoekbdseiqt:Himanshu1202@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
)


# ─────────────────────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────────────────────

def get_connection():
    """Open and return a psycopg2 connection with dict-like rows."""
    conn = psycopg2.connect(
        POSTGRES_URL,
        connect_timeout=15,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    return conn


# ─────────────────────────────────────────────────────────────
# INIT TABLES
# ─────────────────────────────────────────────────────────────

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task       TEXT NOT NULL,
            date       TEXT,
            time       TEXT,
            priority   TEXT DEFAULT 'normal',
            completed  INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] ✅ PostgreSQL tables ready")


# ─────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(name: str, email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id",
            (name.strip(), email.strip().lower(), hash_password(password))
        )
        row = c.fetchone()
        conn.commit()
        return {"id": row["id"], "name": name, "email": email}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, email FROM users WHERE email=%s AND password=%s",
        (email.strip().lower(), hash_password(password))
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
        (token, user_id)
    )
    conn.commit()
    conn.close()
    return token


def get_user_from_token(token: str):
    if not token:
        return None
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.name, u.email
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = %s
    """, (token,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(token: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE token = %s", (token,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# STATUS — used by /db-status endpoint
# ─────────────────────────────────────────────────────────────

def get_db_status() -> dict:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS cnt FROM users")
        row = c.fetchone()
        conn.close()
        return {
            "backend":          "postgresql",
            "postgres_url_set": True,
            "psycopg2_available": True,
            "user_count":       row["cnt"],
            "status":           "connected",
        }
    except Exception as e:
        return {
            "backend":          "postgresql",
            "postgres_url_set": bool(POSTGRES_URL),
            "psycopg2_available": True,
            "status":           "error",
            "error":            str(e),
        }
