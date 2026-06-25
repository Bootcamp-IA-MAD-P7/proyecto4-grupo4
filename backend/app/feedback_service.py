from datetime import UTC, datetime

from app.database import save_feedback
from app.input_schema import FeedbackRequest


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def record_feedback(payload: FeedbackRequest) -> int | None:
    return save_feedback(
        {
            "year_founded": payload.year_founded,
            "funding_usd": payload.funding_usd,
            "company_age": payload.company_age,
            "industry": payload.industry,
            "country": payload.country,
            "continent": payload.continent,
            "predicted_valuation_usd": payload.predicted_valuation_usd,
            "actual_valuation_usd": payload.actual_valuation_usd,
            "comment": payload.comment,
            "created_at": utc_now_iso(),
        }
    )
