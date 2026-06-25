"""
Tests for database.py — SQLAlchemy-based persistence layer.
DATABASE_URL is injected by conftest.py (SQLite for the test session).
"""
from datetime import UTC, datetime

from app.database import fetch_prediction, init_db, save_feedback


def test_save_feedback_and_fetch_record():
    init_db()

    record_id = save_feedback(
        {
            "year_founded": 2015,
            "funding_usd": 50_000_000.0,
            "company_age": 9,
            "industry": "fintech",
            "country": "United States",
            "continent": "North America",
            "predicted_valuation_usd": 1_250_000_000.0,
            "actual_valuation_usd": 1_100_000_000.0,
            "comment": "Close estimate",
            "created_at": datetime(2026, 6, 19, 10, 0, 0, tzinfo=UTC),
        }
    )

    assert record_id is not None

    record = fetch_prediction(record_id)

    assert record is not None
    assert record["year_founded"] == 2015
    assert record["predicted_valuation_usd"] == 1_250_000_000.0
    assert record["actual_valuation_usd"] == 1_100_000_000.0
    assert record["comment"] == "Close estimate"


def test_fetch_prediction_returns_none_for_missing_record():
    record = fetch_prediction(999_999)
    assert record is None
