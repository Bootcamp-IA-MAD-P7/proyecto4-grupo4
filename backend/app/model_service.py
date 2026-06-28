"""Model service with A/B testing and multiple-target reconversion.

Module-level state
------------------
_prod_model      – pipeline loaded from ``best_model.joblib`` (required).
_candidate_model – pipeline loaded from ``candidate_model.joblib`` (optional).
_cfg             – parsed ``config.yaml`` dict.

Prediction flow
---------------
1. ``_select_model()`` picks the model variant according to A/B weights.
2. ``pipeline.predict(X)`` returns ``log1p(multiple)`` (Phase-7 target).
3. ``np.expm1(pred)`` → actual multiple.
4. If ``target_transform == "multiple"``:  ``valuation_usd = multiple * funding_usd``.
   Else (classic absolute):               ``valuation_usd = np.expm1(pred)``.
5. Returns ``(valuation_usd, predicted_multiple, model_version)``.
"""
from __future__ import annotations

import json
import logging
import os
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.input_schema import PredictionInput
from src.config import load_config
from src.data.load import get_industry_funding_medians, make_model_feature_frame

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = os.getenv("MODEL_PATH", "models/best_model.joblib")
CANDIDATE_MODEL_PATH = os.getenv("CANDIDATE_MODEL_PATH", "models/candidate_model.joblib")
METRICS_PATH = ROOT_DIR / "models" / "metrics.json"

_prod_model: Any | None = None
_candidate_model: Any | None = None
_cfg: dict[str, Any] | None = None


# ── path helpers ───────────────────────────────────────────────────────────


def _resolve(relative: str) -> Path:
    path = Path(relative)
    return path if path.is_absolute() else ROOT_DIR / path


def get_model_path() -> Path:
    return _resolve(MODEL_PATH)


def get_candidate_model_path() -> Path:
    return _resolve(CANDIDATE_MODEL_PATH)


# ── lifecycle ──────────────────────────────────────────────────────────────


def preload_model() -> None:
    """Load both production and (optionally) candidate models at startup.

    Raises
    ------
    RuntimeError
        If the production model file is missing.
    """
    global _prod_model, _candidate_model, _cfg

    _cfg = load_config()

    prod_path = get_model_path()
    if not prod_path.exists():
        raise RuntimeError(
            f"Production model not found at '{prod_path}'. "
            "Run 'python scripts/train.py' to train and save the model."
        )
    _prod_model = joblib.load(prod_path)
    logger.info("Loaded production model from %s", prod_path)

    candidate_path = get_candidate_model_path()
    if candidate_path.exists():
        _candidate_model = joblib.load(candidate_path)
        logger.info("Loaded candidate model from %s (A/B testing active)", candidate_path)
    else:
        _candidate_model = None
        logger.info("No candidate model found at %s – A/B testing disabled", candidate_path)


# ── model selection ────────────────────────────────────────────────────────


def _select_model() -> tuple[Any, str]:
    """Return ``(pipeline, model_version_str)`` according to A/B weights."""
    if (
        _candidate_model is not None
        and _cfg is not None
        and _cfg.get("ab_testing", {}).get("enabled", False)
    ):
        weight: float = float(_cfg["ab_testing"].get("candidate_weight", 0.2))
        if random.random() < weight:
            return _candidate_model, "candidate"
    return _prod_model, "prod"


# ── status helpers ─────────────────────────────────────────────────────────


def load_model() -> Any | None:
    """Return the production model cache (fallback: load from disk)."""
    if _prod_model is not None:
        return _prod_model
    path = get_model_path()
    return joblib.load(path) if path.exists() else None


def is_model_loaded() -> bool:
    return _prod_model is not None or get_model_path().exists()


def get_model_mode() -> str:
    return "trained_model" if is_model_loaded() else "not_loaded"


def get_model_r2() -> float | None:
    if not METRICS_PATH.exists():
        return None
    try:
        data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        return data.get("validation", {}).get("r2_mean") or data.get("validation", {}).get("r2")
    except Exception:
        return None


def get_metrics() -> dict[str, Any] | None:
    if not METRICS_PATH.exists():
        return None
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


# ── feature engineering ────────────────────────────────────────────────────


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


# ── inference ──────────────────────────────────────────────────────────────


def predict_valuation(payload: PredictionInput) -> tuple[float, float, str]:
    """Run inference and return ``(valuation_usd, predicted_multiple, model_version)``.

    The model always outputs a log-transformed value (log-multiple or
    log-valuation).  This function inverts the transform and returns
    absolute dollars plus the dimensionless multiple.

    Parameters
    ----------
    payload:
        Validated prediction request (includes ``funding_usd``).

    Returns
    -------
    tuple of:
        - ``valuation_usd``    – predicted company valuation in absolute USD.
        - ``predicted_multiple`` – ``valuation_usd / funding_usd`` ratio.
        - ``model_version``    – ``"prod"`` or ``"candidate"``.
    """
    pipeline, model_version = _select_model()
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Production model not loaded. Run scripts/train.py first.",
        )

    df = make_feature_frame(payload)
    log_pred = float(pipeline.predict(df)[0])
    raw_pred = float(np.expm1(log_pred))

    cfg = _cfg if _cfg is not None else load_config()
    transform = cfg["training"].get("target_transform", "absolute")

    if transform == "multiple":
        predicted_multiple = raw_pred
        valuation_usd = raw_pred * max(payload.funding_usd, 1.0)
    else:
        valuation_usd = raw_pred
        predicted_multiple = raw_pred / max(payload.funding_usd, 1.0)

    return (
        round(max(valuation_usd, 0.0), 3),
        round(predicted_multiple, 6),
        model_version,
    )
