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
from app.api import auth, chat, databases
from app.core.db import Base, engine, SessionLocal
from app.core.encryption import decrypt_string
from app.models import user, database_connection  # noqa: F401 — registers models with Base
from app.models.database_connection import DatabaseConnection
from app.db_connectors.postgres_connector import register_connection
from scripts.seed_test_schema import seed_test_db

app = FastAPI(title="Querynetic API", version="0.1.0")

# Local dev only — the Vite dev server runs on a different port, so the
# browser blocks cross-origin requests without this. A real deployment
# would restrict this to the actual production frontend origin, not "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(databases.router, prefix="/api/databases", tags=["databases"])


@app.on_event("startup")
def create_tables():
    # Simple approach for local development: builds tables directly from
    # the model definitions. Real production systems use a migration tool
    # (Alembic) instead, so schema changes are tracked and reversible —
    # worth adopting once this moves past local testing.
    Base.metadata.create_all(bind=engine)

    # TODO: local-dev shortcut — real per-user databases (below) are the
    # actual design; this just keeps the original hardcoded test_db working
    # for existing test scripts.
    seed_test_db()

    # Reload every previously connected database into the in-memory
    # connector registry. Without this, connections added before a server
    # restart would silently stop working — the registry is memory-only.
    db = SessionLocal()
    try:
        for conn in db.query(DatabaseConnection).all():
            register_connection(conn.name, decrypt_string(conn.encrypted_connection_string))
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}