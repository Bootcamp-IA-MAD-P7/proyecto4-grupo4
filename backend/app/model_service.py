import json
import numpy as np
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import HTTPException

from app.input_schema import PredictionInput
from src.data.load import get_industry_funding_medians, make_model_feature_frame
from src.models.train import LogTargetRegressor


ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = os.getenv("MODEL_PATH", "models/best_model.joblib")
METRICS_PATH = ROOT_DIR / "models" / "metrics.json"

_cached_model: Any | None = None


def get_model_path() -> Path:
    path = Path(MODEL_PATH)
    if not path.is_absolute():
        return ROOT_DIR / path
    return path


def preload_model() -> None:
    """Load the model into the module-level cache at application startup.

    Raises RuntimeError if the model file is missing so the process fails
    with an explicit message rather than silently serving 503s.
    """
    global _cached_model
    model_path = get_model_path()
    if not model_path.exists():
        raise RuntimeError(
            f"Model file not found at '{model_path}'. "
            "Run 'python scripts/train.py' to train and save the model."
        )
    _cached_model = joblib.load(model_path)


def load_model() -> Any | None:
    """Return the cached model, or load it on first call (fallback for tests)."""
    if _cached_model is not None:
        return _cached_model
    model_path = get_model_path()
    if not model_path.exists():
        return None
    return joblib.load(model_path)


def is_model_loaded() -> bool:
    return _cached_model is not None or get_model_path().exists()


def get_model_mode() -> str:
    return "trained_model" if is_model_loaded() else "not_loaded"


def get_model_r2() -> float | None:
    if not METRICS_PATH.exists():
        return None
    try:
        data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        return data.get("validation", {}).get("r2")
    except Exception:
        return None


def get_metrics() -> dict[str, Any] | None:
    if not METRICS_PATH.exists():
        return None
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


@lru_cache(maxsize=1)
def _industry_funding_medians() -> dict[str, float]:
    return get_industry_funding_medians()


def make_feature_frame(payload: PredictionInput) -> pd.DataFrame:
    base = pd.DataFrame(
        [
            {
                "year_founded": payload.year_founded,
                "funding_usd": payload.funding_usd,
                "company_age": payload.company_age,
                "industry": payload.industry,
                "country": payload.country,
                "continent": payload.continent,
            }
        ]
    )
    return make_model_feature_frame(base, industry_medians=_industry_funding_medians())


def predict_valuation(payload: PredictionInput) -> tuple[float, str]:
    model = load_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run scripts/train.py first.",
        )
    raw_prediction = float(model.predict(make_feature_frame(payload))[0])
    if isinstance(model, LogTargetRegressor):
        valuation_usd = raw_prediction
    else:
        valuation_usd = float(np.expm1(raw_prediction))
    return round(max(valuation_usd, 0.0), 3), "trained_model"
