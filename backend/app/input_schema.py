from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    year_founded: int = Field(..., ge=1800, le=2026, examples=[2015])
    funding_usd: float = Field(..., ge=0, examples=[50_000_000.0])
    company_age: int = Field(..., ge=0, examples=[9])
    industry: str = Field(..., min_length=1, examples=["fintech"])
    country: str = Field(..., min_length=1, examples=["United States"])
    continent: str = Field(..., min_length=1, examples=["North America"])

    @field_validator("industry", "country", "continent")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned


class PredictResponse(BaseModel):
    valuation_usd: float
    valuation_b: float
    model_version: str
    timestamp: str


class FeedbackRequest(PredictRequest):
    predicted_valuation_usd: float = Field(..., ge=0)
    actual_valuation_usd: float | None = Field(default=None, ge=0)
    comment: str | None = Field(default=None, max_length=500)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


class FeedbackResponse(BaseModel):
    id: int
    status: str
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_mode: str


# Backward-compatible aliases for modules that still import the old names.
PredictionInput = PredictRequest
PredictionResponse = PredictResponse
FeedbackInput = FeedbackRequest
