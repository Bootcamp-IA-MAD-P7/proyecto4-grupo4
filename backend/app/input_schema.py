from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PredictionInput(BaseModel):
    country: str = Field(..., min_length=1, examples=["United States"])
    city: str = Field(..., min_length=1, examples=["San Francisco"])
    industry: str = Field(..., min_length=1, examples=["Fintech"])
    join_year: int = Field(..., ge=2007, le=2026, examples=[2021])
    join_month: int = Field(..., ge=1, le=12, examples=[7])
    investor_count: int = Field(..., ge=0, le=20, examples=[3])

    @field_validator("country", "city", "industry")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned


class PredictionResponse(BaseModel):
    request_id: str
    prediction_billion_usd: float
    unit: str = "billion_usd"
    model_used: str
    message: str


class FeedbackInput(BaseModel):
    request_id: str = Field(..., min_length=1)
    feedback_score: Optional[int] = Field(default=None, ge=1, le=5)
    actual_valuation_b: Optional[float] = Field(default=None, ge=0)
    comments: Optional[str] = Field(default=None, max_length=500)

    @field_validator("request_id")
    @classmethod
    def strip_request_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("request_id cannot be empty.")
        return cleaned

    @field_validator("comments")
    @classmethod
    def strip_comments(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


class FeedbackResponse(BaseModel):
    request_id: str
    saved: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    model_mode: str
