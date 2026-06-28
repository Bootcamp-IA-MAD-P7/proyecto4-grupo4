import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

import app.model_service as model_service_module
from app.main import app
from tests.conftest import PREDICT_PAYLOAD

client = TestClient(app)

# Phase-7 target is log1p(multiple).  multiple ≈ 20 → valuation = 20 × funding.
_MOCK_MULTIPLE = 20.0
_MOCK_FUNDING = PREDICT_PAYLOAD["funding_usd"]
_LOG_SCALE_PREDICTION = math.log1p(_MOCK_MULTIPLE)


@pytest.fixture(autouse=True)
def _inject_mock_model():
    """Replace _prod_model with a MagicMock for the duration of each test."""
    from unittest.mock import MagicMock
    import yaml
    from pathlib import Path

    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "config.yaml").read_text())

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([_LOG_SCALE_PREDICTION])

    original_prod = model_service_module._prod_model
    original_cfg = model_service_module._cfg
    model_service_module._prod_model = mock_model
    model_service_module._cfg = cfg
    yield mock_model
    model_service_module._prod_model = original_prod
    model_service_module._cfg = original_cfg


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_and_feedback_flow():
    prediction_response = client.post("/predict", json=PREDICT_PAYLOAD)

    assert prediction_response.status_code == 200
    prediction_body = prediction_response.json()
    assert prediction_body["valuation_usd"] > 0
    assert prediction_body["valuation_b"] > 0
    assert round(prediction_body["valuation_b"], 4) == round(
        prediction_body["valuation_usd"] / 1_000_000_000, 4
    )

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
