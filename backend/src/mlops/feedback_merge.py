"""Merge confirmed prediction feedback into the Kaggle training dataset.

Phase-7 ticket [T-7.11]: closes the MLOps loop by incorporating rows where
``actual_valuation_usd IS NOT NULL`` into retraining (``POST /retrain`` /
``scripts/train.py --report``).

Rules (see ``2_spec.md §3.1.6``):
- Minimum 5 confirmed feedback rows required to activate the merge.
- Deduplicate by ``(year_founded, funding_usd, industry, country)``; the most
  recent ``created_at`` wins.
- Feedback rows replace matching Kaggle rows before concatenation.
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.data.load import add_engineered_features, get_industry_funding_medians

logger = logging.getLogger(__name__)

MIN_FEEDBACK_SAMPLES = 5
_DEDUP_COLS = ("year_founded", "funding_usd", "industry", "country")
_FEEDBACK_COLS = (
    "year_founded",
    "funding_usd",
    "company_age",
    "industry",
    "country",
    "continent",
    "actual_valuation_usd",
    "created_at",
)


def _normalize_key(row: pd.Series) -> tuple[Any, ...]:
    """Build a deduplication key with case-insensitive text fields."""
    return (
        int(row["year_founded"]),
        float(row["funding_usd"]),
        str(row["industry"]).strip().lower(),
        str(row["country"]).strip(),
    )


def _load_confirmed_feedback() -> pd.DataFrame:
    """Return feedback rows with a confirmed ground-truth valuation."""
    try:
        from app.database import Prediction, get_session

        session = get_session()
        try:
            rows = (
                session.query(Prediction)
                .filter(Prediction.actual_valuation_usd.isnot(None))
                .order_by(Prediction.created_at.asc())
                .all()
            )
            if not rows:
                return pd.DataFrame(columns=_FEEDBACK_COLS)
            data = [{col: getattr(row, col, None) for col in _FEEDBACK_COLS} for row in rows]
            return pd.DataFrame(data)
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Could not query feedback from DB (%s). Skipping merge.", exc)
        return pd.DataFrame(columns=_FEEDBACK_COLS)


def _dedupe_feedback(feedback_df: pd.DataFrame) -> pd.DataFrame:
    """Keep the most recent row per deduplication key."""
    if feedback_df.empty:
        return feedback_df

    working = feedback_df.copy()
    working["_dedup_key"] = working.apply(_normalize_key, axis=1)
    working = working.sort_values("created_at", ascending=True)
    deduped = working.drop_duplicates(subset=["_dedup_key"], keep="last").drop(columns="_dedup_key")
    return deduped.reset_index(drop=True)


def _feedback_to_training_rows(
    feedback_df: pd.DataFrame,
    reference_df: pd.DataFrame,
) -> pd.DataFrame:
    """Convert feedback records into processed-dataset rows."""
    base = feedback_df.rename(columns={"actual_valuation_usd": "valuation_usd"}).copy()
    base = base[
        [
            "year_founded",
            "funding_usd",
            "company_age",
            "industry",
            "country",
            "continent",
            "valuation_usd",
        ]
    ]
    industry_medians = get_industry_funding_medians(reference_df)
    return add_engineered_features(base, industry_medians=industry_medians)


def _drop_kaggle_duplicates(df_kaggle: pd.DataFrame, feedback_df: pd.DataFrame) -> pd.DataFrame:
    """Remove Kaggle rows superseded by feedback keys."""
    if feedback_df.empty:
        return df_kaggle

    feedback_keys = {_normalize_key(row) for _, row in feedback_df.iterrows()}
    keep_mask = df_kaggle.apply(lambda row: _normalize_key(row) not in feedback_keys, axis=1)
    return df_kaggle.loc[keep_mask].reset_index(drop=True)


def merge_feedback_into_dataset(
    df_kaggle: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Augment the Kaggle dataset with confirmed feedback when enough rows exist.

    Parameters
    ----------
    df_kaggle:
        Processed training dataset (output of ``load_processed_dataset()``).
    cfg:
        Loaded ``config.yaml`` dict (reserved for future thresholds).

    Returns
    -------
    tuple of:
        - augmented DataFrame ready for Optuna K-Fold
        - merge metadata dict with ``n_feedback_samples_merged`` and
          ``feedback_merge_enabled`` keys
    """
    del cfg  # reserved for future configuration hooks

    feedback_raw = _load_confirmed_feedback()
    feedback_deduped = _dedupe_feedback(feedback_raw)
    n_feedback = len(feedback_deduped)

    meta: dict[str, Any] = {
        "n_feedback_samples_merged": 0,
        "feedback_merge_enabled": False,
    }

    if n_feedback < MIN_FEEDBACK_SAMPLES:
        logger.info(
            "Feedback merge skipped: %d confirmed rows (< %d required).",
            n_feedback,
            MIN_FEEDBACK_SAMPLES,
        )
        return df_kaggle, meta

    feedback_rows = _feedback_to_training_rows(feedback_deduped, df_kaggle)
    kaggle_filtered = _drop_kaggle_duplicates(df_kaggle, feedback_deduped)
    merged = pd.concat([kaggle_filtered, feedback_rows], ignore_index=True)

    meta["n_feedback_samples_merged"] = n_feedback
    meta["feedback_merge_enabled"] = True
    logger.info("Merged %d feedback samples into training dataset.", n_feedback)
    print(f"[INFO] Merged {n_feedback} feedback samples into training dataset.")

    return merged, meta
