"""
One row per chat conversation. Title is auto-generated from the first
question (see api/conversations.py) — same pattern as ChatGPT-style history
sidebars, so the user never has to name a conversation manually.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.core.db import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    database_id = Column(String, nullable=False)
    title = Column(String, nullable=False, default="New conversation")
    created_at = Column(DateTime, server_default=func.now())