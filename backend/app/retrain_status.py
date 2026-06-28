"""In-memory retrain job status for MLOps dashboard polling."""
from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

DECISION_MESSAGES: dict[str, str] = {
    "promoted": (
        "Modelo promovido a producción (R² {current_r2:.4f} → {new_r2:.4f}). "
        "La API ya sirve el nuevo modelo — no hace falta reiniciar contenedores."
    ),
    "candidate": (
        "Nuevo modelo guardado como candidato A/B (R² {current_r2:.4f} → {new_r2:.4f}, "
        "gap={overfitting_gap:.4f}). Producción intacta; ~20% del tráfico usará el candidato."
    ),
    "discarded": (
        "Candidato descartado (R² nuevo {new_r2:.4f} ≤ producción {current_r2:.4f}). "
        "El modelo en producción no cambió."
    ),
    "skipped": "Entrenamiento completado. No había candidato que evaluar (primer modelo o sin prod).",
}

PHASE_MESSAGES: dict[str, str] = {
    "drift": "Comprobando drift en datos de feedback…",
    "training": "Entrenando con Optuna + K-Fold (puede tardar 2–5 min)…",
    "reload": "Recargando modelos en memoria de la API…",
}

_status: dict[str, Any] = {
    "status": "idle",
    "phase": None,
    "message": "Sin reentrenamientos recientes.",
    "started_at": None,
    "finished_at": None,
    "decision": None,
    "details": {},
    "error": None,
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_status() -> dict[str, Any]:
    return deepcopy(_status)


def is_running() -> bool:
    return _status["status"] == "running"


def mark_started() -> None:
    _status.update(
        {
            "status": "running",
            "phase": "drift",
            "message": PHASE_MESSAGES["drift"],
            "started_at": _now_iso(),
            "finished_at": None,
            "decision": None,
            "details": {},
            "error": None,
        }
    )


def set_phase(phase: str, *, extra: dict[str, Any] | None = None) -> None:
    _status["phase"] = phase
    _status["message"] = PHASE_MESSAGES.get(phase, phase)
    if extra:
        _status["details"] = {**_status.get("details", {}), **extra}


def mark_completed(
    *,
    decision: str | None,
    replacement: dict[str, Any] | None = None,
    drift_detected: bool | None = None,
    model_reloaded: bool = True,
) -> None:
    details: dict[str, Any] = dict(_status.get("details") or {})
    if replacement:
        details.update(
            {
                "current_r2": replacement.get("current_r2"),
                "new_r2": replacement.get("new_r2"),
                "overfitting_gap": replacement.get("overfitting_gap"),
                "archive_dir": replacement.get("archive_dir"),
            }
        )
    if drift_detected is not None:
        details["drift_detected"] = drift_detected
    details["model_reloaded"] = model_reloaded
    details["requires_container_restart"] = False

    message = DECISION_MESSAGES.get(decision or "skipped", DECISION_MESSAGES["skipped"])
    if replacement and decision in {"promoted", "candidate", "discarded"}:
        try:
            message = message.format(
                current_r2=replacement.get("current_r2") or 0.0,
                new_r2=replacement.get("new_r2") or 0.0,
                overfitting_gap=replacement.get("overfitting_gap") or 0.0,
            )
        except (KeyError, TypeError, ValueError):
            pass

    _status.update(
        {
            "status": "completed",
            "phase": None,
            "message": message,
            "finished_at": _now_iso(),
            "decision": decision,
            "details": details,
            "error": None,
        }
    )


def mark_failed(error: str) -> None:
    _status.update(
        {
            "status": "failed",
            "phase": None,
            "message": "El reentrenamiento falló. Revisa los logs del backend.",
            "finished_at": _now_iso(),
            "error": error,
        }
    )
