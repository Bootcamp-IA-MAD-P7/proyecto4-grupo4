"""Auto-replacement gate for retrained models — Phase 7 (T-7.13).

Implements CASO A/B/C from ``2_spec.md §3.1.5`` after a candidate model is
trained and saved as ``candidate_model.joblib`` + ``metrics_candidate.json``.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import resolve_path

logger = logging.getLogger(__name__)

CANDIDATE_METRICS_FILE = "metrics_candidate.json"


def _validation_r2(metrics: dict[str, Any]) -> float:
    validation = metrics.get("validation", {})
    value = validation.get("r2_mean", validation.get("r2"))
    if value is None:
        raise KeyError("validation r2_mean missing from metrics payload")
    return float(value)


def _train_r2(metrics: dict[str, Any]) -> float:
    validation = metrics.get("validation", {})
    if "r2_train_split" in validation:
        return float(validation["r2_train_split"])
    train = metrics.get("train", {})
    if "r2" in train:
        return float(train["r2"])
    raise KeyError("train r2 missing from metrics payload")


def _overfitting_gap(metrics: dict[str, Any]) -> float:
    if "overfitting_gap" in metrics:
        return max(0.0, float(metrics["overfitting_gap"]))
    return max(0.0, _train_r2(metrics) - _validation_r2(metrics))


def decide_replacement(
    prod_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    *,
    max_overfitting_gap: float = 0.05,
) -> str:
    """Return ``promoted``, ``candidate`` or ``discarded``."""
    current_r2 = _validation_r2(prod_metrics)
    new_r2 = _validation_r2(candidate_metrics)
    gap = _overfitting_gap(candidate_metrics)

    if new_r2 <= current_r2:
        return "discarded"
    if gap >= max_overfitting_gap:
        return "candidate"
    return "promoted"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _archive_production(
    model_dir: Path,
    best_path: Path,
    metrics_path: Path,
) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = model_dir / "archive" / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    if best_path.exists():
        shutil.copy2(best_path, archive_dir / "best_model.joblib")
    if metrics_path.exists():
        shutil.copy2(metrics_path, archive_dir / "metrics.json")
    return archive_dir


def apply_auto_replacement(
    cfg: dict[str, Any],
    *,
    model_dir: Path | None = None,
) -> dict[str, Any]:
    """Apply CASO A/B/C to a freshly trained candidate model.

    Returns a structured report with ``decision`` in
    ``promoted | candidate | discarded | skipped``.
    """
    resolved_dir = model_dir or resolve_path(cfg["paths"]["model_dir"])
    resolved_dir.mkdir(parents=True, exist_ok=True)

    best_path = resolved_dir / "best_model.joblib"
    candidate_path = resolved_dir / "candidate_model.joblib"
    metrics_path = resolved_dir / Path(cfg["paths"]["metrics_file"]).name
    candidate_metrics_path = resolved_dir / CANDIDATE_METRICS_FILE
    max_gap = float(cfg["training"].get("max_overfitting_gap", 0.05))

    report: dict[str, Any] = {
        "decision": "skipped",
        "current_r2": None,
        "new_r2": None,
        "overfitting_gap": None,
        "archive_dir": None,
    }

    if not best_path.exists():
        report["reason"] = "no_production_model"
        return report

    if not candidate_path.exists() or not candidate_metrics_path.exists():
        report["reason"] = "no_candidate_artifacts"
        return report

    prod_metrics = _load_json(metrics_path)
    candidate_metrics = _load_json(candidate_metrics_path)

    current_r2 = _validation_r2(prod_metrics)
    new_r2 = _validation_r2(candidate_metrics)
    gap = _overfitting_gap(candidate_metrics)
    decision = decide_replacement(
        prod_metrics,
        candidate_metrics,
        max_overfitting_gap=max_gap,
    )

    report.update(
        {
            "decision": decision,
            "current_r2": current_r2,
            "new_r2": new_r2,
            "overfitting_gap": gap,
        }
    )

    if decision == "promoted":
        archive_dir = _archive_production(model_dir=resolved_dir, best_path=best_path, metrics_path=metrics_path)
        shutil.copy2(candidate_path, best_path)
        metrics_path.write_text(json.dumps(candidate_metrics, indent=2), encoding="utf-8")
        candidate_path.unlink(missing_ok=True)
        candidate_metrics_path.unlink(missing_ok=True)
        report["archive_dir"] = str(archive_dir)
        logger.info(
            "Model promoted (R²: %.4f → %.4f, gap=%.4f). Backup at %s",
            current_r2,
            new_r2,
            gap,
            archive_dir,
        )
        print(
            f"[INFO] Modelo reemplazado (R²: {current_r2:.4f} → {new_r2:.4f}). "
            f"Backup: {archive_dir}"
        )
    elif decision == "candidate":
        logger.info(
            "Candidate kept for A/B testing (R²: %.4f → %.4f, overfitting gap=%.4f >= %.4f).",
            current_r2,
            new_r2,
            gap,
            max_gap,
        )
        print(
            f"[INFO] Candidato A/B (overfitting={gap:.4f} >= {max_gap:.4f}). "
            f"R²: {current_r2:.4f} → {new_r2:.4f}"
        )
    else:
        candidate_path.unlink(missing_ok=True)
        candidate_metrics_path.unlink(missing_ok=True)
        logger.info(
            "Candidate discarded (R²: %.4f <= prod %.4f). Production model unchanged.",
            new_r2,
            current_r2,
        )
        print(f"[INFO] Candidato descartado (R²: {new_r2:.4f} <= {current_r2:.4f}).")

    return report
