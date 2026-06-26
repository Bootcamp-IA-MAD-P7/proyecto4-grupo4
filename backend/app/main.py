from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.feedback_service import record_feedback
from app.input_schema import (
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
)
from app.model_service import get_metrics, get_model_r2, is_model_loaded, predict_valuation, preload_model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    preload_model()
    yield


app = FastAPI(title="Unicorn Valuation API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
    valuation_usd, _model_used = predict_valuation(payload)
    return PredictResponse(
        valuation_usd=valuation_usd,
        valuation_b=round(valuation_usd / 1_000_000_000, 4),
        model_version="best_model.joblib",
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
