"""Data-drift detection — Phase 7 (T-7.7).

Entry point
-----------
``detect_drift(cfg)`` is the public API consumed by the retrain background
task (``POST /retrain``) and by ``scripts/train.py``.

Algorithm
---------
For each numeric feature in ``DRIFT_FEATURES``:

1. Kolmogorov-Smirnov two-sample test between the training distribution
   (reference) and the feedback distribution (live).
2. Mean-percentage difference: ``|live_mean - ref_mean| / |ref_mean| * 100``.

A feature is flagged as drifted when **either** condition holds:
   - ``ks_pvalue < cfg["drift"]["ks_pvalue_threshold"]``  (default 0.05)
   - ``mean_drift_pct >= cfg["drift"]["mean_drift_pct_threshold"]``  (default 20 %)

Early exit
----------
If ``n_feedback_samples < 30``, the test is skipped and the report records
``drift_detected: false`` with ``note: "insufficient_data"``.

Output
------
The result dict is serialised to ``{model_dir}/drift_report.json`` and
returned to the caller.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

logger = logging.getLogger(__name__)

DRIFT_FEATURES: list[str] = ["funding_usd", "year_founded", "company_age"]
MIN_FEEDBACK_SAMPLES = 30


def _load_reference(cfg: dict[str, Any]) -> pd.DataFrame:
    """Load the processed training dataset (parquet) from cfg paths."""
    root = Path(__file__).resolve().parents[3]
    rel_path = cfg["paths"]["processed_data"]
    parquet_path = Path(rel_path) if Path(rel_path).is_absolute() else root / rel_path
    if not parquet_path.exists():
        raise FileNotFoundError(f"Reference dataset not found at '{parquet_path}'.")
    return pd.read_parquet(parquet_path)


def _load_feedback_from_db(feature_cols: list[str]) -> pd.DataFrame:
    """Query feedback rows that have a confirmed actual_valuation_usd.

    Falls back to an empty DataFrame if the DB is unavailable or the table
    does not yet exist.
    """
    try:
        from app.database import get_session, Prediction

        session = get_session()
        try:
            rows = (
                session.query(Prediction)
                .filter(Prediction.actual_valuation_usd.isnot(None))
                .all()
            )
            if not rows:
                return pd.DataFrame(columns=feature_cols)
            data = [
                {col: getattr(r, col, None) for col in feature_cols}
                for r in rows
            ]
            return pd.DataFrame(data)
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Could not query feedback from DB (%s). Returning empty frame.", exc)
        return pd.DataFrame(columns=feature_cols)


def detect_drift(cfg: dict[str, Any]) -> dict[str, Any]:
    """Run drift detection against confirmed feedback records.

    Parameters
    ----------
    cfg:
        Parsed ``config.yaml`` dict (see ``src.config.load_config``).

    Returns
    -------
    dict with keys:
        - ``drift_detected`` (bool)
        - ``n_feedback_samples`` (int)
        - ``features`` (dict per feature with ``ks_pvalue``,
          ``mean_drift_pct``, ``drifted`` keys)
        - ``timestamp`` (ISO string)
        - ``note`` (optional — ``"insufficient_data"`` when sample count is low)
    """
    ks_threshold: float = float(cfg["drift"]["ks_pvalue_threshold"])
    mean_pct_threshold: float = float(cfg["drift"]["mean_drift_pct_threshold"])

    feature_cols = DRIFT_FEATURES

    feedback_df = _load_feedback_from_db(feature_cols)
    n_feedback = len(feedback_df)

    timestamp = datetime.now(timezone.utc).isoformat()

    insufficient = n_feedback < MIN_FEEDBACK_SAMPLES
    report: dict[str, Any] = {
        "drift_detected": False,
        "n_feedback_samples": n_feedback,
        "features": {},
        "timestamp": timestamp,
    }

    if insufficient:
        report["note"] = "insufficient_data"
        _save_report(cfg, report)
        return report

    try:
        reference_df = _load_reference(cfg)
    except FileNotFoundError as exc:
        logger.warning("Reference dataset unavailable: %s. Skipping drift.", exc)
        report["note"] = "reference_not_found"
        _save_report(cfg, report)
        return report

    any_drift = False
    features_detail: dict[str, Any] = {}

    for feat in feature_cols:
        if feat not in reference_df.columns or feat not in feedback_df.columns:
            logger.debug("Feature '%s' not found in one of the datasets — skipping.", feat)
            continue

        ref_vals = reference_df[feat].dropna().values
        live_vals = feedback_df[feat].dropna().values

        if len(ref_vals) == 0 or len(live_vals) == 0:
            continue

        _, p_value = ks_2samp(ref_vals, live_vals)
        ref_mean = float(np.mean(ref_vals))
        live_mean = float(np.mean(live_vals))
        mean_drift_pct = (
            abs(live_mean - ref_mean) / abs(ref_mean) * 100.0
            if ref_mean != 0
            else 0.0
        )

        feature_drifted = p_value < ks_threshold or mean_drift_pct >= mean_pct_threshold
        if feature_drifted:
            any_drift = True

        features_detail[feat] = {
            "ks_pvalue": round(float(p_value), 6),
            "mean_drift_pct": round(mean_drift_pct, 4),
            "drifted": feature_drifted,
        }

    report["drift_detected"] = any_drift
    report["features"] = features_detail
    _save_report(cfg, report)
    return report


def _save_report(cfg: dict[str, Any], report: dict[str, Any]) -> None:
    """Serialise the drift report to ``{model_dir}/drift_report.json``."""
    try:
        root = Path(__file__).resolve().parents[3]
        model_dir = cfg["paths"].get("model_dir", "models")
        report_path = (
            Path(model_dir) if Path(model_dir).is_absolute() else root / model_dir
        ) / "drift_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Drift report saved to %s", report_path)
    except Exception as exc:
        logger.error("Could not save drift report: %s", exc)
