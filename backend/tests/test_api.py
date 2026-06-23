from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_and_feedback_flow():
    prediction_response = client.post(
        "/predict",
        json={
            "country": "United States",
            "city": "San Francisco",
            "industry": "Fintech",
            "join_year": 2021,
            "join_month": 7,
            "investor_count": 3,
        },
    )

    assert prediction_response.status_code == 200
    prediction_body = prediction_response.json()
    assert prediction_body["prediction_billion_usd"] > 0
    assert prediction_body["model_used"] in {"mock_model", "trained_model"}

    feedback_response = client.post(
        "/feedback",
        json={
            "request_id": prediction_body["request_id"],
            "feedback_score": 5,
            "actual_valuation_b": 3.4,
            "comments": "Useful estimate",
        },
    )

    assert feedback_response.status_code == 200
    assert feedback_response.json()["saved"] is True
