"""
Result Summarization Agent

Job: turn potentially large raw query results into a short, meaningful
summary BEFORE any of it reaches the LLM, then use that summary to write
the final plain-English answer.

This agent has two distinct halves, and they use different tools on purpose:

  1. Statistics (row counts, sums, averages) are computed in plain Python.
     No LLM involved — arithmetic should never depend on a model getting
     the math right.
  2. The final natural-language answer is written by the LLM, using ONLY
     the already-correct summary from step 1 — never the raw rows.

Unlike every earlier agent, this one's final output is free text, not JSON.
Nothing downstream parses final_answer programmatically — a human reads it
directly, so plain prose is the right shape here.
"""

from groq import Groq
from langchain_core.messages import AIMessage
from app.core.config import settings
from app.agents.state import AnalystState

client = Groq(api_key=settings.LLM_API_KEY)

SAMPLE_SIZE = 5  # small preview of raw rows included alongside the stats

FINAL_ANSWER_SYSTEM_PROMPT = """You are the final-answer stage of a data
analyst AI. You will be given the user's original question and a condensed
statistical summary of query results (never raw data). Write a clear,
concise, plain-English answer using ONLY the numbers provided in the
summary. Do not invent figures that aren't present in the summary."""


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _summarize_rows(rows: list) -> dict:
    row_count = len(rows)
    column_stats = {}

    if rows:
        columns = rows[0].keys()
        for col in columns:
            values = [r[col] for r in rows if _is_numeric(r.get(col))]
            if values:
                column_stats[col] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "sum": sum(values),
                }

    return {
        "row_count": row_count,
        "column_stats": column_stats,
        "sample_rows": rows[:SAMPLE_SIZE],
    }


def summarize_results(state: AnalystState) -> AnalystState:
    execution_result = state.get("execution_result")

    if not execution_result:
        state["error"] = "Summarization requires execution_result first."
        return state

    # Step 1: pure Python computation. Numbers come from real arithmetic,
    # not from a model guessing at them.
    summaries = []
    for entry in execution_result:
        stats = _summarize_rows(entry["rows"])
        summaries.append({"sub_question": entry["sub_question"], **stats})

    state["summary"] = summaries

    # Step 2: hand ONLY the condensed summary (never raw rows) to the LLM,
    # to turn correct numbers into a plain-English answer.
    user_prompt = (
        f"Original question: {state['question']}\n\n"
        f"Summarized results:\n{summaries}"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": FINAL_ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            # Slightly above 0 here, unlike Planner/SQL Generation — this
            # stage is writing prose, not producing something another
            # agent must parse exactly, so a little natural variation is fine.
            temperature=0.3,
        )
        state["final_answer"] = response.choices[0].message.content
        # This gets MERGED into history by the add_messages reducer, not
        # overwritten — so the next question in this conversation will see
        # this answer as prior context.
        state["messages"] = [AIMessage(content=state["final_answer"])]

    except Exception as e:
        state["error"] = f"Final answer generation failed: {str(e)}"
        return state

    return state