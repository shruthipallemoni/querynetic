"""
Shared helpers for parsing structured (JSON) output from LLM calls.

Used by every agent that asks the model for JSON (Planner, SQL Generation,
Repair). Kept here, not duplicated three times, so a fix here fixes all
three agents at once.
"""

import json


def parse_json_response(raw_output: str) -> dict:
    """
    Parses a model's JSON response, tolerating the most common way models
    break "respond with ONLY JSON" instructions: wrapping the answer in a
    markdown code fence like ```json ... ```.

    Always pair this with response_format={"type": "json_object"} in the
    API call itself — that's the real enforcement; this is a second,
    independent safety net (same defense-in-depth pattern used elsewhere
    in this codebase) in case a model still adds stray formatting.
    """
    cleaned = raw_output.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    return json.loads(cleaned)