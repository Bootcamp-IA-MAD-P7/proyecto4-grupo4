from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.inspection import permutation_importance

from src.config import load_config, resolve_path
from src.data.load import build_features, load_raw_dataset, prepare_modeling_frame
from src.models.train import compute_metrics, load_pipeline


def load_metrics_report() -> dict:
    config = load_config()
    metrics_path = resolve_path(config["paths"]["metrics_file"])
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def plot_target_distribution(y: pd.Series, output_path: Path) -> None:
    plt.figure(figsize=(8, 5))
    sns.histplot(y / 1e9, bins=30, kde=True)
    plt.xlabel("Valuation (billions USD)")
    plt.ylabel("Count")
    plt.title("Distribución de la variable objetivo")
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()


def plot_predictions_vs_actual(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> None:
    plt.figure(figsize=(7, 7))
    plt.scatter(y_true / 1e9, y_pred / 1e9, alpha=0.6)
    max_val = max(y_true.max(), y_pred.max()) / 1e9
    plt.plot([0, max_val], [0, max_val], "--", color="red")
    plt.xlabel("Valor real (B USD)")
    plt.ylabel("Predicción (B USD)")
    plt.title("Predicción vs Real")
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> None:
    residuals = y_true - y_pred
    plt.figure(figsize=(8, 5))
    sns.scatterplot(x=y_pred / 1e9, y=residuals / 1e9, alpha=0.6)
    plt.axhline(0, color="red", linestyle="--")
    plt.xlabel("Predicción (B USD)")
    plt.ylabel("Residuo (B USD)")
    plt.title("Análisis de residuos")
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()


def generate_report_assets(output_dir: Path | None = None) -> dict:
    config = load_config()
    output_dir = output_dir or resolve_path("reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = load_raw_dataset()
    featured = build_features(raw)
    x, y = prepare_modeling_frame(featured)
    pipeline = load_pipeline()
    predictions = pipeline.predict(x)

    metrics = compute_metrics(y.to_numpy(), predictions)
    plot_target_distribution(y, output_dir / "target_distribution.png")
    plot_predictions_vs_actual(y.to_numpy(), predictions, output_dir / "pred_vs_actual.png")
    plot_residuals(y.to_numpy(), predictions, output_dir / "residuals.png")

    perm = permutation_importance(
        pipeline,
        x,
        y,
        n_repeats=10,
        random_state=config["project"]["random_state"],
        n_jobs=-1,
    )
    importance_df = pd.DataFrame(
        {"feature": x.columns, "importance": perm.importances_mean}
    ).sort_values("importance", ascending=False)

    top = importance_df.head(15)
    plt.figure(figsize=(9, 6))
    sns.barplot(data=top, x="importance", y="feature")
    plt.title("Permutation importance (top 15)")
    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance.png", dpi=120)
    plt.close()

    return {
        "metrics_full_dataset": metrics.to_dict(),
        "top_features": top.to_dict(orient="records"),
        "artifacts": [
            str(output_dir / "target_distribution.png"),
            str(output_dir / "pred_vs_actual.png"),
            str(output_dir / "residuals.png"),
            str(output_dir / "feature_importance.png"),
        ],
    }
