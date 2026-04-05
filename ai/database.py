import os
import sqlite3
import hashlib
import secrets

# ─────────────────────────────────────────────────────────────
# POSTGRES URL — set via Render environment variable
# MUST use Supabase POOLER url (port 6543 not 5432)
# Get it from: Supabase → Settings → Database → Connection Pooling → Transaction
# Format: postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
# ─────────────────────────────────────────────────────────────

POSTGRES_URL = os.environ.get("POSTGRES_URL", "")
SQLITE_PATH  = "data/ahira.db"

# ─────────────────────────────────────────────────────────────
# DETECT BACKEND — try PostgreSQL, fall back to SQLite silently
# ─────────────────────────────────────────────────────────────

_pg          = None
USE_POSTGRES = False

if POSTGRES_URL:
    try:
        import psycopg2
        _test = psycopg2.connect(POSTGRES_URL, connect_timeout=10)
        _test.close()
        _pg          = psycopg2
        USE_POSTGRES = True
        print("[DB] PostgreSQL connected successfully ✅")
    except Exception as _e:
        print(f"[DB] PostgreSQL unavailable → using SQLite. Error: {_e}")
else:
    print("[DB] POSTGRES_URL not set → using SQLite")


# ─────────────────────────────────────────────────────────────
# CONNECTION HELPERS
# ─────────────────────────────────────────────────────────────

def get_connection():
    if USE_POSTGRES:
        return _pg.connect(POSTGRES_URL, connect_timeout=10)
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _p():
    return "%s" if USE_POSTGRES else "?"


def _row(cursor):
    if USE_POSTGRES:
        r = cursor.fetchone()
        if r is None:
            return None
        return dict(zip([d[0] for d in cursor.description], r))
    r = cursor.fetchone()
    return dict(r) if r else None


def _all(cursor):
    if USE_POSTGRES:
        rows = cursor.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, r)) for r in rows]
    return [dict(r) for r in cursor.fetchall()]


# Public aliases used by reminders.py
def _placeholder(_ignored): return _p()
def _fetchrow(cursor):      return _row(cursor)
def _fetchall(cursor):      return _all(cursor)


# ─────────────────────────────────────────────────────────────
# INIT TABLES
# ─────────────────────────────────────────────────────────────

def init_db():
    conn = get_connection()
    c    = conn.cursor()

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
        c.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id         SERIAL PRIMARY KEY,
                user_id    INTEGER DEFAULT 1,
                task       TEXT NOT NULL,
                date       TEXT,
                time       TEXT,
                priority   TEXT DEFAULT 'normal',
                completed  INTEGER DEFAULT 0,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
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
        for sql in [
            "ALTER TABLE reminders ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE reminders ADD COLUMN date TEXT",
            "ALTER TABLE reminders ADD COLUMN time TEXT",
            "ALTER TABLE reminders ADD COLUMN priority TEXT DEFAULT 'normal'",
            "ALTER TABLE reminders ADD COLUMN completed INTEGER DEFAULT 0",
            "ALTER TABLE reminders ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]:
            try:
                c.execute(sql)
            except Exception:
                pass

    conn.commit()
    conn.close()
    print(f"[DB] Tables ready — {'PostgreSQL' if USE_POSTGRES else 'SQLite'}")


# ─────────────────────────────────────────────────────────────
# USER AUTH
# ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(name: str, email: str, password: str):
    conn = get_connection()
    c    = conn.cursor()
    ph   = _p()
    try:
        if USE_POSTGRES:
            c.execute(
                f"INSERT INTO users (name,email,password) VALUES ({ph},{ph},{ph}) RETURNING id",
                (name.strip(), email.strip().lower(), hash_password(password))
            )
            user_id = c.fetchone()[0]
        else:
            c.execute(
                f"INSERT INTO users (name,email,password) VALUES ({ph},{ph},{ph})",
                (name.strip(), email.strip().lower(), hash_password(password))
            )
            user_id = c.lastrowid
        conn.commit()
        return {"id": user_id, "name": name, "email": email}
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return None
        raise
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_connection()
    c    = conn.cursor()
    ph   = _p()
    c.execute(
        f"SELECT id,name,email FROM users WHERE email={ph} AND password={ph}",
        (email.strip().lower(), hash_password(password))
    )
    row = _row(c)
    conn.close()
    return row


def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    conn  = get_connection()
    c     = conn.cursor()
    ph    = _p()
    c.execute(f"INSERT INTO sessions (token,user_id) VALUES ({ph},{ph})", (token, user_id))
    conn.commit()
    conn.close()
    return token


def get_user_from_token(token: str):
    if not token:
        return None
    conn = get_connection()
    c    = conn.cursor()
    ph   = _p()
    c.execute(f"""
        SELECT u.id, u.name, u.email
        FROM sessions s JOIN users u ON s.user_id = u.id
        WHERE s.token = {ph}
    """, (token,))
    row = _row(c)
    conn.close()
    return row


def delete_session(token: str):
    conn = get_connection()
    c    = conn.cursor()
    ph   = _p()
    c.execute(f"DELETE FROM sessions WHERE token={ph}", (token,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# STATUS (used by /db-status endpoint)
# ─────────────────────────────────────────────────────────────

def get_db_status() -> dict:
    return {
        "backend":            "postgresql" if USE_POSTGRES else "sqlite",
        "postgres_url_set":   bool(POSTGRES_URL),
        "psycopg2_available": _pg is not None,
    }
