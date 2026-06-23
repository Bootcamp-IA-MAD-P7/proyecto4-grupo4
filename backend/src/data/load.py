from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.config import load_config, resolve_path

MONEY_PATTERN = re.compile(r"^\$([\d.]+)([BMK])?$", re.IGNORECASE)


def parse_money(value: str | float | int | None) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"unknown", "n/a"}:
        return None

    match = MONEY_PATTERN.match(text)
    if not match:
        return None

    amount = float(match.group(1))
    suffix = (match.group(2) or "").upper()
    multiplier = {"B": 1e9, "M": 1e6, "K": 1e3}.get(suffix, 1.0)
    return amount * multiplier


def load_raw_dataset(path: Path | None = None) -> pd.DataFrame:
    config = load_config()
    data_path = path or resolve_path(config["paths"]["raw_data"])
    return pd.read_csv(data_path)


def load_processed_dataset(path: Path | None = None) -> pd.DataFrame:
    config = load_config()
    data_path = path or resolve_path(config["paths"]["processed_data"])
    if not data_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {data_path}. "
            "Run build_and_save_processed_dataset() first."
        )
    return pd.read_parquet(data_path)


def build_and_save_processed_dataset(path: Path | None = None) -> Path:
    config = load_config()
    output_path = path or resolve_path(config["paths"]["processed_data"])
    featured = build_features(load_raw_dataset())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    featured.to_parquet(output_path, index=False)
    return output_path


def _group_rare_categories(series: pd.Series, min_count: int = 15) -> pd.Series:
    counts = series.value_counts()
    frequent = set(counts[counts >= min_count].index)
    return series.where(series.isin(frequent), other="Other")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["valuation_usd"] = data["Valuation"].map(parse_money)
    data["funding_usd"] = data["Funding"].map(parse_money)
    data["year_founded"] = pd.to_numeric(data["Year Founded"], errors="coerce")
    data["company_age"] = pd.Timestamp.today().year - data["year_founded"]
    data["industry"] = _group_rare_categories(data["Industry"].fillna("Unknown").astype(str))
    data["country"] = _group_rare_categories(data["Country"].fillna("Unknown").astype(str))
    data["continent"] = data["Continent"].fillna("Unknown").astype(str)
    return data


def prepare_modeling_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    config = load_config()
    feature_cols = config["features"]["numeric"] + config["features"]["categorical"]
    target_col = config["project"]["target"]

    clean = df.dropna(subset=[target_col, *config["features"]["numeric"]]).copy()
    x = clean[feature_cols]
    y = clean[target_col]
    return x, y
