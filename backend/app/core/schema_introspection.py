"""
Reads a database's REAL structure automatically — table names and columns —
instead of a human hand-writing descriptions (which is what we did for
test_db, as a placeholder, throughout early development).

This is what makes "connect your own database" actually work for a
database Querynetic has never seen before: it asks the database itself
what it contains, then feeds that into the same Chroma-based retrieval
Schema Retrieval already relies on. No agent code changes — this just
populates the data Schema Retrieval expects to find.
"""

from sqlalchemy import create_engine, inspect
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "./chroma_data"


def introspect_and_index_schema(database_id: str, connection_string: str) -> int:
    """
    Connects to the given database, reads its real table/column structure,
    and indexes it into Chroma under schema_{database_id}. Returns the
    number of tables indexed.
    """
    engine = create_engine(connection_string)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if not table_names:
        raise ValueError("No tables found in this database.")

    ids, documents, metadatas = [], [], []

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        column_names = ", ".join(col["name"] for col in columns)

        ids.append(table_name)
        documents.append(f"{table_name} table with columns: {column_names}")
        metadatas.append({"table_name": table_name, "columns": column_names})

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    collection = chroma_client.get_or_create_collection(
        name=f"schema_{database_id}",
        embedding_function=embedding_fn,
    )
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    engine.dispose()
    return len(table_names)