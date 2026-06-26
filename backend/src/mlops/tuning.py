from __future__ import annotations

from typing import Any

import optuna
from sklearn.model_selection import cross_val_score

from src.config import load_config
from src.data.load import load_processed_dataset, prepare_modeling_frame
from src.models.train import build_pipeline, train_and_evaluate


def optimize_hyperparameters(n_trials: int = 30) -> dict[str, Any]:
    config = load_config()
    featured = load_processed_dataset()
    x, y = prepare_modeling_frame(featured)

    def objective(trial: optuna.Trial) -> float:
        model_type = trial.suggest_categorical("model_type", ["ridge", "random_forest", "gradient_boosting"])
        params: dict[str, Any] = {}

        if model_type == "ridge":
            params["alpha"] = trial.suggest_float("alpha", 0.1, 100.0, log=True)
        elif model_type == "random_forest":
            params["n_estimators"] = trial.suggest_int("n_estimators", 100, 400)
            params["max_depth"] = trial.suggest_int("max_depth", 3, 12)
            params["min_samples_leaf"] = trial.suggest_int("min_samples_leaf", 2, 10)
        else:
            params["n_estimators"] = trial.suggest_int("gb_n_estimators", 80, 250)
            params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.2, log=True)
            params["max_depth"] = trial.suggest_int("gb_max_depth", 2, 5)

        pipeline = build_pipeline(model_type, **params)
        scores = cross_val_score(
            pipeline,
            x,
            y,
            cv=config["training"]["cv_folds"],
            scoring="neg_root_mean_squared_error",
            n_jobs=-1,
        )
        return float(scores.mean())

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best = study.best_params
    model_type = best.pop("model_type")
    result = train_and_evaluate(model_type, **best)

    return {
        "best_params": study.best_params,
        "best_value": study.best_value,
        "pipeline": result["pipeline"],
        "report": result["report"],
    }
