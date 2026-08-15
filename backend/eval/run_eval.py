"""
Lightweight evaluation harness.

Runs every test case in dataset.py through the real pipeline and reports
aggregate reliability metrics — NOT a claim about factual correctness of
the answers themselves (see dataset.py's docstring for that distinction).

Run with:  python -m eval.run_eval
"""

import time
import json
from app.graph import analyst_graph
from eval.dataset import TEST_CASES
from scripts.seed_test_schema import seed_test_db

# Must run in the SAME process as analyst_graph.invoke() below — the
# connection registry lives in memory and doesn't survive across separate
# script runs. See seed_test_schema.py's docstring for why.
seed_test_db()


def _fresh_turn_input(case: dict) -> dict:
    # Same reset pattern used in api/chat.py — every eval run starts clean,
    # no leftover state from a previous test case.
    return {
        "question": case["question"],
        "database_id": case["database_id"],
        "messages": [],
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


def run_eval() -> dict:
    results = []

    for case in TEST_CASES:
        config = {"configurable": {"thread_id": f"eval-{case['id']}"}}
        start = time.perf_counter()

        output = analyst_graph.invoke(_fresh_turn_input(case), config=config)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        succeeded = output.get("error") is None and bool(output.get("final_answer"))

        results.append({
            "id": case["id"],
            "question": case["question"],
            "succeeded": succeeded,
            "needed_repair": output.get("retry_count", 0) > 0,
            "retry_count": output.get("retry_count", 0),
            "latency_ms": latency_ms,
            "error": output.get("error"),
        })

    total = len(results)
    success_count = sum(r["succeeded"] for r in results)
    repair_count = sum(r["needed_repair"] for r in results)

    return {
        "total_cases": total,
        "success_rate": round(success_count / total, 3) if total else 0,
        "repair_trigger_rate": round(repair_count / total, 3) if total else 0,
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / total, 2) if total else 0,
        "results": results,
    }


if __name__ == "__main__":
    report = run_eval()
    print(json.dumps(report, indent=2))