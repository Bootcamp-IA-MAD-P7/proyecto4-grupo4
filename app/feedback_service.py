from datetime import UTC, datetime
from uuid import uuid4

from app.database import save_prediction, update_feedback
from app.input_schema import FeedbackInput, PredictionInput


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def record_prediction(
    payload: PredictionInput,
    prediction_billion_usd: float,
    model_used: str,
) -> str:
    request_id = str(uuid4())
    timestamp = utc_now_iso()
    save_prediction(
        {
            "request_id": request_id,
            "country": payload.country,
            "city": payload.city,
            "industry": payload.industry,
            "join_year": payload.join_year,
            "join_month": payload.join_month,
            "investor_count": payload.investor_count,
            "prediction_billion_usd": prediction_billion_usd,
            "model_used": model_used,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    return request_id


def record_feedback(payload: FeedbackInput) -> bool:
    return update_feedback(
        request_id=payload.request_id,
        feedback_score=payload.feedback_score,
        actual_valuation_b=payload.actual_valuation_b,
        comments=payload.comments,
        updated_at=utc_now_iso(),
    )
