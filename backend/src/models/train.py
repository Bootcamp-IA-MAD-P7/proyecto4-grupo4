from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from src.config import load_config, resolve_path
from src.data.load import load_processed_dataset, prepare_modeling_frame
from src.data.preprocess import build_preprocessor


@dataclass
class MetricsBundle:
    rmse: float
    mae: float
    r2: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


class LogTargetRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, estimator: BaseEstimator):
        self.estimator = estimator

    def fit(self, x, y):
        self.estimator_ = self.estimator
        self.estimator_.fit(x, np.log1p(y))
        return self

    def predict(self, x):
        return np.expm1(self.estimator_.predict(x))


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> MetricsBundle:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return MetricsBundle(rmse=rmse, mae=mae, r2=r2)


def overfitting_gap_pct(train_metric: float, val_metric: float, higher_is_better: bool = False) -> float:
    if higher_is_better:
        if val_metric >= train_metric:
            return 0.0
        if train_metric == 0:
            return 0.0
        return (train_metric - val_metric) / abs(train_metric) * 100.0

    if val_metric <= train_metric:
        return 0.0
    if train_metric == 0:
        return 0.0
    return (val_metric - train_metric) / abs(train_metric) * 100.0


def compute_overfitting_report(train_metrics: MetricsBundle, val_metrics: MetricsBundle) -> dict[str, float | bool]:
    config = load_config()
    mae_gap = overfitting_gap_pct(train_metrics.mae, val_metrics.mae)
    rmse_gap = overfitting_gap_pct(train_metrics.rmse, val_metrics.rmse)
    r2_gap = overfitting_gap_pct(train_metrics.r2, val_metrics.r2, higher_is_better=True)
    max_gap = max(mae_gap, rmse_gap, r2_gap)

    return {
        "mae_gap_pct": mae_gap,
        "rmse_gap_pct": rmse_gap,
        "r2_gap_pct": r2_gap,
        "max_gap_pct": max_gap,
        "within_limit": max_gap <= config["training"]["max_overfitting_pct"],
    }


def build_estimator(model_type: str | None = None, **params: Any) -> RegressorMixin:
    config = load_config()
    model_type = model_type or config["model"]["type"]

    if model_type == "ridge":
        return Ridge(alpha=params.get("alpha", config["model"].get("alpha", 1.0)))
    if model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=params.get("n_estimators", 120),
            max_depth=params.get("max_depth", 5),
            min_samples_leaf=params.get("min_samples_leaf", 12),
            random_state=config["project"]["random_state"],
            n_jobs=-1,
        )
    if model_type == "gradient_boosting":
        return GradientBoostingRegressor(
            n_estimators=params.get("n_estimators", 120),
            learning_rate=params.get("learning_rate", 0.05),
            max_depth=params.get("max_depth", 2),
            min_samples_leaf=params.get("min_samples_leaf", 20),
            subsample=params.get("subsample", 0.8),
            random_state=config["project"]["random_state"],
        )
    if model_type == "dummy":
        return DummyRegressor(strategy=params.get("strategy", "median"))
    raise ValueError(f"Modelo no soportado: {model_type}")


def build_pipeline(model_type: str | None = None, **params: Any) -> Pipeline | LogTargetRegressor:
    config = load_config()
    estimator = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", build_estimator(model_type, **params)),
        ]
    )
    if config["model"].get("log_target", True):
        return LogTargetRegressor(estimator)
    return estimator


def run_cross_validation(model, x, y) -> dict[str, float]:
    config = load_config()
    cv = KFold(
        n_splits=config["training"]["cv_folds"],
        shuffle=True,
        random_state=config["project"]["random_state"],
    )
    scores = cross_val_score(model, x, y, cv=cv, scoring="r2", n_jobs=-1)
    return {"cv_r2_mean": float(scores.mean()), "cv_r2_std": float(scores.std())}


def _evaluate_split(model, x_train, x_val, y_train, y_val) -> dict[str, Any]:
    train_pred = model.predict(x_train)
    val_pred = model.predict(x_val)

    train_metrics = compute_metrics(y_train.to_numpy(), train_pred)
    val_metrics = compute_metrics(y_val.to_numpy(), val_pred)
    overfitting = compute_overfitting_report(train_metrics, val_metrics)

    return {
        "train": train_metrics.to_dict(),
        "validation": val_metrics.to_dict(),
        "overfitting": overfitting,
    }


def _auto_select_params(model_type: str, x_train, x_val, y_train, y_val) -> tuple[dict[str, Any], Any]:
    candidates: list[dict[str, Any]] = []

    if model_type == "ridge":
        candidates.extend({"alpha": alpha} for alpha in [1.0, 10.0, 100.0, 500.0, 1000.0, 5000.0, 50000.0])
    elif model_type == "random_forest":
        candidates.extend(
            [
                {"n_estimators": 100, "max_depth": 3, "min_samples_leaf": 30},
                {"n_estimators": 120, "max_depth": 4, "min_samples_leaf": 25},
                {"n_estimators": 200, "max_depth": 5, "min_samples_leaf": 20},
            ]
        )
    elif model_type == "gradient_boosting":
        candidates.extend(
            [
                {"n_estimators": 60, "max_depth": 1, "min_samples_leaf": 80, "learning_rate": 0.05},
                {"n_estimators": 80, "max_depth": 2, "min_samples_leaf": 50, "learning_rate": 0.05},
                {"n_estimators": 120, "max_depth": 2, "min_samples_leaf": 30, "learning_rate": 0.03},
            ]
        )
    else:
        candidates.append({})

    candidates.extend(
        [
            {"model_type_override": "ridge", "alpha": 10000.0},
            {"model_type_override": "ridge", "alpha": 100000.0},
            {"model_type_override": "dummy", "strategy": "median"},
        ]
    )

    best_within_limit: tuple[dict[str, Any], Any, dict[str, Any]] | None = None
    best_fallback: tuple[dict[str, Any], Any, dict[str, Any]] | None = None

    for candidate in candidates:
        params = candidate.copy()
        selected_type = params.pop("model_type_override", model_type)
        model = build_pipeline(selected_type, **params)
        model.fit(x_train, y_train)
        evaluation = _evaluate_split(model, x_train, x_val, y_train, y_val)
        record = {"selected_type": selected_type, **params}

        if evaluation["overfitting"]["within_limit"]:
            if best_within_limit is None or evaluation["validation"]["r2"] > best_within_limit[2]["validation"]["r2"]:
                best_within_limit = (record, model, evaluation)
        elif best_fallback is None or evaluation["overfitting"]["max_gap_pct"] < best_fallback[2]["overfitting"]["max_gap_pct"]:
            best_fallback = (record, model, evaluation)

    chosen = best_within_limit or best_fallback
    assert chosen is not None
    return chosen[0], chosen[1]


def train_and_evaluate(model_type: str | None = None, **params: Any) -> dict[str, Any]:
    config = load_config()
    random_state = config["project"]["random_state"]
    model_type = model_type or config["model"]["type"]

    featured = load_processed_dataset()
    x, y = prepare_modeling_frame(featured)

    y_bins = pd.qcut(y, q=5, duplicates="drop")
    x_train, x_val, y_train, y_val = train_test_split(
        x,
        y,
        test_size=config["training"]["test_size"],
        random_state=random_state,
        stratify=y_bins,
    )

    if params:
        pipeline = build_pipeline(model_type, **params)
        pipeline.fit(x_train, y_train)
        evaluation = _evaluate_split(pipeline, x_train, x_val, y_train, y_val)
        selected_params = params
    else:
        selected_params, pipeline = _auto_select_params(model_type, x_train, x_val, y_train, y_val)
        evaluation = _evaluate_split(pipeline, x_train, x_val, y_train, y_val)

    cv_metrics = run_cross_validation(pipeline, x, y)

    report = {
        "model_type": selected_params.get("selected_type", model_type),
        "params": selected_params,
        "n_samples": int(len(x)),
        **evaluation,
        "cross_validation": cv_metrics,
    }
    return {"pipeline": pipeline, "report": report}


def save_artifacts(pipeline: Pipeline | LogTargetRegressor, report: dict[str, Any]) -> None:
    config = load_config()
    model_path = resolve_path(config["paths"]["model_file"])
    metrics_path = resolve_path(config["paths"]["metrics_file"])
    model_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def load_pipeline() -> Pipeline | LogTargetRegressor:
    config = load_config()
    model_path = resolve_path(config["paths"]["model_file"])
    return joblib.load(model_path)
