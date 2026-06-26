#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
from src.data.load import build_and_save_processed_dataset, load_processed_dataset, prepare_modeling_frame
from src.models.evaluate import generate_report_assets
from src.models.train import predict_absolute, train_and_evaluate
from src.mlops.tuning import optimize_hyperparameters
from src.storage.db import save_metric_snapshot
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

STRESS_PLOT_PATH = resolve_path("reports/figures/residual_stress_plot.png")


def ensure_processed_dataset() -> None:
    processed_path = resolve_path(load_config()["paths"]["processed_data"])
    if not processed_path.exists():
        print(f"Building processed dataset at {processed_path}...")
        build_and_save_processed_dataset()


def log_target_training_message() -> None:
    cfg = load_config()
    if cfg["model"].get("log_target", True):
        print(
            "Target transform: np.log1p(valuation_usd) during training; "
            "metrics and API output in absolute USD via np.expm1."
        )
    else:
        print("WARNING: log_target disabled in config.yaml.")


def enforce_quality_gate(report: dict[str, Any], allow_low_r2_artifact: bool = False) -> None:
    cfg = load_config()
    min_r2 = cfg["training"]["min_r2"]
    val_r2 = report["validation"]["r2"]
    if val_r2 < min_r2:
        if allow_low_r2_artifact:
            print(
                f"[WARN] R²={val_r2:.4f} < threshold {min_r2}. "
                "Saving artifact for MVP runtime; CI gate remains unchanged."
            )
            return
        print(f"[FAIL] R²={val_r2:.4f} < threshold {min_r2}. Training rejected.")
        sys.exit(1)
    print(f"[OK] R²={val_r2:.4f} >= threshold {min_r2}. Model saved.")


def _validation_holdout() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    config = load_config()
    featured = load_processed_dataset()
    x, y = prepare_modeling_frame(featured)
    y_bins = pd.qcut(y, q=5, duplicates="drop")
    return train_test_split(
        x,
        y,
        test_size=config["training"]["test_size"],
        random_state=config["project"]["random_state"],
        stratify=y_bins,
    )


def plot_residual_stress(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> None:
    residuals = y_true - y_pred
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].scatter(y_pred / 1e9, residuals / 1e9, alpha=0.55, edgecolors="none")
    axes[0].axhline(0, color="red", linestyle="--", linewidth=1)
    z = np.polyfit(y_pred / 1e9, residuals / 1e9, 1)
    trend_x = np.linspace(y_pred.min() / 1e9, y_pred.max() / 1e9, 100)
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


def analyze_residual_pattern(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    residuals = y_true - y_pred
    pred_b = y_pred / 1e9
    resid_b = residuals / 1e9

    corr = float(np.corrcoef(pred_b, resid_b)[0, 1]) if len(pred_b) > 1 else 0.0
    slope, intercept = np.polyfit(pred_b, resid_b, 1)
    r2_val = float(r2_score(y_true, y_pred))

    abs_resid = np.abs(resid_b)
    low_pred = pred_b <= np.percentile(pred_b, 33)
    high_pred = pred_b >= np.percentile(pred_b, 67)
    hetero_ratio = float(abs_resid[high_pred].mean() / max(abs_resid[low_pred].mean(), 1e-9))

    if abs(corr) >= 0.25 or abs(slope) >= 0.15:
        verdict = "pattern"
        interpretation = (
            "Hay patrón sistemático: los residuos dependen de la predicción "
            "(tendencia lineal o sesgo por rango). Falta señal o transformación."
        )
    elif hetero_ratio >= 2.0:
        verdict = "pattern"
        interpretation = (
            "Hay patrón de heterocedasticidad: el error crece con la magnitud predicha. "
            "El modelo no captura bien la cola alta."
        )
    else:
        verdict = "random_cloud"
        interpretation = (
            "La nube de errores es aproximadamente aleatoria alrededor de cero. "
            "El modelo ya extrae la señal disponible; R²≈0.50 probablemente inalcanzable con estos datos."
        )

    return {
        "validation_r2": r2_val,
        "corr_prediction_error": corr,
        "residual_trend_slope": float(slope),
        "residual_trend_intercept": float(intercept),
        "heteroscedasticity_ratio": hetero_ratio,
        "verdict": verdict,
        "interpretation": interpretation,
    }


def run_stress_test() -> dict[str, Any]:
    print("🔬 Stress test: entrenamiento diagnóstico (sin guardar artefactos)\n")
    models_to_compare = [
        ("gradient_boosting", {"n_estimators": 120, "max_depth": 2, "min_samples_leaf": 30, "learning_rate": 0.03}),
        ("ridge", {}),
        ("random_forest", {}),
    ]

    best_name = None
    best_pipeline = None
    best_report = None
    best_r2 = -float("inf")
    summary: dict[str, float] = {}

    for model_name, params in models_to_compare:
        print(f"🔄 Evaluando: {model_name}...")
        trained = train_and_evaluate(model_name, **params)
        r2_val = trained["report"]["validation"]["r2"]
        summary[model_name] = r2_val
        if r2_val > best_r2:
            best_r2 = r2_val
            best_name = model_name
            best_pipeline = trained["pipeline"]
            best_report = trained["report"]

    x_train, x_val, y_train, y_val = _validation_holdout()
    y_pred = predict_absolute(best_pipeline, x_val)
    analysis = analyze_residual_pattern(y_val.to_numpy(), y_pred)
    plot_residual_stress(y_val.to_numpy(), y_pred, STRESS_PLOT_PATH)

    print("\n" + "=" * 45)
    print(f"{'MODELO':<25} | {'R² VALIDACIÓN':<15}")
    print("=" * 45)
    for model, r2 in summary.items():
        marker = " ← diagnóstico" if model == best_name else ""
        print(f"{model:<25} | {r2:.4f}{marker}")
    print("=" * 45)
    print(f"Modelo usado para residual plot: {best_name.upper()} (R²={best_r2:.4f})\n")

    print("--- Residual Plot Analysis ---")
    print(f"  R² validación:              {analysis['validation_r2']:.4f}")
    print(f"  corr(predicción, error):    {analysis['corr_prediction_error']:+.4f}")
    print(f"  pendiente tendencia error:  {analysis['residual_trend_slope']:+.4f} B USD / B USD predicho")
    print(f"  ratio heterocedasticidad:   {analysis['heteroscedasticity_ratio']:.2f}x")
    print(f"  Veredicto:                  {analysis['verdict'].upper()}")
    print(f"  {analysis['interpretation']}")
    print(f"\n  Gráfico guardado en: {STRESS_PLOT_PATH}")

    return {
        "best_model": best_name,
        "summary": summary,
        "report": best_report,
        "analysis": analysis,
        "plot_path": str(STRESS_PLOT_PATH),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el modelo de regresión.")
    parser.add_argument("--model", default=None, help="ridge | random_forest | gradient_boosting")
    parser.add_argument("--optimize", action="store_true", help="Optimiza hiperparámetros con Optuna")
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--report", action="store_true", help="Genera gráficos de evaluación")
    parser.add_argument(
        "--allow-low-r2-artifact",
        action="store_true",
        help="Guarda artefactos aunque no superen min_r2. Usar solo para runtime MVP/Docker.",
    )
    parser.add_argument(
        "--stress-test",
        action="store_true",
        help="Entrena, genera Residual Plot y analiza patrón sin guardar el modelo",
    )
    args = parser.parse_args()

    ensure_processed_dataset()
    log_target_training_message()

    if args.stress_test:
        run_stress_test()
        print("\n[STRESS TEST] Artefactos NO guardados (diagnóstico only).")
        return

    from src.models.train import save_artifacts

    if args.optimize:
        result = optimize_hyperparameters(n_trials=args.trials)
        report = result["report"]
        print(json.dumps(result, indent=2, default=str))
        enforce_quality_gate(report, allow_low_r2_artifact=args.allow_low_r2_artifact)
        save_artifacts(result["pipeline"], report)
    else:
        if args.model is not None:
            print(f"🎯 Ejecución individual: Entrenando únicamente '{args.model}'...")
            trained = train_and_evaluate(args.model)
            enforce_quality_gate(trained["report"], allow_low_r2_artifact=args.allow_low_r2_artifact)
            save_artifacts(trained["pipeline"], trained["report"])
            report = trained["report"]
            print(json.dumps(report, indent=2))
        else:
            print("🤖 Modo automático activado: Iniciando comparación de modelos...\n")
            models_to_compare = ["ridge", "random_forest", "gradient_boosting"]

            best_r2 = -float("inf")
            best_pipeline = None
            best_report = None
            best_model_name = None
            summary_results = {}

            for model_name in models_to_compare:
                print(f"🔄 Entrenando y evaluando: {model_name}...")
                trained = train_and_evaluate(model_name)

                r2_val = trained["report"]["validation"]["r2"]
                summary_results[model_name] = r2_val

                if r2_val > best_r2:
                    best_r2 = r2_val
                    best_pipeline = trained["pipeline"]
                    best_report = trained["report"]
                    best_model_name = model_name

            print("\n" + "=" * 45)
            print(f"{'MODELO':<25} | {'R² VALIDACIÓN':<15}")
            print("=" * 45)
            for model, r2 in summary_results.items():
                print(f"{model:<25} | {r2:.4f}")
            print("=" * 45)
            print(f"🏆 GANADOR: {best_model_name.upper()} con R² = {best_r2:.4f}")
            print("=" * 45 + "\n")

            print(f"💾 Guardando artefactos del ganador ({best_model_name})...")
            enforce_quality_gate(best_report, allow_low_r2_artifact=args.allow_low_r2_artifact)
            save_artifacts(best_pipeline, best_report)

            report = best_report

    save_metric_snapshot(
        model_version=report["model_type"],
        metrics=report["validation"],
        is_champion=report["overfitting"]["within_limit"],
    )

    if not report["overfitting"]["within_limit"]:
        print(
            f"WARNING: overfitting max gap {report['overfitting']['max_gap_pct']:.2f}% "
            f"supera el límite configurado.",
            file=sys.stderr,
        )

    if args.report:
        assets = generate_report_assets()
        print(json.dumps(assets, indent=2))


if __name__ == "__main__":
    main()
