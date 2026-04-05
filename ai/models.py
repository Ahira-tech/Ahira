"""
models.py
---------
Defines all database tables as Python classes.
SQLAlchemy converts these to real PostgreSQL tables automatically.
"""

import hashlib
import secrets
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ai.database import Base


# ── User ──────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(255), unique=True, nullable=False, index=True)
    password   = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    sessions   = relationship("UserSession", back_populates="user", cascade="all, delete")
    reminders  = relationship("Reminder",    back_populates="user", cascade="all, delete")

    @staticmethod
    def hash_password(pw: str) -> str:
        return hashlib.sha256(pw.encode()).hexdigest()

    def check_password(self, pw: str) -> bool:
        return self.password == self.hash_password(pw)


# ── Session (login tokens) ────────────────────────────────────

class UserSession(Base):
    __tablename__ = "sessions"

    token      = Column(String(64), primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="sessions")

    @staticmethod
    def generate_token() -> str:
        return secrets.token_hex(32)


# ── Reminder / Task ───────────────────────────────────────────

class Reminder(Base):
    __tablename__ = "reminders"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task       = Column(Text, nullable=False)
    date       = Column(String(20), nullable=True)
    time       = Column(String(10), nullable=True)
    priority   = Column(String(20), default="normal")
    completed  = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="reminders")
