from datetime import UTC, datetime

from app.database import save_feedback
from app.input_schema import FeedbackRequest


def record_feedback(
    payload: FeedbackRequest,
    *,
    predicted_multiple: float = 0.0,
    model_version: str = "prod",
) -> int | None:
    """Persist one feedback record and return its auto-generated id.

    Args:
        payload: The validated feedback request from the API layer.
        predicted_multiple: ``valuation_usd / funding_usd`` ratio produced at
            inference time.  Defaults to 0.0 when not provided (backwards
            compatibility with callers that predate Phase 7).
        model_version: Slug of the model variant that produced the prediction
            (``"prod"`` or ``"candidate"``).  Used for A/B metric tracking.

    Returns:
        The auto-generated integer id of the newly inserted row, or ``None``
        if the insert failed silently.
    """
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
            "created_at": datetime.now(UTC),
            # ── Phase-7 MLOps fields ──────────────────────────────────────
            "predicted_multiple": predicted_multiple,
            "model_version": model_version,
        }
    )
