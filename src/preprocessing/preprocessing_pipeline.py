import os
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.impute import SimpleImputer


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Feature engineering: date features, investor count, valuation cleaning."""

    def __init__(self, reference_date=None):
        self.reference_date = reference_date

    def fit(self, X, y=None):
        if self.reference_date is None:
            self.reference_date = pd.Timestamp.now()
        return self

    def transform(self, X):
        df = X.copy()
        df = self._clean_columns(df)
        df = self._extract_date_features(df)
        df = self._count_investors(df)
        df = self._clean_valuation(df)
        df = self._drop_unused(df)
        return df

    def _clean_columns(self, df):
        df.columns = [c.strip().replace("\xa0", "") for c in df.columns]
        return df

    def _extract_date_features(self, df):
        df["Date Joined"] = pd.to_datetime(df["Date Joined"], errors="coerce")
        df["join_year"] = df["Date Joined"].dt.year.astype("Int64")
        df["join_month"] = df["Date Joined"].dt.month.astype("Int64")
        ref = pd.Timestamp(self.reference_date)
        df["years_since_joined"] = (
            (ref - df["Date Joined"]).dt.days / 365.25
        ).round(2)
        return df

    def _count_investors(self, df):
        df["investors_count"] = df["Investors"].apply(
            lambda x: len(str(x).split(",")) if pd.notna(x) and str(x).strip() else 0
        )
        return df

    def _clean_valuation(self, df):
        col = "Valuation ($B)"
        if col in df.columns:
            df["valuation_b"] = (
                df[col]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df["valuation_b"] = pd.to_numeric(df["valuation_b"], errors="coerce")
        return df

    def _drop_unused(self, df):
        cols_to_drop = ["Company", "Date Joined", "Investors", "Valuation ($B)"]
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors="ignore")
        return df


def get_feature_types(df):
    """Return lists of numeric and categorical column names."""
    numeric_cols = ["join_year", "join_month", "years_since_joined", "investors_count"]
    categorical_cols = ["Country", "Industry"]
    numeric_cols = [c for c in numeric_cols if c in df.columns]
    categorical_cols = [c for c in categorical_cols if c in df.columns]
    return numeric_cols, categorical_cols


def build_preprocessor(numeric_cols, categorical_cols):
    """Build a ColumnTransformer with scaling for numeric and OHE for categorical."""
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=0.01)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )
    return preprocessor


def build_full_pipeline(numeric_cols, categorical_cols):
    """Full pipeline: feature engineering + preprocessing."""
    pipeline = Pipeline(
        steps=[
            ("feature_engineering", FeatureEngineer()),
            ("preprocessor", build_preprocessor(numeric_cols, categorical_cols)),
        ]
    )
    return pipeline


def save_clean_data(csv_path: str, output_dir: str = "data", reference_date=None):
    """Load raw CSV, apply FeatureEngineer, and save clean dataset."""
    df = pd.read_csv(csv_path)
    fe = FeatureEngineer(reference_date=reference_date).fit(df)
    df_clean = fe.transform(df)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "dataset_clean.csv")
    df_clean.to_csv(output_path, index=False)
    return output_path, df_clean
