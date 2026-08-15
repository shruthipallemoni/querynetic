"""
Sets up the connection to QUERYNETIC'S OWN database — the one that stores
users, organizations, chat history, and audit logs.

IMPORTANT: this is NOT the user's connected business database (their
PostgreSQL/MySQL that they want analyzed). That connection logic lives in
db_connectors/, deliberately kept separate so the two are never confused.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.APP_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — hands a route a DB session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()