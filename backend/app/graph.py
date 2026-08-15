"""
Wires all agents together into a single LangGraph pipeline.

This file is deliberately "dumb" — it defines the ORDER agents run in and
how state flows between them. All actual thinking happens inside each
agent's own file (agents/*.py). Nothing here should contain business logic.

Currently wired: Planner only. More agents get added as nodes, one at a
time, as we build them — the graph structure grows, but this pattern stays
the same for every new agent we add.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AnalystState
from app.agents.planner import plan
from app.agents.schema_retrieval import retrieve_schema
from app.agents.sql_generation import generate_sql
from app.agents.sql_validation import validate_sql
from app.agents.repair import repair_sql
from app.agents.execution import execute_sql
from app.agents.summarization import summarize_results
from app.core.observability import observe

MAX_REPAIR_ATTEMPTS = 2


def route_after_validation(state: AnalystState) -> str:
    """
    Conditional routing function — this is the graph's if/else.

    Reads state (does NOT modify it) and returns a label. The graph looks
    up that label in the mapping passed to add_conditional_edges to decide
    which node runs next.
    """
    validation_result = state.get("validation_result", {})

    if validation_result.get("is_valid"):
        return "success"

    if state.get("retry_count", 0) >= MAX_REPAIR_ATTEMPTS:
        return "give_up"

    return "repair"


def route_after_execution(state: AnalystState) -> str:
    # If Execution already set an error, stop here — proceeding into
    # Summarization would let its own guard clause overwrite Execution's
    # specific error message with a vague, less useful one.
    if state.get("error"):
        return "failed"
    return "success"


def build_graph():
    graph = StateGraph(AnalystState)

    # Every node is wrapped with observe(name) here, at registration —
    # this is the ONLY place logging gets added. No agent file above was
    # touched to make this happen.
    graph.add_node("planner", observe("planner")(plan))
    graph.add_node("schema_retrieval", observe("schema_retrieval")(retrieve_schema))
    graph.add_node("sql_generation", observe("sql_generation")(generate_sql))
    graph.add_node("sql_validation", observe("sql_validation")(validate_sql))
    graph.add_node("repair", observe("repair")(repair_sql))
    graph.add_node("execution", observe("execution")(execute_sql))
    graph.add_node("summarization", observe("summarization")(summarize_results))

    graph.set_entry_point("planner")

    graph.add_edge("planner", "schema_retrieval")
    graph.add_edge("schema_retrieval", "sql_generation")
    graph.add_edge("sql_generation", "sql_validation")

    # The fork: after validation, where we go next depends on the outcome.
    #   "success"  -> only validated SQL is allowed to reach Execution
    #   "repair"   -> fix only the failed queries, then re-validate
    #   "give_up"  -> retries exhausted, stop (END for now — later this
    #                 should route to a clear "couldn't answer" response)
    graph.add_conditional_edges(
        "sql_validation",
        route_after_validation,
        {
            "success": "execution",
            "repair": "repair",
            "give_up": END,
        },
    )

    # This is the loop: repair sends the fixed queries back through
    # validation again, rather than trusting itself blindly.
    graph.add_edge("repair", "sql_validation")

    # Once Summarization exists, this becomes:
    #   graph.add_edge("execution", "summarization")
    graph.add_conditional_edges(
        "execution",
        route_after_execution,
        {
            "success": "summarization",
            "failed": END,
        },
    )
    graph.add_edge("summarization", END)

    # MemorySaver keeps state in this process's memory only — it's lost on
    # restart, and won't work if you run multiple server instances. That's
    # fine for local development and demos. In production this line becomes
    # a PostgresSaver instead, so conversation history survives restarts
    # and works across multiple servers — same interface, different backend.
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Compiled once at import time, reused across requests.
analyst_graph = build_graph()