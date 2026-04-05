"""
database.py
-----------
Sets up the SQLAlchemy engine and session.
All other files import from here.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# ── 1. Read DATABASE_URL from environment ─────────────────────
# Render gives "postgres://..." but SQLAlchemy needs "postgresql://..."
# We fix that automatically here.

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres.vshbubcofxoekbdseiqt:Himanshu1202@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
)

# Fix "postgres://" → "postgresql://" (Render quirk)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── 2. Create engine ──────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # checks connection is alive before using it
    pool_recycle=300,         # recycle connections every 5 minutes
    connect_args={
        "connect_timeout": 15,
        "options": "-c statement_timeout=30000"
    }
)

# ── 3. Session factory ────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ── 4. Base class for all models ──────────────────────────────
Base = declarative_base()


# ── 5. Dependency for FastAPI routes ─────────────────────────
def get_db():
    """
    Use this in FastAPI endpoints:
        db: Session = Depends(get_db)
    Opens a session, yields it, closes it after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 6. Connection test ────────────────────────────────────────
def test_connection() -> bool:
    """Returns True if PostgreSQL is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Connection test failed: {e}")
        return False
