"""
Full end-to-end smoke test: runs a real question through the ENTIRE graph
— Planner, Schema Retrieval, SQL Generation, Validation, Repair (if
needed), Execution, and Summarization — against the real local Postgres
database seeded by seed_data.sql / seed_test_schema.py.

Bypasses HTTP and auth entirely on purpose: this isolates "does the
pipeline itself work" from "does the API layer around it work" — the same
one-thing-at-a-time testing principle used throughout this project.

Run from backend/, AFTER seed_data.sql and seed_test_schema.py:
    python -m scripts.smoke_test
"""

import json
from langchain_core.messages import HumanMessage
from app.graph import analyst_graph
from scripts.seed_test_schema import seed_test_db

# Must run in the SAME process as analyst_graph.invoke() below — the
# connection registry lives in memory and doesn't survive across separate
# script runs. See seed_test_schema.py's docstring for why.
seed_test_db()

question = "Compare total revenue between Europe and North America"

turn_input = {
    "question": question,
    "database_id": "test_db",
    "messages": [HumanMessage(content=question)],
    "plan": {},
    "retrieved_schema": [],
    "generated_queries": [],
    "validation_result": {},
    "retry_count": 0,
    "execution_result": [],
    "summary": [],
    "final_answer": "",
    "error": None,
}

result = analyst_graph.invoke(
    turn_input,
    config={"configurable": {"thread_id": "smoke-test-1"}},
)

print("=" * 60)
print("FINAL ANSWER:")
print(result.get("final_answer"))
print("=" * 60)
print("Error:", result.get("error"))
print("Retry count:", result.get("retry_count"))
print("Tables retrieved:", [t["table_name"] for t in result.get("retrieved_schema", [])])
print("Validation passed:", result.get("validation_result", {}).get("is_valid"))
print("=" * 60)
print("DEBUG — generated_queries:")
print(json.dumps(result.get("generated_queries"), indent=2))
print("DEBUG — execution_result (raw rows):")
print(json.dumps(result.get("execution_result"), indent=2))
print("DEBUG — summary (computed stats):")
print(json.dumps(result.get("summary"), indent=2))