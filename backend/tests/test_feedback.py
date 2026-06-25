from app.database import fetch_prediction, init_db, save_feedback


def test_save_feedback_and_fetch_record(tmp_path):
    db_path = tmp_path / "feedback.sqlite3"
    init_db(db_path)

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
            "created_at": "2026-06-19T10:00:00+00:00",
        },
        db_path,
    )

    record = fetch_prediction(str(record_id), db_path)

    assert record_id is not None
    assert record is not None
    assert record["year_founded"] == 2015
    assert record["predicted_valuation_usd"] == 1_250_000_000.0
    assert record["actual_valuation_usd"] == 1_100_000_000.0
    assert record["comment"] == "Close estimate"


def test_fetch_prediction_returns_none_for_missing_record(tmp_path):
    db_path = tmp_path / "feedback.sqlite3"

    record = fetch_prediction("999", db_path)

    assert record is None
