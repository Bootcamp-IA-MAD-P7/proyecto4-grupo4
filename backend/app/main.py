from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.feedback_service import record_feedback
from app.input_schema import (
    FeedbackInput,
    FeedbackResponse,
    HealthResponse,
    PredictionInput,
    PredictionResponse,
)
from app.model_service import get_model_mode, predict_valuation


app = FastAPI(title="Unicorn Valuation API", version="0.1.0")

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
    return HealthResponse(status="ok", model_mode=get_model_mode())


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionInput) -> PredictionResponse:
    valuation_usd, model_used = predict_valuation(payload)
    return PredictionResponse(
        valuation_usd=valuation_usd,
        valuation_b=round(valuation_usd / 1_000_000_000, 4),
        model_version="best_model.joblib",
        model_used=model_used,
        message="Prediction generated successfully.",
        timestamp=utc_now_iso(),
    )


@app.post("/feedback", response_model=FeedbackResponse, status_code=201)
def feedback(payload: FeedbackInput) -> FeedbackResponse:
    feedback_id = record_feedback(payload)
    if feedback_id is None:
        raise HTTPException(status_code=500, detail="Feedback could not be saved.")
    return FeedbackResponse(
        id=feedback_id,
        status="recorded",
        message="Feedback recorded successfully.",
        timestamp=utc_now_iso(),
    )
