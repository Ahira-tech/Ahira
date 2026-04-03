"""
database.py — Auto-detects environment.
Local = SQLite, Render = PostgreSQL (DATABASE_URL env var or hardcoded fallback)
"""

import os
import hashlib
import secrets

# Render internal URL — used when deployed on Render
RENDER_DB_URL = "postgresql://ahira_db_user:q21CDcVJZXZhIfGBqT7V6E8ibnM33dse@dpg-d77ok1ua2pns73au3t3g-a/ahira_db"

DATABASE_URL = os.environ.get("DATABASE_URL", RENDER_DB_URL)

# If running locally without any pg server, fall back to SQLite
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    # Quick connectivity test
    _test = psycopg2.connect(DATABASE_URL, connect_timeout=5, cursor_factory=RealDictCursor)
    _test.close()
    USE_POSTGRES = True
    print("[DB] Connected to PostgreSQL ✓")
except Exception as _e:
    USE_POSTGRES = False
    print(f"[DB] PostgreSQL unavailable ({_e}), falling back to SQLite")

if not USE_POSTGRES:
    import sqlite3

    DB_PATH = "data/ahira.db"

    def get_connection():
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

else:
    def get_connection():
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    if USE_POSTGRES:
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
                user_id    INTEGER NOT NULL REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                email      TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for sql in [
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]:
            try:
                c.execute(sql)
            except Exception:
                pass

    conn.commit()
    conn.close()
    print("[DB] Tables ready ✓")


def _p():
    """Return correct placeholder for current DB."""
    return "%s" if USE_POSTGRES else "?"


def create_user(name: str, email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    p = _p()
    try:
        if USE_POSTGRES:
            c.execute(
                f"INSERT INTO users (name, email, password) VALUES ({p},{p},{p}) RETURNING id",
                (name.strip(), email.strip().lower(), hash_password(password))
            )
            row = c.fetchone()
            user_id = row["id"]
        else:
            c.execute(
                f"INSERT INTO users (name, email, password) VALUES ({p},{p},{p})",
                (name.strip(), email.strip().lower(), hash_password(password))
            )
            user_id = c.lastrowid
        conn.commit()
        return {"id": user_id, "name": name.strip(), "email": email.strip().lower()}
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    p = _p()
    c.execute(
        f"SELECT id, name, email FROM users WHERE email={p} AND password={p}",
        (email.strip().lower(), hash_password(password))
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    conn = get_connection()
    c = conn.cursor()
    p = _p()
    c.execute(f"INSERT INTO sessions (token, user_id) VALUES ({p},{p})", (token, user_id))
    conn.commit()
    conn.close()
    return token


def get_user_from_token(token: str):
    if not token:
        return None
    conn = get_connection()
    c = conn.cursor()
    p = _p()
    c.execute(f"""
        SELECT u.id, u.name, u.email
        FROM sessions s JOIN users u ON s.user_id = u.id
        WHERE s.token = {p}
    """, (token,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(token: str):
    conn = get_connection()
    c = conn.cursor()
    p = _p()
    c.execute(f"DELETE FROM sessions WHERE token={p}", (token,))
    conn.commit()
    conn.close()
