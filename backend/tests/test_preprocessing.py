from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.data.load import build_features, get_feature_columns, prepare_modeling_frame
from src.data.preprocess import build_preprocessor

FEATURE_COLUMNS = get_feature_columns()


@pytest.fixture
def raw_unicorn_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Valuation": ["$140B", "$127B", "$100B", "$95B", "$40B"],
            "Funding": ["$3B", "$1B", "$2B", "$2.3B", "$300M"],
            "Year Founded": [2012, 2002, 2015, 2010, 2013],
            "Industry": [
                "Artificial intelligence",
                "Other",
                "E-commerce & direct-to-consumer",
                "Fintech",
                "Internet software & services",
            ],
            "Country": ["China", "United States", "China", "United States", "Australia"],
            "Continent": ["Asia", "North America", "Asia", "North America", "Oceania"],
        }
    )


@pytest.fixture
def featured_df(raw_unicorn_df) -> pd.DataFrame:
    return build_features(raw_unicorn_df)


class TestBuildFeatures:
    def test_creates_definitive_schema_columns(self, featured_df):
        config = load_config()
        expected = set(FEATURE_COLUMNS + [config["project"]["target"]])
        assert expected.issubset(set(featured_df.columns))

    def test_parses_valuation_usd(self, featured_df):
        assert featured_df["valuation_usd"].iloc[0] == 140_000_000_000
        assert featured_df["valuation_usd"].notna().all()

    def test_parses_funding_usd(self, featured_df):
        assert featured_df["funding_usd"].iloc[0] == 3_000_000_000
        assert featured_df["funding_usd"].notna().all()

    def test_computes_company_age(self, featured_df):
        assert featured_df["company_age"].notna().all()
        assert (featured_df["company_age"] >= 0).all()

    def test_adds_engineered_features(self, featured_df):
        assert "log_funding_usd" in featured_df.columns
        assert "funding_velocity" in featured_df.columns
        assert "funding_vs_industry" in featured_df.columns
        assert np.allclose(
            featured_df["log_funding_usd"],
            np.log1p(featured_df["funding_usd"]),
        )
        assert (featured_df["funding_velocity"] > 0).all()
        assert (featured_df["funding_vs_industry"] > 0).all()


class TestPrepareModelingFrame:
    def test_returns_aligned_features_and_target(self, featured_df):
        x, y = prepare_modeling_frame(featured_df)
        assert list(x.columns) == FEATURE_COLUMNS
        assert len(x) == len(y)
        assert y.name == "valuation_usd"

    def test_drops_rows_with_missing_numeric_features(self, featured_df):
        broken = featured_df.copy()
        broken.loc[0, "log_funding_usd"] = np.nan
        x, y = prepare_modeling_frame(broken)
        assert len(x) == len(featured_df) - 1


class TestBuildPreprocessor:
    def test_builds_column_transformer(self, featured_df):
        x, _ = prepare_modeling_frame(featured_df)
        preprocessor = build_preprocessor()
        transformed = preprocessor.fit_transform(x)
        assert transformed.shape[0] == len(x)
        assert transformed.shape[1] > 0

    def test_no_nan_after_transform(self, featured_df):
        x, _ = prepare_modeling_frame(featured_df)
        preprocessor = build_preprocessor()
        transformed = preprocessor.fit_transform(x)
        assert not np.isnan(transformed).any()
