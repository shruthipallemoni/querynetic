"""
Fast, dependency-free tests for the SQL firewall — no LLM, no database
needed. This is the cheapest possible way to prove the firewall actually
blocks what it claims to block, rather than just trusting that it does.
"""

from app.agents.sql_validation import validate_sql


def _fake_state(sql: str, allowed_tables=("orders",)):
    return {
        "generated_queries": [{"sub_question": "test", "sql": sql}],
        "retrieved_schema": [{"table_name": t} for t in allowed_tables],
    }


def test_blocks_drop_table():
    state = validate_sql(_fake_state("DROP TABLE orders;"))
    assert state["validation_result"]["is_valid"] is False


def test_blocks_statement_chaining():
    state = validate_sql(_fake_state("SELECT * FROM orders; DROP TABLE orders;"))
    assert state["validation_result"]["is_valid"] is False


def test_blocks_unauthorized_table():
    # "users" was never in retrieved_schema — only "orders" was allowed.
    state = validate_sql(_fake_state("SELECT * FROM users;"))
    assert state["validation_result"]["is_valid"] is False


def test_allows_safe_select():
    state = validate_sql(_fake_state("SELECT * FROM orders WHERE amount > 100;"))
    assert state["validation_result"]["is_valid"] is True


def test_allows_subquery_join():
    # Regression test: a JOIN against a subquery was previously flagged as
    # an "unauthorized table" because the naive table-extraction logic
    # treated the subquery's opening "(" itself as a table name.
    sql = (
        "SELECT o.* FROM orders o JOIN "
        "(SELECT customer_id, COUNT(*) as cnt FROM orders "
        "GROUP BY customer_id ORDER BY cnt DESC LIMIT 1) t "
        "ON o.customer_id = t.customer_id"
    )
    state = validate_sql(_fake_state(sql, allowed_tables=("orders",)))
    assert state["validation_result"]["is_valid"] is True