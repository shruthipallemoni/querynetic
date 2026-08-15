"""
Schema Retrieval Agent

Job: given the user's question, find ONLY the tables/columns relevant to it,
using embeddings + vector search — never send the user's full database
schema to the LLM.

Depends on a one-time "ingestion" step (not built yet) that, when a user
connects a database, generates a short description for each table and
stores it in Chroma under a collection named f"schema_{database_id}".
This agent only ever READS from that collection.
"""

import chromadb
from chromadb.utils import embedding_functions
from app.agents.state import AnalystState

CHROMA_PATH = "./chroma_data"
TOP_K = 5  # how many closest-matching tables to retrieve

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# A small, fast embedding model on purpose — keeps memory usage low enough
# to run comfortably on constrained hosting (e.g. free-tier deployments).
embedding_fn = embedding_functions.DefaultEmbeddingFunction()


def retrieve_schema(state: AnalystState) -> AnalystState:
    question = state["question"]
    database_id = state.get("database_id")

    if not database_id:
        state["error"] = "No database_id set — cannot look up schema."
        return state

    try:
        collection = chroma_client.get_collection(
            name=f"schema_{database_id}",
            embedding_function=embedding_fn,
        )
    except Exception:
        state["error"] = (
            f"No schema index found for database '{database_id}'. "
            "Run schema ingestion for this database first."
        )
        return state

    results = collection.query(query_texts=[question], n_results=TOP_K)

    # Chroma returns parallel lists (documents, metadatas) for the single
    # query we sent — [0] because we only queried one question at a time.
    retrieved = [
        {"description": doc, **metadata}
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0])
    ]

    if not retrieved:
        state["error"] = "No relevant tables found for this question."
        return state

    state["retrieved_schema"] = retrieved
    return state