"""
Endpoints for connecting and listing a user's databases.

Job of this file: encrypt + persist the connection, run schema
introspection, and register it in the in-memory connector registry so
Execution can use it immediately — all in one request, so a newly
connected database is queryable right away, not after a server restart.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.encryption import encrypt_string
from app.core.schema_introspection import introspect_and_index_schema
from app.db_connectors.postgres_connector import register_connection
from app.models.user import User
from app.models.database_connection import DatabaseConnection

router = APIRouter()


class ConnectDatabaseRequest(BaseModel):
    name: str
    connection_string: str


@router.post("/")
def connect_database(
    payload: ConnectDatabaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.user_id == current_user.id,
            DatabaseConnection.name == payload.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already have a database with this name.")

    try:
        table_count = introspect_and_index_schema(payload.name, payload.connection_string)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not connect or read schema: {str(e)}")

    connection = DatabaseConnection(
        user_id=current_user.id,
        name=payload.name,
        encrypted_connection_string=encrypt_string(payload.connection_string),
    )
    db.add(connection)
    db.commit()

    # Available for Execution immediately — no restart needed.
    register_connection(payload.name, payload.connection_string)

    return {"database_id": payload.name, "tables_indexed": table_count}


@router.get("/")
def list_databases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connections = (
        db.query(DatabaseConnection)
        .filter(DatabaseConnection.user_id == current_user.id)
        .all()
    )
    # Only the name is returned — never the connection string, encrypted or not.
    return [{"database_id": c.name} for c in connections]