"""
Planner Agent

Job: look at the user's question (plus recent conversation history) and
decide WHAT needs to happen — e.g. "this is one query" vs "this needs two
queries compared against each other" — before any SQL gets written.

This agent does NOT write SQL and does NOT touch the database. Keeping
planning separate from execution means a misunderstood question fails
loudly at the planning stage, instead of silently producing wrong SQL.

Output is forced into a fixed JSON shape (structured output) so downstream
agents can act on it directly instead of re-interpreting free text.
"""

import json
from groq import Groq
from app.core.config import settings
from app.core.llm_utils import parse_json_response
from app.agents.state import AnalystState

client = Groq(api_key=settings.LLM_API_KEY)

PLANNER_SYSTEM_PROMPT = """You are the planning stage of a data analyst AI.
Given a user's question and recent conversation context, decide how to break
it into one or more concrete sub-questions that can each be answered by a
single SQL query later in the pipeline.

Respond with ONLY valid JSON in this exact shape, nothing else:

{
  "query_type": "single" | "comparison" | "trend",
  "sub_questions": ["..."],
  "needs_clarification": true | false,
  "clarification_question": "..." | null
}

Rules:
- Use "single" for one straightforward question.
- Use "comparison" when the user wants two or more things measured against
  each other (e.g. "compare Q1 to Q2").
- Use "trend" when the user wants a value over time (e.g. "monthly revenue
  this year").
- sub_questions MUST be phrased in plain English, exactly like a person
  would ask them (e.g. "What is total revenue in Europe?"). NEVER write
  SQL syntax (no SELECT, FROM, WHERE) in a sub_question.
- You do NOT have access to the database schema at this stage — do not
  guess or invent table or column names anywhere in your response.
- If the question is too vague to plan confidently, set needs_clarification
  to true and provide a specific clarification_question. In that case,
  sub_questions can be an empty list.
"""


def _to_groq_messages(history: list) -> list:
    # History arrives as LangChain message objects (HumanMessage/AIMessage),
    # each with a .type ("human"/"ai"). Groq's API expects plain dicts with
    # "role"/"content" instead — this converts between the two shapes.
    role_map = {"human": "user", "ai": "assistant"}
    return [
        {"role": role_map.get(m.type, "user"), "content": m.content}
        for m in history
    ]


def plan(state: AnalystState) -> AnalystState:
    history = state.get("messages", [])

    messages = [{"role": "system", "content": PLANNER_SYSTEM_PROMPT}]
    messages += _to_groq_messages(history)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0,  # planning should be deterministic, not creative
            response_format={"type": "json_object"},  # enforced, not just requested
        )
        raw_output = response.choices[0].message.content
        plan_data = parse_json_response(raw_output)

    except json.JSONDecodeError:
        # The model didn't return valid JSON — fail loudly and let the graph
        # route to an error/clarification response instead of guessing.
        state["error"] = "Planner failed to produce valid structured output."
        return state

    except Exception as e:
        state["error"] = f"Planner agent failed: {str(e)}"
        return state

    state["plan"] = plan_data
    return state