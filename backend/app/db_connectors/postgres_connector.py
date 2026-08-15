"""
Handles connecting to the USER'S business database (the one they want
analyzed) — NOT Querynetic's own app database (that's core/db.py).

Rules this file must always follow:
- Use a READ-ONLY database role/user whenever possible (this is a DB-admin
  level control — set up when the user connects their database, not
  something Python alone can guarantee)
- ALSO enforce read-only at the connection level in code below, as a second,
  independent layer — same defense-in-depth pattern used in SQL Validation.
- Never log or print raw credentials.
- Credentials are pulled decrypted only at the moment of connection, never
  stored decrypted anywhere else.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine

# TODO: replace with a real encrypted-credential lookup (DB row -> decrypt
# -> connection string), keyed by database_id. This placeholder exists so
# Execution can be built and tested against the shape of a real connector.
_CONNECTION_REGISTRY = {}


def register_connection(database_id: str, connection_string: str) -> None:
    """Temporary helper for local testing until real credential storage exists."""
    _CONNECTION_REGISTRY[database_id] = connection_string


@contextmanager
def get_connection(database_id: str):
    connection_string = _CONNECTION_REGISTRY.get(database_id)
    if not connection_string:
        raise ValueError(f"No connection registered for database_id='{database_id}'")

    engine = create_engine(connection_string)
    # Layer 2 of read-only enforcement: even if the DB user somehow has
    # write access, this puts the connection itself into read-only mode.
    connection = engine.connect().execution_options(postgresql_readonly=True)
    try:
        yield connection
    finally:
        connection.close()
        engine.dispose()