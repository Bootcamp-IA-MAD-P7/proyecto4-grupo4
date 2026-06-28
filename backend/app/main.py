from __future__ import annotations

import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncIterator, List

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Prediction, get_db, init_db
from app.feedback_service import record_feedback
from app.input_schema import (
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    PredictionRecord,
    RetrainResponse,
    UpdatePredictionRequest,
    UpdatePredictionResponse,
)
from app.model_service import get_metrics, get_model_r2, is_model_loaded, predict_valuation, preload_model

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    preload_model()
    yield


app = FastAPI(title="Unicorn Valuation API", version="0.1.0", lifespan=lifespan)

# CORS_ORIGINS accepts a comma-separated list of allowed origins.
# In production set it to the public frontend URL, e.g.:
#   CORS_ORIGINS=http://EC2_IP:3005
# When the variable is absent the defaults cover local development.
_raw_cors = os.getenv("CORS_ORIGINS", "")
_allow_origins = (
    [o.strip() for o in _raw_cors.split(",") if o.strip()]
    if _raw_cors
    else ["http://localhost:5173", "http://127.0.0.1:5173"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=is_model_loaded(),
        model_r2=get_model_r2(),
    )


@app.get("/metrics")
def metrics() -> dict:
    data = get_metrics()
    if data is None:
        raise HTTPException(
            status_code=503,
            detail="Metrics not available. Run scripts/train.py first.",
        )
    return data


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    valuation_usd, _predicted_multiple, model_version = predict_valuation(payload)
    return PredictResponse(
        valuation_usd=valuation_usd,
        valuation_b=round(valuation_usd / 1_000_000_000, 4),
        model_version=model_version,
        timestamp=utc_now_iso(),
    )


@app.post("/feedback", response_model=FeedbackResponse, status_code=201)
def feedback(payload: FeedbackRequest) -> FeedbackResponse:
    feedback_id = record_feedback(payload)
    if feedback_id is None:
        raise HTTPException(status_code=500, detail="Feedback could not be saved.")
    return FeedbackResponse(
        id=feedback_id,
        status="recorded",
        timestamp=utc_now_iso(),
    )


# ── Phase-7 MLOps endpoints ──────────────────────────────────────────────────


@app.get("/predictions", response_model=List[PredictionRecord])
def get_predictions(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[Prediction]:
    return (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.put("/predictions/{prediction_id}", response_model=UpdatePredictionResponse)
def update_prediction(
    prediction_id: int,
    body: UpdatePredictionRequest,
    db: Session = Depends(get_db),
) -> UpdatePredictionResponse:
    record = db.get(Prediction, prediction_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Prediction {prediction_id} not found.")

    actual_multiple = body.actual_valuation_usd / max(record.funding_usd, 1.0)
    record.actual_valuation_usd = body.actual_valuation_usd
    record.actual_multiple = actual_multiple
    if body.comment is not None:
        record.comment = body.comment
    db.commit()

    return UpdatePredictionResponse(
        id=prediction_id,
        status="updated",
        actual_multiple=round(actual_multiple, 6),
        timestamp=utc_now_iso(),
    )


# ── Retrain background task ──────────────────────────────────────────────────

_retrain_in_progress: bool = False


def _run_retrain_background() -> None:
    global _retrain_in_progress
    try:
        backend_dir = Path(__file__).resolve().parents[1]

        try:
            from src.mlops.drift import detect_drift
            from src.config import load_config

            cfg = load_config()
            drift_result = detect_drift(cfg)
            logger.info("Drift detection result: drift_detected=%s", drift_result.get("drift_detected"))
        except Exception as exc:
            logger.warning("Drift detection skipped (%s). Proceeding with retrain.", exc)

        result = subprocess.run(
            [sys.executable, "scripts/train.py", "--report"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Retrain completed successfully.\n%s", result.stdout)
            if '"decision": "promoted"' in result.stdout:
                logger.info("Auto-replacement: candidate promoted to production.")
            elif '"decision": "discarded"' in result.stdout:
                logger.info("Auto-replacement: candidate discarded.")
            elif '"decision": "candidate"' in result.stdout:
                logger.info("Auto-replacement: candidate kept for A/B testing.")
            try:
                preload_model()
            except Exception as exc:
                logger.error("Could not reload model after retrain: %s", exc)
        else:
            logger.error("Retrain script exited with code %d.\n%s", result.returncode, result.stderr)
    finally:
        _retrain_in_progress = False


@app.post("/retrain", response_model=RetrainResponse, status_code=202)
def retrain(background_tasks: BackgroundTasks) -> RetrainResponse:
    global _retrain_in_progress
    if _retrain_in_progress:
        raise HTTPException(status_code=503, detail="Reentrenamiento ya en curso.")
    _retrain_in_progress = True
    background_tasks.add_task(_run_retrain_background)
    return RetrainResponse(
        status="retrain_started",
        message="El reentrenamiento se ejecuta en segundo plano.",
        timestamp=utc_now_iso(),
    )
