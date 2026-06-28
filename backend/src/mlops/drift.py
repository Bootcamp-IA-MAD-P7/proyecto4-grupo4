"""Data-drift detection utilities (Phase-7, used by T-7.7).

Placeholder module created in T-7.3 so the import path is resolvable.
Full implementation (KS-test + mean-drift) is added in T-7.7.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.config import load_config


def detect_drift(
    reference: pd.DataFrame,
    live: pd.DataFrame,
    feature_cols: list[str] | None = None,
) -> dict[str, Any]:
    """Detect distributional drift between a reference and live dataset.

    Uses the two-sample Kolmogorov-Smirnov test and mean-percentage difference
    per numeric feature.  Thresholds are read from ``config.yaml`` (``drift``
    section).

    Parameters
    ----------
    reference:
        Training / baseline dataset.
    live:
        Current inference payload dataset.
    feature_cols:
        Numeric columns to compare.  Defaults to all shared numeric columns.

    Returns
    -------
    dict with keys ``drifted_features``, ``ks_results``, ``mean_drift_results``,
    and ``any_drift`` (bool).
    """
    cfg = load_config()
    ks_threshold: float = cfg["drift"]["ks_pvalue_threshold"]
    mean_pct_threshold: float = cfg["drift"]["mean_drift_pct_threshold"]

    if feature_cols is None:
        num_cols = reference.select_dtypes(include=[np.number]).columns
        feature_cols = [c for c in num_cols if c in live.columns]

    ks_results: dict[str, float] = {}
    mean_drift_results: dict[str, float] = {}
    drifted_features: list[str] = []

    for col in feature_cols:
        ref_vals = reference[col].dropna().values
        live_vals = live[col].dropna().values
        if len(ref_vals) == 0 or len(live_vals) == 0:
            continue

        ks_stat, p_value = stats.ks_2samp(ref_vals, live_vals)
        ks_results[col] = float(p_value)

        ref_mean = float(np.mean(ref_vals))
        live_mean = float(np.mean(live_vals))
        if ref_mean != 0:
            mean_drift_pct = abs(live_mean - ref_mean) / abs(ref_mean) * 100.0
        else:
            mean_drift_pct = 0.0
        mean_drift_results[col] = round(mean_drift_pct, 4)

        if p_value < ks_threshold or mean_drift_pct >= mean_pct_threshold:
            drifted_features.append(col)

    return {
        "drifted_features": drifted_features,
        "ks_results": ks_results,
        "mean_drift_results": mean_drift_results,
        "any_drift": len(drifted_features) > 0,
    }
