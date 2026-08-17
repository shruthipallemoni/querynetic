"""
HTTP endpoint that the React frontend calls to ask a question.

Job: load this conversation's real message history from the database,
run the pipeline with it as context, then persist both the question and
the answer as new Message rows.

This REPLACES relying on the graph's in-memory checkpointer for cross-
request memory — that was flagged early on as fragile (lost on restart,
doesn't work across multiple server processes). Reconstructing history
from a real database table on every request fixes that, and it's the
same table the conversation history sidebar reads from — one source of
truth for both jobs.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import analyst_graph
from app.core.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    conversation_id: int


def _load_history(conversation_id: int, db: Session) -> list:
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    history = []
    for row in rows:
        if row.role == "user":
            history.append(HumanMessage(content=row.content))
        elif row.role == "assistant":
            history.append(AIMessage(content=row.content))
        # "error" rows are intentionally excluded from context — a failed
        # attempt shouldn't shape how the model interprets later questions.
    return history


@router.post("/")
def ask_question(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    history = _load_history(conversation.id, db)

    turn_input = {
        "question": payload.question,
        "database_id": conversation.database_id,
        "messages": history + [HumanMessage(content=payload.question)],
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
        config={"configurable": {"thread_id": f"conversation-{conversation.id}"}},
    )

    # Persist the user's question.
    db.add(Message(conversation_id=conversation.id, role="user", content=payload.question))

    # First message in a new conversation becomes its title — same pattern
    # as ChatGPT-style history sidebars, so nothing needs manual naming.
    if conversation.title == "New conversation":
        conversation.title = payload.question[:60]

    if result.get("error"):
        db.add(Message(conversation_id=conversation.id, role="error", content=result["error"]))
    else:
        db.add(Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.get("final_answer", ""),
            queries=result.get("generated_queries", []),
            validated=result.get("validation_result", {}).get("is_valid", False),
        ))

    db.commit()

    return {
        "answer": result.get("final_answer"),
        "error": result.get("error"),
        "queries": result.get("generated_queries", []),
        "validated": result.get("validation_result", {}).get("is_valid", False),
    }