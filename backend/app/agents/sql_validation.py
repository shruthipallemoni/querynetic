"""
SQL Validation / Firewall Agent

Job: this is the safety gate. Before any query touches a real database, it
must pass through here. Nothing skips this step, ever.

Design principle: DEFENSE IN DEPTH. No single check here is trusted to be
perfect on its own — several independent checks are layered together, so a
blind spot in one is still caught by another.

Checks performed, each independent of the others:
1. Forbidden keyword scan   — catches obviously destructive operations
2. Single-statement check   — blocks statement-chaining / injection tricks
3. SELECT-only check        — confirms the query's actual type via a parser
4. Table allowlist check    — query may ONLY touch tables Schema Retrieval
                               already said were relevant to this question

If validation fails, this agent does NOT retry or fix anything — it just
reports what's wrong. The Repair Agent (next in the pipeline) decides what
to do with that information.
"""

import re
import sqlparse
from app.agents.state import AnalystState

# Layer 1: blunt-force keyword blocklist. Independent of the parser-based
# checks below — if the parser has a bug or an edge case, this still catches
# destructive operations by keyword alone.
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "ALTER", "TRUNCATE", "INSERT",
    "GRANT", "REVOKE", "CREATE", "REPLACE", "ATTACH", "PRAGMA",
    "EXEC", "EXECUTE", "MERGE",
]


def _contains_forbidden_keyword(sql: str):
    upper_sql = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            return keyword
    return None


def _is_single_statement(sql: str) -> bool:
    # sqlparse splits text on semicolons into separate statement objects.
    # More than one non-empty statement means chaining was attempted.
    statements = [s for s in sqlparse.parse(sql) if s.token_first(skip_cm=True)]
    return len(statements) == 1


def _is_select_only(sql: str) -> bool:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False
    return parsed[0].get_type() == "SELECT"


def _extract_table_names(sql: str) -> set:
    # Walks the token stream and grabs whatever immediately follows FROM/JOIN.
    # Simple on purpose — this only needs to be reliable enough to compare
    # against the allowlist, not a full SQL analyzer.
    parsed = sqlparse.parse(sql)[0]
    tokens = list(parsed.flatten())
    tables = set()

    for i, token in enumerate(tokens):
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ("FROM", "JOIN"):
            for next_token in tokens[i + 1:]:
                if next_token.is_whitespace:
                    continue
                if next_token.value == "(":
                    # This FROM/JOIN introduces a subquery, not a direct
                    # table reference — e.g. "JOIN (SELECT ...) t". The
                    # subquery's OWN internal FROM/JOIN tokens still get
                    # picked up normally later in this same loop, since
                    # flatten() includes them too. We just skip treating
                    # "(" itself as a fake table name.
                    break
                tables.add(next_token.value.strip('`"[]').lower())
                break
    return tables


def validate_sql(state: AnalystState) -> AnalystState:
    generated_queries = state.get("generated_queries")
    retrieved_schema = state.get("retrieved_schema", [])

    if not generated_queries:
        state["error"] = "SQL Validation requires generated_queries first."
        return state

    allowed_tables = {t.get("table_name", "").lower() for t in retrieved_schema}

    results = []
    overall_valid = True

    for entry in generated_queries:
        sql = entry["sql"]
        errors = []

        forbidden = _contains_forbidden_keyword(sql)
        if forbidden:
            errors.append(f"Contains forbidden operation: {forbidden}")

        if not _is_single_statement(sql):
            errors.append("Multiple SQL statements detected — only one is allowed.")

        if not _is_select_only(sql):
            errors.append("Only SELECT queries are allowed.")

        used_tables = _extract_table_names(sql)
        unauthorized = used_tables - allowed_tables
        if unauthorized:
            errors.append(f"References unauthorized table(s): {', '.join(unauthorized)}")

        is_valid = len(errors) == 0
        overall_valid = overall_valid and is_valid

        results.append({
            "sub_question": entry["sub_question"],
            "sql": sql,
            "is_valid": is_valid,
            "errors": errors,
        })

    state["validation_result"] = {"is_valid": overall_valid, "results": results}
    return state