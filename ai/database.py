import sqlite3
import os
import hashlib
import secrets

DB_PATH = "data/ahira.db"


def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sessions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Reminders table — with user_id
    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER DEFAULT 1,
            task       TEXT NOT NULL,
            date       TEXT,
            time       TEXT,
            priority   TEXT DEFAULT 'normal',
            completed  INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe migrations for old databases
    migrations = [
        "ALTER TABLE reminders ADD COLUMN user_id INTEGER DEFAULT 1",
        "ALTER TABLE reminders ADD COLUMN date TEXT",
        "ALTER TABLE reminders ADD COLUMN time TEXT",
        "ALTER TABLE reminders ADD COLUMN priority TEXT DEFAULT 'normal'",
        "ALTER TABLE reminders ADD COLUMN completed INTEGER DEFAULT 0",
        "ALTER TABLE reminders ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    ]
    for sql in migrations:
        try:
            c.execute(sql)
        except Exception:
            pass

    conn.commit()
    conn.close()


# ── User auth ────────────────────────────────────────────────

def create_user(name: str, email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), hash_password(password))
        )
        conn.commit()
        user_id = c.lastrowid
        return {"id": user_id, "name": name, "email": email}
    except sqlite3.IntegrityError:
        return None  # email already exists
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, email FROM users WHERE email=? AND password=?",
        (email.strip().lower(), hash_password(password))
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
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
        FROM sessions s JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    """, (token,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(token: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit()
    conn.close()