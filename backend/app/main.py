"""
Entry point for the FastAPI application.

Job of this file (and only this file):
- Create the FastAPI app instance
- Register routers from api/
- Register startup/shutdown events (e.g. DB connection pool warmup)

This file should NOT contain business logic or AI pipeline code.
If you're tempted to write agent logic here, it belongs in agents/ instead.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat, databases, conversations
from app.core.db import Base, engine, SessionLocal
from app.core.encryption import decrypt_string
from app.models import user, database_connection, conversation, message  # noqa: F401
from app.models.database_connection import DatabaseConnection
from app.db_connectors.postgres_connector import register_connection
from scripts.seed_test_schema import seed_test_db

app = FastAPI(title="Querynetic API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,  # required for the browser to send/receive the refresh-token cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(databases.router, prefix="/api/databases", tags=["databases"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

    seed_test_db()

    db = SessionLocal()
    try:
        for conn in db.query(DatabaseConnection).all():
            register_connection(conn.name, decrypt_string(conn.encrypted_connection_string))
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}