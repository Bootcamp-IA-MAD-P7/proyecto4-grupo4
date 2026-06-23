#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.evaluate import generate_report_assets
from src.models.train import save_artifacts, train_and_evaluate
from src.mlops.tuning import optimize_hyperparameters
from src.storage.db import save_metric_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el modelo de regresión.")
    parser.add_argument("--model", default=None, help="ridge | random_forest | gradient_boosting")
    parser.add_argument("--optimize", action="store_true", help="Optimiza hiperparámetros con Optuna")
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--report", action="store_true", help="Genera gráficos de evaluación")
    args = parser.parse_args()

    if args.optimize:
        result = optimize_hyperparameters(n_trials=args.trials)
        report = result["report"]
        print(json.dumps(result, indent=2, default=str))
    else:
        # [COMPATIBILIDAD] Si se escribe un modelo específico, solo corre ese
        if args.model is not None:
            print(f"🎯 Ejecución individual: Entrenando únicamente '{args.model}'...")
            trained = train_and_evaluate(args.model)
            save_artifacts(trained["pipeline"], trained["report"])
            report = trained["report"]
            print(json.dumps(report, indent=2))
        
        # [TU TAREA - INTEGRANTE 3] Comparación automática si NO se pasa un modelo
        else:
            print("🤖 Modo automático activado: Iniciando comparación de modelos...\n")
            models_to_compare = ["ridge", "random_forest", "gradient_boosting"]
            
            best_r2 = -float("inf")
            best_pipeline = None
            best_report = None
            best_model_name = None
            summary_results = {}

            # Bucle y evaluación de los 3 modelos
            for model_name in models_to_compare:
                print(f"🔄 Entrenando y evaluando: {model_name}...")
                trained = train_and_evaluate(model_name)
                
                r2_val = trained["report"]["validation"]["r2"]
                summary_results[model_name] = r2_val

                # Selección del ganador con mejor R²
                if r2_val > best_r2:
                    best_r2 = r2_val
                    best_pipeline = trained["pipeline"]
                    best_report = trained["report"]
                    best_model_name = model_name

            # Mostrar tabla limpia en la terminal
            print("\n" + "=" * 45)
            print(f"{'MODELO':<25} | {'R² VALIDACIÓN':<15}")
            print("=" * 45)
            for model, r2 in summary_results.items():
                print(f"{model:<25} | {r2:.4f}")
            print("=" * 45)
            print(f"🏆 GANADOR: {best_model_name.upper()} con R² = {best_r2:.4f}")
            print("=" * 45 + "\n")

            # Guardar artefactos del ganador para Streamlit
            print(f"💾 Guardando artefactos del ganador ({best_model_name})...")
            save_artifacts(best_pipeline, best_report)
            
            # Pasamos el reporte del ganador a la base de datos de abajo
            report = best_report

    # Guarda en la base de datos el resultado (del modelo individual o del ganador)
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
