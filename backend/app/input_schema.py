from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    year_founded: int = Field(..., ge=1800, le=2030, examples=[2015])
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


# Backwards-compat alias used by model_service.py
PredictionInput = PredictRequest


class PredictResponse(BaseModel):
    valuation_usd: float
    valuation_b: float
    model_version: str
    timestamp: str


# Backwards-compat alias
PredictionResponse = PredictResponse


class FeedbackRequest(PredictRequest):
    predicted_valuation_usd: float = Field(..., ge=0)
    actual_valuation_usd: Optional[float] = Field(default=None, ge=0)
    comment: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


# Backwards-compat alias used by feedback_service.py
FeedbackInput = FeedbackRequest


class FeedbackResponse(BaseModel):
    id: int
    status: str
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_r2: Optional[float] = None
