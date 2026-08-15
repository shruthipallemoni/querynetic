"""
The User model — Querynetic's own app database, not the user's connected
business database.

`role` is a plain string on purpose for the MVP (not a separate table).
Full multi-tenant organizations with per-org roles come later — this is
the smallest version that still lets us gate access meaningfully today.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    # One of: "viewer", "analyst", "owner" — checked against ROLE_HIERARCHY
    # in core/deps.py, not enforced at the database level.
    role = Column(String, nullable=False, default="viewer")
    created_at = Column(DateTime, server_default=func.now())