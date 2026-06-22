from app.database import fetch_prediction, init_db, save_prediction, update_feedback


def test_save_prediction_and_update_feedback(tmp_path):
    db_path = tmp_path / "feedback.sqlite3"
    init_db(db_path)

    save_prediction(
        {
            "request_id": "req-1",
            "country": "United States",
            "city": "San Francisco",
            "industry": "Fintech",
            "join_year": 2021,
            "join_month": 7,
            "investor_count": 3,
            "prediction_billion_usd": 3.25,
            "model_used": "mock_model",
            "created_at": "2026-06-19T10:00:00+00:00",
            "updated_at": "2026-06-19T10:00:00+00:00",
        },
        db_path,
    )

    saved = update_feedback(
        request_id="req-1",
        feedback_score=4,
        actual_valuation_b=3.5,
        comments="Close estimate",
        updated_at="2026-06-19T10:05:00+00:00",
        db_path=db_path,
    )

    record = fetch_prediction("req-1", db_path)

    assert saved is True
    assert record is not None
    assert record["feedback_score"] == 4
    assert record["actual_valuation_b"] == 3.5
    assert record["comments"] == "Close estimate"


def test_update_feedback_returns_false_for_missing_request(tmp_path):
    db_path = tmp_path / "feedback.sqlite3"

    saved = update_feedback(
        request_id="missing",
        feedback_score=2,
        actual_valuation_b=None,
        comments=None,
        updated_at="2026-06-19T10:05:00+00:00",
        db_path=db_path,
    )

    assert saved is False
