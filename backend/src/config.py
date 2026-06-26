from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or ROOT_DIR / "config.yaml"
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve_path(relative: str) -> Path:
    return ROOT_DIR / relative
