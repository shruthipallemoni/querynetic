"""
Observability wrapper for pipeline agents.

Job: measure latency and log success/failure for each pipeline stage,
WITHOUT modifying any agent's own code. This wraps around agents at
registration time (see graph.py) — same "wiring vs logic" separation used
everywhere else in this codebase.

For now this logs structured JSON lines to stdout. In production, this is
the exact seam where you'd swap in OpenTelemetry or ship these to a real
log aggregator — the agents themselves would never need to change.
"""

import time
import json
import logging

logger = logging.getLogger("querynetic.pipeline")
logging.basicConfig(level=logging.INFO)


def observe(stage_name: str):
    """Decorator factory — observe("planner") returns a decorator for that stage."""

    def decorator(agent_fn):
        def wrapped(state: dict) -> dict:
            had_error_before = state.get("error") is not None
            start = time.perf_counter()

            result_state = agent_fn(state)

            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            has_error_now = result_state.get("error") is not None

            # Only blame THIS stage if the error is NEW — an error from an
            # earlier stage shouldn't be re-attributed to a later stage
            # that just passed the state through unchanged.
            failed_here = has_error_now and not had_error_before

            log_entry = {
                "stage": stage_name,
                "latency_ms": latency_ms,
                "success": not failed_here,
                "retry_count": result_state.get("retry_count", 0),
                "error": result_state.get("error") if failed_here else None,
            }
            logger.info(json.dumps(log_entry))

            return result_state

        return wrapped

    return decorator