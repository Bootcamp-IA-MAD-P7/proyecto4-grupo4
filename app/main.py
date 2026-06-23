from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.feedback_service import record_feedback, record_prediction
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


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model_mode=get_model_mode())


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionInput) -> PredictionResponse:
    prediction, model_used = predict_valuation(payload)
    request_id = record_prediction(payload, prediction, model_used)
    return PredictionResponse(
        request_id=request_id,
        prediction_billion_usd=prediction,
        model_used=model_used,
        message="Prediction generated successfully.",
    )


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackInput) -> FeedbackResponse:
    saved = record_feedback(payload)
    if not saved:
        raise HTTPException(status_code=404, detail="Prediction request_id not found.")
    return FeedbackResponse(
        request_id=payload.request_id,
        saved=True,
        message="Feedback saved successfully.",
    )
