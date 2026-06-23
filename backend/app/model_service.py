import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import HTTPException

from app.input_schema import PredictionInput


ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = os.getenv("MODEL_PATH", "models/best_model.joblib")


def get_model_path() -> Path:
    path = Path(MODEL_PATH)
    if not path.is_absolute():
        return ROOT_DIR / path
    return path


def load_model() -> Any | None:
    model_path = get_model_path()
    if not model_path.exists():
        return None
    return joblib.load(model_path)


def get_model_mode() -> str:
    return "trained_model" if get_model_path().exists() else "not_loaded"


def make_feature_frame(payload: PredictionInput) -> pd.DataFrame:
    return pd.DataFrame(
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


def predict_valuation(payload: PredictionInput) -> tuple[float, str]:
    model = load_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run scripts/train.py first.",
        )
    prediction = float(model.predict(make_feature_frame(payload))[0])
    return round(max(prediction, 0.0), 3), "trained_model"
