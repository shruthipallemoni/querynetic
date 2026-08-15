"""
Stores each user's connected business databases — in Querynetic's OWN app
database, not the connected database itself. The connection string is
ALWAYS encrypted before it reaches this table (see core/encryption.py);
nothing here ever holds a plain-text password.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.core.db import Base


class DatabaseConnection(Base):
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Slug used as the database_id throughout the pipeline (state, Chroma
    # collection names, the connector registry) — must be unique per user.
    name = Column(String, nullable=False)
    encrypted_connection_string = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())