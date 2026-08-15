"""
A small, hand-written set of test questions used to measure the pipeline's
reliability over time.

This is a PROXY for correctness, not full ground-truth verification — it
checks whether the pipeline produces a successful, validated answer, not
whether the specific numbers in that answer are factually correct. True
correctness checking needs labeled expected results per question, which
requires a real populated test database — a natural next step once one
exists, not part of this MVP harness.
"""

TEST_CASES = [
    {
        "id": "revenue_basic",
        "question": "What was our total revenue last month?",
        "database_id": "test_db",
    },
    {
        "id": "revenue_by_region",
        "question": "Compare revenue between Europe and North America.",
        "database_id": "test_db",
    },
    {
        "id": "monthly_trend",
        "question": "Show monthly revenue for this year.",
        "database_id": "test_db",
    },
    # Add more cases here as the schema/questions you support grow.
]