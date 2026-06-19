import pandas as pd
import numpy as np


RAW_REQUIRED_COLUMNS = [
    "Company",
    "Valuation ($B)",
    "Date Joined",
    "Country",
    "City\xa0",
    "Industry",
    "Investors",
]

CLEAN_REQUIRED_COLUMNS = [
    "valuation_b",
    "join_year",
    "join_month",
    "investor_count",
]


def check_required_columns(df: pd.DataFrame, required: list) -> dict:
    """Check that all required columns exist in the dataframe."""
    missing = [c for c in required if c not in df.columns]
    return {
        "passed": len(missing) == 0,
        "missing_columns": missing,
    }


def check_no_duplicates(df: pd.DataFrame) -> dict:
    """Check for exact duplicate rows."""
    n_dup = df.duplicated().sum()
    return {
        "passed": n_dup == 0,
        "n_duplicates": int(n_dup),
    }


def check_nulls(df: pd.DataFrame, max_pct: float = 5.0, exclude: list = None) -> dict:
    """Check null percentages per column. Fails if any column exceeds max_pct."""
    cols = [c for c in df.columns if exclude is None or c not in exclude]
    null_pct = (df[cols].isnull().sum() / len(df) * 100).round(2)
    over_limit = null_pct[null_pct > max_pct]
    return {
        "passed": len(over_limit) == 0,
        "null_pct_per_column": null_pct.to_dict(),
        "columns_over_limit": over_limit.to_dict(),
    }


def check_valuation_numeric(df: pd.DataFrame, col: str = "valuation_b") -> dict:
    """Check that the valuation column is numeric and has no NaN."""
    if col not in df.columns:
        return {"passed": False, "error": f"Column '{col}' not found"}
    is_numeric = pd.api.types.is_numeric_dtype(df[col])
    n_nan = int(df[col].isna().sum())
    return {
        "passed": is_numeric and n_nan == 0,
        "dtype": str(df[col].dtype),
        "n_nan": n_nan,
    }


def check_dates_parseable(df: pd.DataFrame, col: str = "Date Joined") -> dict:
    """Check that date column can be parsed to datetime."""
    if col not in df.columns:
        return {"passed": False, "error": f"Column '{col}' not found"}
    parsed = pd.to_datetime(df[col], errors="coerce")
    n_failed = int(parsed.isna().sum())
    return {
        "passed": n_failed == 0,
        "n_failed": n_failed,
        "n_total": len(df),
    }


def check_no_shifted_rows(df: pd.DataFrame) -> dict:
    """Detect rows where City is missing but should be present (shifted data)."""
    city_col = None
    for c in df.columns:
        if "city" in c.lower():
            city_col = c
            break
    if city_col is None:
        return {"passed": False, "error": "City column not found"}

    empty_cities = df[
        df[city_col].isna()
        | (df[city_col].astype(str).str.strip() == "")
        | (df[city_col].astype(str).str.strip() == "nan")
    ]
    return {
        "passed": len(empty_cities) == 0,
        "n_shifted_rows": len(empty_cities),
        "indices": empty_cities.index.tolist(),
    }


def check_target_range(df: pd.DataFrame, col: str = "valuation_b") -> dict:
    """Check that target values are positive and within reasonable range."""
    if col not in df.columns:
        return {"passed": False, "error": f"Column '{col}' not found"}
    vals = df[col].dropna()
    return {
        "passed": bool((vals > 0).all() and (vals < 1000).all()),
        "min": float(vals.min()),
        "max": float(vals.max()),
        "n_negative": int((vals <= 0).sum()),
        "n_over_1000": int((vals >= 1000).sum()),
    }


def run_all_checks_raw(df: pd.DataFrame) -> dict:
    """Run all validation checks on the raw dataset."""
    return {
        "required_columns": check_required_columns(df, RAW_REQUIRED_COLUMNS),
        "no_duplicates": check_no_duplicates(df),
        "nulls": check_nulls(df, max_pct=5.0),
        "dates_parseable": check_dates_parseable(df, "Date Joined"),
        "shifted_rows": check_no_shifted_rows(df),
    }


def run_all_checks_clean(df: pd.DataFrame) -> dict:
    """Run all validation checks on the clean dataset."""
    return {
        "required_columns": check_required_columns(df, CLEAN_REQUIRED_COLUMNS),
        "no_duplicates": check_no_duplicates(df),
        "nulls": check_nulls(df, max_pct=5.0, exclude=["investors"]),
        "valuation_numeric": check_valuation_numeric(df, "valuation_b"),
        "target_range": check_target_range(df, "valuation_b"),
    }


def print_check_results(name: str, results: dict):
    """Print validation results in a readable format."""
    print(f"\n{'=' * 50}")
    print(f"  {name}")
    print(f"{'=' * 50}")
    for check, result in results.items():
        status = "PASS" if result["passed"] else "FAIL"
        print(f"\n  [{status}] {check}")
        for k, v in result.items():
            if k == "passed":
                continue
            print(f"    {k}: {v}")
