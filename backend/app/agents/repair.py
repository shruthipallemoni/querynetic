"""
SQL Repair Agent

Job: given SQL that FAILED validation, and the specific reasons it failed,
attempt a targeted fix — not a full rewrite from scratch. Only the queries
that actually failed get touched; queries that already passed are left alone.

This agent does not decide whether to retry again or give up — that
decision lives in the graph's conditional routing (graph.py), based on
retry_count. This agent's only job is: given known errors, try to fix them.
"""

import json
from groq import Groq
from app.core.config import settings
from app.core.llm_utils import parse_json_response
from app.agents.state import AnalystState

client = Groq(api_key=settings.LLM_API_KEY)

REPAIR_SYSTEM_PROMPT = """You are the SQL repair stage of a data analyst AI.
You will be given a sub-question, a SQL query that failed validation, and
the specific reasons it failed. Fix ONLY what's necessary to resolve those
specific errors, using ONLY the tables and columns provided in context.

Respond with ONLY valid JSON in this exact shape, nothing else:
{"sql": "..."}
"""


def _format_schema_context(retrieved_schema: list) -> str:
    lines = []
    for table in retrieved_schema:
        name = table.get("table_name", "unknown_table")
        description = table.get("description", "")
        columns = table.get("columns", "")
        lines.append(f"- {name}: {description} (columns: {columns})")
    return "\n".join(lines)


def repair_sql(state: AnalystState) -> AnalystState:
    validation_result = state.get("validation_result")
    retrieved_schema = state.get("retrieved_schema", [])
    generated_queries = state.get("generated_queries", [])

    if not validation_result:
        state["error"] = "SQL Repair requires a validation_result first."
        return state

    schema_context = _format_schema_context(retrieved_schema)
    query_lookup = {q["sub_question"]: q for q in generated_queries}

    for result in validation_result["results"]:
        if result["is_valid"]:
            continue  # already passed — leave it alone, only fix real failures

        sub_question = result["sub_question"]
        user_prompt = (
            f"Relevant tables:\n{schema_context}\n\n"
            f"Sub-question: {sub_question}\n"
            f"Failed SQL: {result['sql']}\n"
            f"Validation errors: {'; '.join(result['errors'])}"
        )

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": REPAIR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            sql_data = parse_json_response(response.choices[0].message.content)
            fixed_sql = sql_data.get("sql", "")

        except json.JSONDecodeError:
            state["error"] = f"SQL Repair returned invalid JSON for: '{sub_question}'"
            return state
        except Exception as e:
            state["error"] = f"SQL Repair failed for '{sub_question}': {str(e)}"
            return state

        if sub_question in query_lookup:
            query_lookup[sub_question]["sql"] = fixed_sql

    state["generated_queries"] = list(query_lookup.values())
    state["retry_count"] = state.get("retry_count", 0) + 1
    return state