"""
The shared "data packet" (state) that flows through every agent in the pipeline.

This is the most important file in the whole backend. Every agent reads from
this state and writes back to it — it's how a Planner agent's output becomes
a Schema Retrieval agent's input, and so on down the line.

Design rules encoded in this file (don't violate these when writing agents):

1. `execution_result` (raw DB rows) and `summary` (condensed, LLM-safe version)
   are kept as SEPARATE fields on purpose. Only `summary` should ever be used
   when building a prompt for the final answer. This is the field-level
   enforcement of "never send raw rows to the LLM."

2. `retrieved_schema` should only ever contain the tables/columns relevant to
   the current question — never the full database schema.

3. `retry_count` exists to cap the SQL repair loop. Always check it before
   looping back to SQL Generation, to avoid an infinite retry cycle.
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AnalystState(TypedDict, total=False):
    # --- Input (set once, never modified downstream) ---
    question: str
    database_id: str  # which connected database this question targets
    # Conversation history. The Annotated[...] + add_messages reducer means
    # new messages returned by any agent get APPENDED to existing history,
    # not overwritten — this is the only field in this whole state that
    # should accumulate across turns rather than reset each time.
    messages: Annotated[List[BaseMessage], add_messages]

    # --- Planner output ---
    plan: Dict[str, Any]

    # --- Schema Retrieval output ---
    retrieved_schema: List[Dict[str, Any]]

    # --- SQL Generation output (one query per sub-question from the plan) ---
    generated_queries: List[Dict[str, str]]  # [{"sub_question": ..., "sql": ...}]

    # --- SQL Validation / Firewall output ---
    validation_result: Dict[str, Any]  # {"is_valid": bool, "errors": [...]}
    retry_count: int

    # --- Execution output (temporary — do not forward to the LLM) ---
    execution_result: List[Dict[str, Any]]

    # --- Summarization output (this is what the LLM sees) ---
    summary: Dict[str, Any]

    # --- Final output shown to the user ---
    final_answer: str

    # --- Error tracking (used by any agent, read by observability/logging) ---
    error: Optional[str]