from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_parse_money():
    from src.data.load import parse_money

    assert parse_money("$180B") == 180_000_000_000
    assert parse_money("$572M") == 572_000_000
    assert parse_money("unknown") is None


def test_prepare_modeling_frame_has_rows():
    from src.data.load import build_features, load_raw_dataset, prepare_modeling_frame

    raw = load_raw_dataset()
    featured = build_features(raw)
    x, y = prepare_modeling_frame(featured)
    assert len(x) > 100
    assert len(x) == len(y)
    assert y.min() > 0


def test_train_meets_overfitting_limit():
    metrics_path = ROOT / "models" / "metrics.json"
    if not metrics_path.exists():
        pytest.skip("Modelo no entrenado todavía")

    report = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert report["overfitting"]["max_gap_pct"] <= 5.0


def test_train_meets_min_r2():
    metrics_path = ROOT / "models" / "metrics.json"
    if not metrics_path.exists():
        pytest.skip("Modelo no entrenado todavía")

    report = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert report["validation"]["r2"] >= 0.15
