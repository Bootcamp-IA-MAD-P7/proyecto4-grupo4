"""K-Fold + Optuna hyperparameter search for the multiple-target model.

Target definition
-----------------
When ``training.target_transform == "multiple"`` (Phase-7 default):
    y_train = log1p(valuation_usd / funding_usd)

The pipeline is therefore a log-multiple predictor.  Inversion:
    multiple    = expm1(pipeline.predict(X))
    valuation   = multiple * funding_usd
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import optuna
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline

from src.config import load_config
from src.data.load import load_processed_dataset, prepare_modeling_frame
from src.data.preprocess import build_preprocessor

optuna.logging.set_verbosity(optuna.logging.WARNING)

logger = logging.getLogger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────


def _build_target(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.Series:
    """Return the training target according to ``target_transform``."""
    transform = cfg["training"].get("target_transform", "absolute")
    if transform == "multiple":
        raw_df = df if "valuation_usd" in df.columns else load_processed_dataset()
        y = np.log1p(raw_df["valuation_usd"] / raw_df["funding_usd"].clip(lower=1.0))
        return pd.Series(y.values, name="log_multiple")
    # fallback: classic log-valuation target
    target_col = cfg["project"]["target"]
    return pd.Series(np.log1p(df[target_col].values), name="log_valuation")


def _build_gb_pipeline(params: dict[str, Any], random_state: int) -> Pipeline:
    estimator = GradientBoostingRegressor(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        learning_rate=params["learning_rate"],
        subsample=params["subsample"],
        min_samples_split=params["min_samples_split"],
        random_state=random_state,
    )
    return Pipeline(steps=[("preprocessor", build_preprocessor()), ("model", estimator)])


# ── public API ─────────────────────────────────────────────────────────────


def run_optuna_kfold(
    df: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Run Optuna + K-Fold search and return the best result.

    Parameters
    ----------
    df:
        Fully-featured dataset (output of ``load_processed_dataset()``).
    cfg:
        Loaded ``config.yaml`` dict (via ``load_config()``).

    Returns
    -------
    dict with keys: ``best_params``, ``r2_mean``, ``r2_std``, ``trial_number``.
    """
    x, _ = prepare_modeling_frame(df)
    y = _build_target(df.loc[x.index], cfg)

    opt_cfg = cfg["optuna"]
    cv_folds: int = opt_cfg["cv_folds"]
    n_trials: int = opt_cfg["n_trials"]
    random_state: int = opt_cfg.get("random_state", cfg["project"]["random_state"])
    param_space: dict[str, list[float | int]] = opt_cfg["param_space"]

    kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)

    def objective(trial: optuna.Trial) -> float:
        params: dict[str, Any] = {
            "n_estimators": trial.suggest_int(
                "n_estimators", int(param_space["n_estimators"][0]), int(param_space["n_estimators"][1])
            ),
            "max_depth": trial.suggest_int(
                "max_depth", int(param_space["max_depth"][0]), int(param_space["max_depth"][1])
            ),
            "learning_rate": trial.suggest_float(
                "learning_rate", float(param_space["learning_rate"][0]), float(param_space["learning_rate"][1]), log=True
            ),
            "subsample": trial.suggest_float(
                "subsample", float(param_space["subsample"][0]), float(param_space["subsample"][1])
            ),
            "min_samples_split": trial.suggest_int(
                "min_samples_split",
                int(param_space["min_samples_split"][0]),
                int(param_space["min_samples_split"][1]),
            ),
        }

        pipeline = _build_gb_pipeline(params, random_state=random_state)

        fold_scores: list[float] = []
        x_arr = x.reset_index(drop=True)
        y_arr = y.reset_index(drop=True)

        for train_idx, val_idx in kfold.split(x_arr):
            clone_pipe = _build_gb_pipeline(params, random_state=random_state)
            clone_pipe.fit(x_arr.iloc[train_idx], y_arr.iloc[train_idx])
            y_pred = clone_pipe.predict(x_arr.iloc[val_idx])
            fold_scores.append(float(r2_score(y_arr.iloc[val_idx], y_pred)))

        del pipeline
        return float(np.mean(fold_scores))

    sampler = optuna.samplers.TPESampler(seed=random_state)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best_trial = study.best_trial
    best_params = best_trial.params

    # Recompute per-fold scores for the best params to get r2_std
    fold_scores_best: list[float] = []
    x_arr = x.reset_index(drop=True)
    y_arr = y.reset_index(drop=True)
    for train_idx, val_idx in kfold.split(x_arr):
        pipe = _build_gb_pipeline(best_params, random_state=random_state)
        pipe.fit(x_arr.iloc[train_idx], y_arr.iloc[train_idx])
        fold_scores_best.append(float(r2_score(y_arr.iloc[val_idx], pipe.predict(x_arr.iloc[val_idx]))))

    r2_mean = float(np.mean(fold_scores_best))
    r2_std = float(np.std(fold_scores_best))

    logger.info(
        "Optuna finished: best trial=%d  R²=%.4f ± %.4f  params=%s",
        best_trial.number,
        r2_mean,
        r2_std,
        best_params,
    )

    return {
        "best_params": best_params,
        "r2_mean": r2_mean,
        "r2_std": r2_std,
        "trial_number": best_trial.number,
    }


def predict_absolute(
    pipeline: Pipeline,
    X: pd.DataFrame,
    funding_usd_series: pd.Series,
    cfg: dict[str, Any],
) -> np.ndarray:
    """Invert the pipeline prediction to absolute ``valuation_usd``.

    Parameters
    ----------
    pipeline:
        Trained sklearn Pipeline whose last step predicts the log-transformed target.
    X:
        Feature matrix passed to ``pipeline.predict``.
    funding_usd_series:
        ``funding_usd`` column aligned with ``X`` (same index).
    cfg:
        Loaded ``config.yaml`` dict.

    Returns
    -------
    np.ndarray of predicted ``valuation_usd`` values in absolute dollars.
    """
    raw_log = pipeline.predict(X)
    transform = cfg["training"].get("target_transform", "absolute")

    if transform == "multiple":
        multiples = np.expm1(raw_log)
        return multiples * funding_usd_series.values
    # fallback: classic log-valuation
    return np.expm1(raw_log)
