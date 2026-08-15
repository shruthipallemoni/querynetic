"""
HTTP endpoint(s) that the React frontend calls.

Job: receive a question, pass it into the agent pipeline (graph.py), and
return the final answer. This file should be thin — it translates between
"HTTP request" and "pipeline input," nothing more.

IMPORTANT: this is where per-turn state resetting happens. The checkpointer
persists the ENTIRE state between calls, not just conversation history —
so every field except `messages` must be explicitly reset here on each new
question. Otherwise leftover data from a previous, unrelated question
(a stale retry_count, an old validation_result) could silently affect the
new one.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.graph import analyst_graph
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    database_id: str
    thread_id: str


@router.post("/")
def ask_question(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    question = payload.question
    database_id = payload.database_id
    thread_id = payload.thread_id
    # thread_id identifies the CONVERSATION — the same value across
    # multiple questions is what lets the checkpointer load prior history.
    config = {"configurable": {"thread_id": thread_id}}

    turn_input = {
        "question": question,
        "database_id": database_id,
        # Only new item passed for `messages` — the add_messages reducer
        # merges this into whatever history the checkpointer already has,
        # it does NOT replace it.
        "messages": [HumanMessage(content=question)],
        # Everything else below has no reducer, so passing fresh values
        # here overwrites any leftover data from the previous question.
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

    result = analyst_graph.invoke(turn_input, config=config)

    return {
        "answer": result.get("final_answer"),
        "error": result.get("error"),
        "queries": result.get("generated_queries", []),
        "validated": result.get("validation_result", {}).get("is_valid", False),
    }