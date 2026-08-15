"""
SQL Generation Agent

Job: given the Planner's sub-questions and the Schema Retrieval agent's
relevant tables, write ONE SQL query per sub-question.

Design choice: even for "comparison" or "trend" plans, this agent writes
several SIMPLE queries rather than one complex query with nested joins/
subqueries. Simple queries are easier to validate, execute, and repair
independently — the actual comparing happens later, in Summarization.

This agent trusts nothing it writes. Its output always passes through
SQL Validation next; it never executes anything itself.
"""

import json
from groq import Groq
from app.core.config import settings
from app.core.llm_utils import parse_json_response
from app.agents.state import AnalystState

client = Groq(api_key=settings.LLM_API_KEY)

SQL_GENERATION_SYSTEM_PROMPT = """You are the SQL generation stage of a data
analyst AI. You will be given a single sub-question and a list of relevant
tables (with descriptions and columns).

Write ONE safe, read-only SQL query (SELECT only) that answers the
sub-question, using ONLY the tables and columns provided. Do not invent
table or column names that weren't given to you.

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


def generate_sql(state: AnalystState) -> AnalystState:
    plan = state.get("plan")
    retrieved_schema = state.get("retrieved_schema")

    if not plan or not retrieved_schema:
        state["error"] = "SQL Generation requires a plan and retrieved schema first."
        return state

    sub_questions = plan.get("sub_questions", [])
    if not sub_questions:
        state["error"] = "Planner produced no sub-questions to generate SQL for."
        return state

    schema_context = _format_schema_context(retrieved_schema)
    generated_queries = []

    for sub_question in sub_questions:
        user_prompt = f"Relevant tables:\n{schema_context}\n\nSub-question: {sub_question}"

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SQL_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            sql_data = parse_json_response(response.choices[0].message.content)
            sql = sql_data.get("sql", "")

        except json.JSONDecodeError:
            state["error"] = f"SQL Generation returned invalid JSON for: '{sub_question}'"
            return state
        except Exception as e:
            state["error"] = f"SQL Generation failed for '{sub_question}': {str(e)}"
            return state

        generated_queries.append({"sub_question": sub_question, "sql": sql})

    state["generated_queries"] = generated_queries
    return state