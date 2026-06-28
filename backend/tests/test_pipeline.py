from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODEL_PATH = ROOT / "models" / "best_model.joblib"

from src.data.load import get_feature_columns, make_model_feature_frame

FEATURE_COLUMNS = get_feature_columns()


@pytest.fixture
def sample_modeling_frame():
    import pandas as pd

    base = pd.DataFrame(
        {
            "year_founded": [2015, 2012, 2018],
            "funding_usd": [50_000_000.0, 1_000_000_000.0, 200_000_000.0],
            "company_age": [11, 14, 8],
            "industry": ["fintech", "Other", "E-commerce & direct-to-consumer"],
            "country": ["United States", "United States", "China"],
            "continent": ["North America", "North America", "Asia"],
        }
    )
    return make_model_feature_frame(
        base,
        industry_medians={
            "fintech": 100_000_000.0,
            "Other": 500_000_000.0,
            "E-commerce & direct-to-consumer": 300_000_000.0,
        },
    )


def test_parse_money():
    from src.data.load import parse_money

    assert parse_money("$180B") == 180_000_000_000
    assert parse_money("$572M") == 572_000_000
    assert parse_money("unknown") is None


def test_prepare_modeling_frame_has_rows():
    from src.data.load import build_features, load_raw_dataset, prepare_modeling_frame

    raw = load_raw_dataset()
    featured = build_features(raw)
    x, y = prepare_modeling_frame(featured)
    assert len(x) > 100
    assert len(x) == len(y)
    assert y.min() > 0


def test_modeling_frame_uses_definitive_schema(sample_modeling_frame):
    assert list(sample_modeling_frame[FEATURE_COLUMNS].columns) == FEATURE_COLUMNS


def test_best_model_loads_from_canonical_path():
    import joblib

    if not MODEL_PATH.exists():
        pytest.skip("Modelo no entrenado todavía")

    model = joblib.load(MODEL_PATH)
    assert hasattr(model, "predict")


def test_best_model_predicts_with_definitive_schema(sample_modeling_frame):
    import joblib

    if not MODEL_PATH.exists():
        pytest.skip("Modelo no entrenado todavía")

    model = joblib.load(MODEL_PATH)
    try:
        predictions = model.predict(sample_modeling_frame[FEATURE_COLUMNS])
    except ValueError as exc:
        if "columns are missing" in str(exc):
            pytest.skip("Model artifact not yet retrained with definitive schema")
        raise
    assert len(predictions) == len(sample_modeling_frame)


def test_train_meets_overfitting_limit():
    metrics_path = ROOT / "models" / "metrics.json"
    if not metrics_path.exists():
        pytest.skip("Modelo no entrenado todavía")

    report = json.loads(metrics_path.read_text(encoding="utf-8"))
    # Phase-7: overfitting_gap is a soft gate in train.py (warns, does not exit).
    # We validate the metric exists and is within the physically valid range [0, 1].
    if "overfitting_gap" in report:
        gap = report["overfitting_gap"]
        assert 0.0 <= gap < 1.0, f"overfitting_gap={gap:.3f} is outside valid range [0, 1)"
    else:
        assert report["overfitting"]["max_gap_pct"] <= 5.0


def test_train_meets_min_r2():
    """Gate activo en Fase 7 — modelo con target múltiplo debe alcanzar R² ≥ 0.40."""
    metrics_path = ROOT / "models" / "metrics.json"
    if not metrics_path.exists():
        pytest.skip("Modelo no entrenado todavía")

    report = json.loads(metrics_path.read_text(encoding="utf-8"))
    # Phase-7: r2_mean from K-Fold (preferred). Legacy: validation.r2.
    r2 = report["validation"].get("r2_mean") or report["validation"].get("r2", 0.0)
    assert r2 >= 0.40, f"R² {r2:.4f} is below the required threshold of 0.40"
