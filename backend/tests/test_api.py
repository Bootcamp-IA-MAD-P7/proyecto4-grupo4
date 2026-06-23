from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import PREDICT_PAYLOAD

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.model_service.load_model")
def test_predict_and_feedback_flow(mock_load_model):
    mock_model = MagicMock()
    mock_model.predict.return_value = [1_250_000_000.0]
    mock_load_model.return_value = mock_model

    prediction_response = client.post("/predict", json=PREDICT_PAYLOAD)

    assert prediction_response.status_code == 200
    prediction_body = prediction_response.json()
    assert prediction_body["valuation_usd"] > 0
    assert prediction_body["valuation_b"] > 0
    assert prediction_body["valuation_b"] == prediction_body["valuation_usd"] / 1_000_000_000

    feedback_response = client.post(
        "/feedback",
        json={
            **PREDICT_PAYLOAD,
            "predicted_valuation_usd": prediction_body["valuation_usd"],
            "actual_valuation_usd": 1_100_000_000.0,
            "comment": "Useful estimate",
        },
    )

    assert feedback_response.status_code == 201
    feedback_body = feedback_response.json()
    assert feedback_body["status"] == "recorded"
    assert feedback_body["id"] > 0
