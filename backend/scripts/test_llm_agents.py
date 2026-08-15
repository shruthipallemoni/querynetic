"""
Manual smoke test for Planner + SQL Generation — the two agents that need
ONLY a Groq API key. No database, no vector store required.

Schema Retrieval is deliberately skipped and replaced with a hand-written
fake schema below. This isolates "does the LLM produce good SQL given
clean schema info" from "does vector search find the right tables" — two
different things worth verifying separately, not one bundled test.

Run from backend/, with GROQ_API_KEY set in your .env:
    python -m scripts.test_llm_agents
"""

import json
from langchain_core.messages import HumanMessage
from app.agents.planner import plan
from app.agents.sql_generation import generate_sql

# Hand-written, standing in for what Schema Retrieval would normally find.
FAKE_SCHEMA = [
    {
        "table_name": "orders",
        "description": "stores each customer purchase, including amount and region",
        "columns": "id, customer_id, amount, region, created_at",
    },
    {
        "table_name": "customers",
        "description": "stores customer names and signup dates",
        "columns": "id, name, signup_date",
    },
]

question = "Compare total revenue between Europe and North America"

state = {
    "question": question,
    # Planner reads FROM messages now, not from `question` directly — this
    # has to be here, matching exactly what chat.py does on every real
    # request. Without it, Planner sees no actual question at all.
    "messages": [HumanMessage(content=question)],
}

print("Calling Planner...")
state = plan(state)
print(json.dumps(state.get("plan"), indent=2))

if state.get("error"):
    print("Planner error:", state["error"])
    raise SystemExit(1)

state["retrieved_schema"] = FAKE_SCHEMA

print("\nCalling SQL Generation...")
state = generate_sql(state)
print(json.dumps(state.get("generated_queries"), indent=2))

if state.get("error"):
    print("SQL Generation error:", state["error"])