from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Set DATABASE_URL before any app imports so database.py doesn't raise RuntimeError.
# Tests use a file-based SQLite; production uses the PostgreSQL URL from the environment.
_TEST_DB = Path(__file__).resolve().parent / "test_feedback.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")

from src.data.load import get_feature_columns, make_model_feature_frame

MODEL_PATH = ROOT / "models" / "best_model.joblib"

PREDICT_PAYLOAD = {
    "year_founded": 2015,
    "funding_usd": 50_000_000.0,
    "company_age": 9,
    "industry": "fintech",
    "country": "United States",
    "continent": "North America",
}


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_db():
    """Remove the SQLite test database file after the full test session."""
    yield
    if _TEST_DB.exists():
        _TEST_DB.unlink()


@pytest.fixture
def predict_payload() -> dict:
    return dict(PREDICT_PAYLOAD)


@pytest.fixture
def sample_modeling_frame():
    import pandas as pd

    base = pd.DataFrame(
        {
            "year_founded": [2015, 2012, 2018],
            "funding_usd": [50_000_000.0, 1_000_000_000.0, 200_000_000.0],
            "company_age": [11, 14, 8],
            "industry": ["fintech", "Other", "E-commerce & direct-to-consumer"],
            "country": ["United States", "United States", "China"],
            "continent": ["North America", "North America", "Asia"],
        }
    )
    return make_model_feature_frame(
        base,
        industry_medians={
            "fintech": 100_000_000.0,
            "Other": 500_000_000.0,
            "E-commerce & direct-to-consumer": 300_000_000.0,
        },
    )
