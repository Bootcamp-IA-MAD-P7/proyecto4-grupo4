"""Phase-7 MLOps endpoint and utility tests (T-7.8).

All tests are self-contained:
- Model service is faked by setting module-level variables directly; no
  real .joblib file is required.
- Database uses the test SQLite configured by conftest.py (DATABASE_URL).

Test cases
----------
- test_get_predictions_returns_list
- test_put_prediction_updates_actual_multiple
- test_put_prediction_not_found
- test_post_retrain_returns_202
- test_post_retrain_concurrent_blocked
- test_detect_drift_output_schema
- test_model_version_field_in_response
- test_predicted_multiple_persisted
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import yaml
from fastapi.testclient import TestClient

import app.main as main_module
import app.model_service as model_service_module
from app.database import init_db, save_feedback
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
_CFG = yaml.safe_load((ROOT / "config.yaml").read_text())

# Mock multiple ≈ 20 → valuation ≈ 20 × 50_000_000 = 1_000_000_000
_MOCK_MULTIPLE = 20.0
_MOCK_FUNDING = 50_000_000.0
_MOCK_LOG_PRED = float(np.log1p(_MOCK_MULTIPLE))

_PREDICT_PAYLOAD = {
    "year_founded": 2015,
    "funding_usd": _MOCK_FUNDING,
    "company_age": 9,
    "industry": "fintech",
    "country": "United States",
    "continent": "North America",
}


# ── fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def mock_pipeline():
    """Mock sklearn pipeline that returns a fixed log-scale prediction."""
    m = MagicMock()
    m.predict.return_value = np.array([_MOCK_LOG_PRED])
    return m


@pytest.fixture(scope="module", autouse=True)
def inject_mock_model(mock_pipeline):
    """Inject a mock pipeline so no real .joblib is needed during this suite."""
    original_prod = model_service_module._prod_model
    original_cfg = model_service_module._cfg
    model_service_module._prod_model = mock_pipeline
    model_service_module._cfg = _CFG
    init_db()
    yield
    model_service_module._prod_model = original_prod
    model_service_module._cfg = original_cfg


@pytest.fixture(scope="module")
def client():
    """Synchronous test client (no lifespan; model is injected by autouse fixture)."""
    return TestClient(app)


# ── helper ─────────────────────────────────────────────────────────────────────


def _insert_row(*, predicted_multiple: float = _MOCK_MULTIPLE) -> int:
    """Insert a minimal prediction row directly via the ORM helper."""
    row_id = save_feedback(
        {
            "year_founded": 2015,
            "funding_usd": _MOCK_FUNDING,
            "company_age": 9,
            "industry": "fintech",
            "country": "United States",
            "continent": "North America",
            "predicted_valuation_usd": predicted_multiple * _MOCK_FUNDING,
            "predicted_multiple": predicted_multiple,
            "model_version": "prod",
            "created_at": datetime.now(timezone.utc),
        }
    )
    assert row_id is not None, "save_feedback must return a row id"
    return row_id


# ── tests ──────────────────────────────────────────────────────────────────────


def test_get_predictions_returns_list(client):
    response = client.get("/predictions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_prediction_updates_actual_multiple(client):
    row_id = _insert_row()

    response = client.put(
        f"/predictions/{row_id}",
        json={"actual_valuation_usd": 1_000_000_000.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == row_id
    assert body["status"] == "updated"
    expected_multiple = 1_000_000_000.0 / _MOCK_FUNDING
    assert abs(body["actual_multiple"] - expected_multiple) < 1e-4


def test_put_prediction_not_found(client):
    response = client.put(
        "/predictions/99999",
        json={"actual_valuation_usd": 1_000_000_000.0},
    )
    assert response.status_code == 404


def test_post_retrain_returns_202(client):
    main_module._retrain_in_progress = False
    with patch("app.main._run_retrain_background"):
        response = client.post("/retrain")
    # Background task was mocked — reset the flag it would normally clear
    main_module._retrain_in_progress = False
    assert response.status_code == 202
    assert response.json()["status"] == "retrain_started"


def test_post_retrain_concurrent_blocked(client):
    """A second /retrain while one is running must return 503."""
    main_module._retrain_in_progress = True
    try:
        response = client.post("/retrain")
        assert response.status_code == 503
    finally:
        main_module._retrain_in_progress = False


def test_detect_drift_output_schema():
    from src.mlops.drift import detect_drift

    result = detect_drift(_CFG)
    assert "drift_detected" in result, "drift_detected key missing"
    assert "features" in result, "features key missing"
    assert "n_feedback_samples" in result, "n_feedback_samples key missing"
    assert isinstance(result["drift_detected"], bool)
    assert isinstance(result["n_feedback_samples"], int)


def test_model_version_field_in_response(mock_pipeline):
    from app.input_schema import PredictRequest
    from app.model_service import predict_valuation

    payload = PredictRequest(**_PREDICT_PAYLOAD)
    valuation_usd, predicted_multiple, model_version = predict_valuation(payload)
    assert model_version in ("prod", "candidate")
    assert predicted_multiple > 0
    assert valuation_usd > 0


def test_predicted_multiple_persisted(client):
    """A row inserted with predicted_multiple > 0 is returned by GET /predictions."""
    row_id = _insert_row(predicted_multiple=25.0)

    response = client.get("/predictions")
    assert response.status_code == 200
    records = response.json()
    matching = [r for r in records if r["id"] == row_id]
    assert len(matching) == 1, f"Row {row_id} not found in /predictions response"
    assert matching[0]["predicted_multiple"] > 0
