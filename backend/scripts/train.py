#!/usr/bin/env python3
"""Main training script.

Phase-7 flow
------------
1. Load processed dataset.
2. Run Optuna K-Fold search via ``run_optuna_kfold(df, cfg)`` from
   ``src.mlops.tuning``.  Target is ``log1p(valuation_usd / funding_usd)``
   when ``training.target_transform == "multiple"``.
3. Build the final pipeline with the best hyper-parameters and fit it on
   the full training split.
4. Evaluate on a held-out validation split.
5. Persist artefacts:
   - If ``best_model.joblib`` does NOT exist  → save as production model.
   - If ``best_model.joblib`` already exists  → save as ``candidate_model.joblib``
     (A/B candidate; the auto-replacement gate runs in a later MLOps step).
6. Enforce the quality gate:
   - Hard gate: ``val_r2 < min_r2``  → ``sys.exit(1)``.
   - Soft gate: ``overfitting_gap >= max_overfitting_gap`` → warn only.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_config, resolve_path
from src.data.load import (
    build_and_save_processed_dataset,
    load_processed_dataset,
    prepare_modeling_frame,
)
from src.mlops.tuning import _build_gb_pipeline, predict_absolute, run_optuna_kfold
from src.models.evaluate import generate_report_assets
from src.models.train import (
    compute_metrics,
    load_pipeline,
)
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
import joblib

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

STRESS_PLOT_PATH = resolve_path("reports/figures/residual_stress_plot.png")


# ── dataset helpers ────────────────────────────────────────────────────────


def ensure_processed_dataset() -> None:
    processed_path = resolve_path(load_config()["paths"]["processed_data"])
    if not processed_path.exists():
        print(f"Building processed dataset at {processed_path}...")
        build_and_save_processed_dataset()


def log_target_training_message() -> None:
    cfg = load_config()
    transform = cfg["training"].get("target_transform", "absolute")
    if transform == "multiple":
        print("Target transform: log1p(valuation_usd / funding_usd). API reconverts via expm1 * funding_usd.")
    else:
        print("Target transform: log1p(valuation_usd). API reconverts via expm1.")


# ── artifact saving ────────────────────────────────────────────────────────


def _model_dir() -> Path:
    cfg = load_config()
    path = resolve_path(cfg["paths"]["model_dir"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_artifacts(
    pipeline: Any,
    report: dict[str, Any],
    *,
    force_production: bool = False,
) -> str:
    """Persist the trained pipeline and metrics.

    Returns the role under which the model was saved: ``"production"`` or
    ``"candidate"``.
    """
    cfg = load_config()
    model_dir = _model_dir()
    best_path = model_dir / "best_model.joblib"
    candidate_path = model_dir / "candidate_model.joblib"
    metrics_path = resolve_path(cfg["paths"]["metrics_file"])

    if best_path.exists() and not force_production:
        joblib.dump(pipeline, candidate_path)
        role = "candidate"
        logger.info("Production model already exists. Saved new model as candidate: %s", candidate_path)
        print(f"[INFO] Saved as CANDIDATE model (A/B): {candidate_path}")
    else:
        joblib.dump(pipeline, best_path)
        role = "production"
        logger.info("Saved as production model: %s", best_path)
        print(f"[INFO] Saved as PRODUCTION model: {best_path}")

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return role


# ── quality gate ───────────────────────────────────────────────────────────


def enforce_quality_gate(
    metrics: dict[str, Any],
    *,
    allow_low_r2_artifact: bool = False,
) -> None:
    """Hard gate on val R² and soft gate on overfitting gap."""
    cfg = load_config()
    min_r2 = cfg["training"]["min_r2"]
    max_gap = cfg["training"]["max_overfitting_gap"]

    val_r2: float = metrics["validation"]["r2_mean"]
    gap: float = metrics.get("overfitting_gap", 0.0)

    if val_r2 < min_r2:
        if allow_low_r2_artifact:
            print(
                f"[WARN] R²={val_r2:.4f} < threshold {min_r2}. "
                "Saving artifact for MVP runtime; CI gate remains unchanged."
            )
            return
        print(f"[FAIL] R²={val_r2:.4f} < threshold {min_r2}. Training rejected.")
        sys.exit(1)

    print(f"[OK] R²={val_r2:.4f} >= threshold {min_r2}.")

    if gap >= max_gap:
        print(
            f"[WARN] Overfitting alto (gap={gap:.3f} >= {max_gap}). "
            "Modelo guardado como candidato A/B."
        )
    else:
        print(f"[OK] Overfitting gap={gap:.3f} within limit {max_gap}.")


# ── training ───────────────────────────────────────────────────────────────


def _build_target_series(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.Series:
    """Return the training target series aligned with ``df``."""
    transform = cfg["training"].get("target_transform", "absolute")
    if transform == "multiple":
        y = np.log1p(df["valuation_usd"] / df["funding_usd"].clip(lower=1.0))
        return pd.Series(y.values, index=df.index, name="log_multiple")
    target_col = cfg["project"]["target"]
    return pd.Series(np.log1p(df[target_col].values), index=df.index, name="log_valuation")


def _validation_holdout(
    df: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    x, _y_raw = prepare_modeling_frame(df)
    y = _build_target_series(df.loc[x.index], cfg)

    y_bins = pd.qcut(y, q=5, duplicates="drop")
    return train_test_split(
        x,
        y,
        test_size=cfg["training"]["test_size"],
        random_state=cfg["project"]["random_state"],
        stratify=y_bins,
    )


def run_optuna_training(
    df: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    allow_low_r2_artifact: bool = False,
) -> dict[str, Any]:
    """Run Optuna K-Fold and build the final pipeline."""
    print(f"\n[Optuna] Starting search (n_trials={cfg['optuna']['n_trials']}, cv_folds={cfg['optuna']['cv_folds']})...")
    optuna_result = run_optuna_kfold(df, cfg)

    best_params: dict[str, Any] = optuna_result["best_params"]
    r2_mean: float = optuna_result["r2_mean"]
    r2_std: float = optuna_result["r2_std"]
    trial_number: int = optuna_result["trial_number"]

    print(
        f"[Optuna] Best trial #{trial_number}: R²={r2_mean:.4f} ± {r2_std:.4f}  params={best_params}"
    )

    random_state = cfg["project"]["random_state"]
    x_train, x_val, y_train, y_val = _validation_holdout(df, cfg)

    # Fit the final pipeline on the training split with the best hyper-params
    final_pipeline = _build_gb_pipeline(best_params, random_state=random_state)
    final_pipeline.fit(x_train, y_train)

    # Evaluate on both splits (predictions are still in log-space)
    train_r2 = float(r2_score(y_train, final_pipeline.predict(x_train)))
    val_r2 = float(r2_score(y_val, final_pipeline.predict(x_val)))
    overfitting_gap = max(0.0, train_r2 - val_r2)

    metrics = {
        "target": cfg["training"].get("target_transform", "absolute"),
        "cv_folds": cfg["optuna"]["cv_folds"],
        "optuna_trials": cfg["optuna"]["n_trials"],
        "best_trial_number": trial_number,
        "best_params": best_params,
        "validation": {
            "r2_mean": r2_mean,
            "r2_std": r2_std,
            "r2_train_split": train_r2,
            "r2_val_split": val_r2,
        },
        "overfitting_gap": overfitting_gap,
    }

    return {"pipeline": final_pipeline, "metrics": metrics}


# ── residual stress analysis ───────────────────────────────────────────────


def plot_residual_stress(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> None:
    residuals = y_true - y_pred
    pred_b = y_pred / 1e9
    resid_b = residuals / 1e9
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].scatter(pred_b, resid_b, alpha=0.55, edgecolors="none")
    axes[0].axhline(0, color="red", linestyle="--", linewidth=1)
    z = np.polyfit(pred_b, resid_b, 1)
    trend_x = np.linspace(pred_b.min(), pred_b.max(), 100)
    axes[0].plot(trend_x, np.poly1d(z)(trend_x), color="orange", linewidth=2, label="Tendencia lineal")
    axes[0].set_xlabel("Predicción (B USD)")
    axes[0].set_ylabel("Error / Residuo (B USD)")
    axes[0].set_title("Residual Plot: Predicción vs Error")
    axes[0].legend()

    axes[1].scatter(y_true / 1e9, y_pred / 1e9, alpha=0.55, edgecolors="none")
    max_val = max(y_true.max(), y_pred.max()) / 1e9
    axes[1].plot([0, max_val], [0, max_val], "--", color="red", linewidth=1)
    axes[1].set_xlabel("Valor real (B USD)")
    axes[1].set_ylabel("Predicción (B USD)")
    axes[1].set_title("Predicción vs Real")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


# ── entry point ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el modelo de regresión (Phase-7 MLOps).")
    parser.add_argument("--report", action="store_true", help="Genera gráficos de evaluación")
    parser.add_argument(
        "--allow-low-r2-artifact",
        action="store_true",
        help="Guarda artefactos aunque no superen min_r2. Usar solo para runtime MVP/Docker.",
    )
    parser.add_argument(
        "--force-production",
        action="store_true",
        help="Guarda directamente como best_model.joblib aunque ya exista uno.",
    )
    args = parser.parse_args()

    ensure_processed_dataset()
    log_target_training_message()

    cfg = load_config()
    df = load_processed_dataset()

    result = run_optuna_training(df, cfg, allow_low_r2_artifact=args.allow_low_r2_artifact)

    enforce_quality_gate(result["metrics"], allow_low_r2_artifact=args.allow_low_r2_artifact)

    role = save_artifacts(result["pipeline"], result["metrics"], force_production=args.force_production)

    print(f"\n[DONE] Model saved as: {role.upper()}")
    print(json.dumps(result["metrics"], indent=2))

    if args.report:
        assets = generate_report_assets()
        print(json.dumps(assets, indent=2))


if __name__ == "__main__":
    main()
