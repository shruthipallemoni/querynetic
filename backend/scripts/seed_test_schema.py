"""
One-off manual script: seeds a Chroma collection with descriptions of the
test tables created by seed_data.sql, and registers the connection string
for database_id="test_db".

This stands in for the real "schema ingestion" step, which would normally
run automatically when a user connects a database in the product — not
built yet. Run this once before the full pipeline smoke test.

Run from backend/, AFTER seed_data.sql has been applied to Postgres:
    python -m scripts.seed_test_schema
"""

import chromadb
from chromadb.utils import embedding_functions
from app.db_connectors.postgres_connector import register_connection

CHROMA_PATH = "./chroma_data"
DATABASE_ID = "test_db"


def seed_test_db():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    collection = chroma_client.get_or_create_collection(
        name=f"schema_{DATABASE_ID}",
        embedding_function=embedding_fn,
    )

    collection.upsert(
        ids=["orders", "customers"],
        documents=[
            "orders table: stores each customer purchase, including amount, region, and date",
            "customers table: stores customer names and signup dates",
        ],
        metadatas=[
            {"table_name": "orders", "columns": "id, customer_id, amount, region, created_at"},
            {"table_name": "customers", "columns": "id, name, signup_date"},
        ],
    )

    # NOTE: using the postgres superuser here for local testing convenience
    # only. Real usage should connect through a dedicated READ-ONLY database
    # role — see the security notes in README.md. This is a TODO for when
    # real credential storage (encrypted, per-user) gets built.
    register_connection(
        DATABASE_ID,
        "postgresql://postgres:postgres@localhost:5432/test_db",
    )

    print(f"Seeded schema for '{DATABASE_ID}' and registered its connection.")


if __name__ == "__main__":
    seed_test_db()