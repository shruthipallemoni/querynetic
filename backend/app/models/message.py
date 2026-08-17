"""
One row per message in a conversation — both the user's question and the
assistant's answer. This is the single source of truth for BOTH what the
sidebar displays AND what gets fed back into the Planner as conversation
context on the next question (see api/chat.py) — one table serving two
jobs, instead of the frontend's display state and the pipeline's memory
silently drifting out of sync.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON, func
from app.core.db import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant" | "error"
    content = Column(Text, nullable=False)
    queries = Column(JSON, nullable=True)      # SQL trace, assistant messages only
    validated = Column(Boolean, nullable=True)
    created_at = Column(DateTime, server_default=func.now())