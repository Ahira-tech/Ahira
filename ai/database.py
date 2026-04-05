import os
import sqlite3
import hashlib
import secrets

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

POSTGRES_URL = os.environ.get(
    "POSTGRES_URL",
    "postgresql://postgres:Himanshu@9119@db.vshbubcofxoekbdseiqt.supabase.co:5432/postgres"
)

SQLITE_PATH = "data/ahira.db"

# ─────────────────────────────────────────────────────────────
# BACKEND DETECTION
# ─────────────────────────────────────────────────────────────

def _try_import_psycopg2():
    try:
        import psycopg2
        return psycopg2
    except ImportError:
        return None

_psycopg2 = _try_import_psycopg2()
USE_POSTGRES = bool(_psycopg2 and POSTGRES_URL)


def get_connection():
    if USE_POSTGRES:
        return _psycopg2.connect(POSTGRES_URL)
    else:
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def _placeholder(use_postgres: bool) -> str:
    return "%s" if use_postgres else "?"


def _fetchrow(cursor):
    if USE_POSTGRES:
        row = cursor.fetchone()
        if row is None:
            return None
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))
    else:
        row = cursor.fetchone()
        return dict(row) if row else None


def _fetchall(cursor):
    if USE_POSTGRES:
        rows = cursor.fetchall()
        if not rows:
            return []
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, r)) for r in rows]
    else:
        return [dict(r) for r in cursor.fetchall()]


# ─────────────────────────────────────────────────────────────
# INIT DB
# ─────────────────────────────────────────────────────────────

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
                user_id    INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
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
    print(f"[DB] Initialized using {'PostgreSQL (Supabase)' if USE_POSTGRES else 'SQLite'}")


# ─────────────────────────────────────────────────────────────
# USER AUTH
# ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(name: str, email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    try:
        if USE_POSTGRES:
            c.execute(
                f"INSERT INTO users (name, email, password) VALUES ({p}, {p}, {p}) RETURNING id",
                (name.strip(), email.strip().lower(), hash_password(password))
            )
            row = c.fetchone()
            user_id = row[0]
        else:
            c.execute(
                f"INSERT INTO users (name, email, password) VALUES ({p}, {p}, {p})",
                (name.strip(), email.strip().lower(), hash_password(password))
            )
            user_id = c.lastrowid
        conn.commit()
        return {"id": user_id, "name": name, "email": email}
    except Exception as e:
        err = str(e).lower()
        if "unique" in err or "duplicate" in err:
            return None
        raise
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    c.execute(
        f"SELECT id, name, email FROM users WHERE email={p} AND password={p}",
        (email.strip().lower(), hash_password(password))
    )
    row = _fetchrow(c)
    conn.close()
    return row


def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    c.execute(f"INSERT INTO sessions (token, user_id) VALUES ({p}, {p})", (token, user_id))
    conn.commit()
    conn.close()
    return token


def get_user_from_token(token: str):
    if not token:
        return None
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    c.execute(f"""
        SELECT u.id, u.name, u.email
        FROM sessions s JOIN users u ON s.user_id = u.id
        WHERE s.token = {p}
    """, (token,))
    row = _fetchrow(c)
    conn.close()
    return row


def delete_session(token: str):
    conn = get_connection()
    c = conn.cursor()
    p = _placeholder(USE_POSTGRES)
    c.execute(f"DELETE FROM sessions WHERE token={p}", (token,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# STATUS CHECK
# ─────────────────────────────────────────────────────────────

def get_db_status() -> dict:
    return {
        "backend": "postgresql" if USE_POSTGRES else "sqlite",
        "postgres_url_set": bool(POSTGRES_URL),
        "psycopg2_available": bool(_psycopg2),
    }
