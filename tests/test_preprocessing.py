import sys
import os
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.preprocessing.preprocessing_pipeline import (
    FeatureEngineer,
    get_feature_types,
    build_preprocessor,
    build_full_pipeline,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Company": ["ByteDance", "SpaceX", "SHEIN", "Stripe", "Canva"],
            "Valuation ($B)": ["$140", "$127", "$100", "$95", "$40"],
            "Date Joined": ["4/7/2017", "12/1/2012", "7/3/2018", "1/23/2014", "1/8/2018"],
            "Country": ["China", "United States", "China", "United States", "Australia"],
            "City ": ["Beijing", "Hawthorne", "Shenzhen", "San Francisco", "Surry Hills"],
            "Industry": [
                "Artificial intelligence",
                "Other",
                "E-commerce & direct-to-consumer",
                "Fintech",
                "Internet software & services",
            ],
            "Investors": [
                "Sequoia, SIG Asia, Sina Weibo, Softbank",
                "Founders Fund, Draper Fisher, Rothenberg",
                "Tiger Global, Sequoia China, Shunwei",
                "Khosla, LowercaseCapital, capitalG",
                "Sequoia China, Blackbird, Matrix",
            ],
        }
    )


class TestFeatureEngineer:
    def test_fit_transform(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_creates_valuation_b(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        assert "valuation_b" in result.columns
        assert np.issubdtype(result["valuation_b"].dtype, np.number)
        assert result["valuation_b"].iloc[0] == 140

    def test_creates_date_features(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        assert "join_year" in result.columns
        assert "join_month" in result.columns
        assert "years_since_joined" in result.columns
        assert result["join_year"].iloc[0] == 2017
        assert result["join_month"].iloc[0] == 4

    def test_creates_investors_count(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        assert "investors_count" in result.columns
        assert result["investors_count"].iloc[0] == 4

    def test_drops_company(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        assert "Company" not in result.columns
        assert "Date Joined" not in result.columns
        assert "Investors" not in result.columns
        assert "Valuation ($B)" not in result.columns

    def test_city_column_cleaned(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        assert "City" in result.columns

    def test_handles_missing_investors(self):
        df = pd.DataFrame(
            {
                "Company": ["A", "B"],
                "Valuation ($B)": ["$10", "$20"],
                "Date Joined": ["1/1/2020", "6/15/2021"],
                "Country": ["US", "UK"],
                "City ": ["NY", "London"],
                "Industry": ["Tech", "Finance"],
                "Investors": [np.nan, "VC1, VC2"],
            }
        )
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(df)
        assert result["investors_count"].iloc[0] == 0
        assert result["investors_count"].iloc[1] == 2


class TestGetFeatureTypes:
    def test_returns_correct_types(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        numeric, categorical = get_feature_types(result)
        assert "join_year" in numeric
        assert "join_month" in numeric
        assert "years_since_joined" in numeric
        assert "investors_count" in numeric
        assert "Country" in categorical
        assert "Industry" in categorical


class TestBuildPreprocessor:
    def test_builds_column_transformer(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        numeric_cols, categorical_cols = get_feature_types(result)
        preprocessor = build_preprocessor(numeric_cols, categorical_cols)
        X_processed = preprocessor.fit_transform(result[numeric_cols + categorical_cols])
        assert X_processed.shape[0] == 5
        assert X_processed.shape[1] > 0

    def test_no_nan_after_transform(self, sample_df):
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        numeric_cols, categorical_cols = get_feature_types(result)
        preprocessor = build_preprocessor(numeric_cols, categorical_cols)
        X_processed = preprocessor.fit_transform(result[numeric_cols + categorical_cols])
        assert not np.isnan(X_processed).any()


class TestBuildFullPipeline:
    def test_pipeline_fit_transform(self, sample_df):
        pipeline = build_full_pipeline(
            ["join_year", "join_month", "years_since_joined", "investors_count"],
            ["Country", "Industry"],
        )
        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        X_raw = sample_df.drop(columns=["Valuation ($B)"], errors="ignore")
        y = result["valuation_b"]
        pipeline.fit(X_raw, y)
        X_transformed = pipeline.transform(X_raw)
        assert X_transformed.shape[0] == 5
        assert X_transformed.shape[1] > 0

    def test_no_data_leakage(self, sample_df):
        from sklearn.model_selection import train_test_split

        fe = FeatureEngineer(reference_date="2022-09-01")
        result = fe.fit_transform(sample_df)
        numeric_cols, categorical_cols = get_feature_types(result)
        X_raw = sample_df.drop(columns=["Valuation ($B)"], errors="ignore")
        y = result["valuation_b"]
        X_train_raw, X_test_raw, y_train, y_test = train_test_split(
            X_raw, y, test_size=0.4, random_state=42
        )
        pipeline = build_full_pipeline(numeric_cols, categorical_cols)
        pipeline.fit(X_train_raw, y_train)
        X_test_transformed = pipeline.transform(X_test_raw)
        assert X_test_transformed.shape[0] == X_test_raw.shape[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
