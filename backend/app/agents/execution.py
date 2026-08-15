"""
Execution Agent

Job: run the validated, safe SQL query against the user's connected
database — using a READ-ONLY connection only.

This agent REFUSES to run anything that wasn't explicitly marked safe by
SQL Validation. Never call the database driver from anywhere else in the
codebase — this is the only agent allowed to touch db_connectors/.
"""

from decimal import Decimal
from sqlalchemy import text
from app.db_connectors.postgres_connector import get_connection
from app.agents.state import AnalystState

# Hard cap on rows returned, independent of whatever the query itself asks
# for. Even a validated, safe query could return millions of rows — this
# is the enforcement point for "never send unbounded results downstream."
ROW_LIMIT = 1000


def _normalize_row(row: dict) -> dict:
    # Postgres returns SUM()/aggregate results as Decimal, not float — and
    # Decimal is neither `int` nor `float`, so downstream code that checks
    # for numeric types (see summarization.py's _is_numeric) silently
    # ignores it. Converting here, once, at the boundary where data leaves
    # the database, means nothing downstream has to know Postgres uses
    # this type at all.
    return {
        key: float(value) if isinstance(value, Decimal) else value
        for key, value in row.items()
    }


def execute_sql(state: AnalystState) -> AnalystState:
    validation_result = state.get("validation_result")
    generated_queries = state.get("generated_queries", [])
    database_id = state.get("database_id")

    # Guard clause: this agent will not run anything that wasn't explicitly
    # marked safe. This check existing here — not just relying on the graph's
    # wiring — is itself a defense-in-depth layer.
    if not validation_result or not validation_result.get("is_valid"):
        state["error"] = "Execution refused: queries have not passed validation."
        return state

    results = []
    try:
        with get_connection(database_id) as conn:
            for entry in generated_queries:
                sql = entry["sql"].rstrip(";")
                # Wrapping as a subquery (rather than naively appending
                # "LIMIT N") works no matter what the inner query already
                # contains — including its own LIMIT or ORDER BY clause,
                # which appending would have produced invalid SQL for.
                capped_sql = f"SELECT * FROM ({sql}) AS capped_query LIMIT {ROW_LIMIT}"
                rows = conn.execute(text(capped_sql)).mappings().all()
                results.append({
                    "sub_question": entry["sub_question"],
                    "rows": [_normalize_row(dict(row)) for row in rows],
                })
    except Exception as e:
        state["error"] = f"Execution failed: {str(e)}"
        return state

    state["execution_result"] = results
    return state