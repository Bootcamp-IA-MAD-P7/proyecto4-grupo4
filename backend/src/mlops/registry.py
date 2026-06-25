"""Hooks para fases Expert: A/B testing, drift y auto-reemplazo de modelos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelCandidate:
    name: str
    version: str
    metrics: dict[str, float]


def should_promote_model(champion: ModelCandidate, challenger: ModelCandidate, min_r2_gain: float = 0.01) -> bool:
    return challenger.metrics["r2"] >= champion.metrics["r2"] + min_r2_gain


def detect_data_drift(reference_mean: float, live_mean: float, threshold_pct: float = 10.0) -> bool:
    if reference_mean == 0:
        return False
    drift_pct = abs(live_mean - reference_mean) / abs(reference_mean) * 100
    return drift_pct >= threshold_pct
