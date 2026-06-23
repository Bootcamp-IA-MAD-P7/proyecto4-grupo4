import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.input_schema import PredictionInput


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = ROOT_DIR / "models" / "current_model.pkl"


def get_model_path() -> Path:
    return Path(os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH))


def load_model() -> Any | None:
    model_path = get_model_path()
    if not model_path.exists():
        return None
    return joblib.load(model_path)


def get_model_mode() -> str:
    return "trained_model" if get_model_path().exists() else "mock_model"


def make_feature_frame(payload: PredictionInput) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "country": payload.country,
                "city": payload.city,
                "industry": payload.industry,
                "join_year": payload.join_year,
                "join_month": payload.join_month,
                "investor_count": payload.investor_count,
            }
        ]
    )


def predict_valuation(payload: PredictionInput) -> tuple[float, str]:
    model = load_model()
    if model is not None:
        prediction = float(model.predict(make_feature_frame(payload))[0])
        return round(max(prediction, 0.0), 3), "trained_model"

    return _mock_prediction(payload), "mock_model"


def _mock_prediction(payload: PredictionInput) -> float:
    country_weight = {
        "United States": 1.15,
        "China": 1.1,
        "India": 1.03,
        "United Kingdom": 1.02,
    }.get(payload.country, 1.0)
    industry_weight = {
        "Fintech": 1.18,
        "Artificial intelligence": 1.16,
        "Internet software & services": 1.1,
        "E-commerce & direct-to-consumer": 1.05,
    }.get(payload.industry, 1.0)
    year_factor = max(0, 2023 - payload.join_year) * 0.08
    investor_factor = payload.investor_count * 0.18
    estimate = (1.0 + year_factor + investor_factor) * country_weight * industry_weight
    return round(estimate, 3)
