import os
import sqlite3
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "feedback" / "predictions.sqlite3"


def get_db_path() -> Path:
    return Path(os.getenv("APP_DB_PATH", DEFAULT_DB_PATH))


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path | None = None) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                request_id TEXT PRIMARY KEY,
                country TEXT NOT NULL,
                city TEXT NOT NULL,
                industry TEXT NOT NULL,
                join_year INTEGER NOT NULL,
                join_month INTEGER NOT NULL,
                investor_count INTEGER NOT NULL,
                prediction_billion_usd REAL NOT NULL,
                model_used TEXT NOT NULL,
                feedback_score INTEGER,
                actual_valuation_b REAL,
                comments TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def save_prediction(record: dict[str, Any], db_path: Path | None = None) -> None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO predictions (
                request_id,
                country,
                city,
                industry,
                join_year,
                join_month,
                investor_count,
                prediction_billion_usd,
                model_used,
                created_at,
                updated_at
            )
            VALUES (
                :request_id,
                :country,
                :city,
                :industry,
                :join_year,
                :join_month,
                :investor_count,
                :prediction_billion_usd,
                :model_used,
                :created_at,
                :updated_at
            )
            """,
            record,
        )


def update_feedback(
    request_id: str,
    feedback_score: int | None,
    actual_valuation_b: float | None,
    comments: str | None,
    updated_at: str,
    db_path: Path | None = None,
) -> bool:
    init_db(db_path)
    with get_connection(db_path) as connection:
        result = connection.execute(
            """
            UPDATE predictions
            SET feedback_score = :feedback_score,
                actual_valuation_b = :actual_valuation_b,
                comments = :comments,
                updated_at = :updated_at
            WHERE request_id = :request_id
            """,
            {
                "request_id": request_id,
                "feedback_score": feedback_score,
                "actual_valuation_b": actual_valuation_b,
                "comments": comments,
                "updated_at": updated_at,
            },
        )
        return result.rowcount > 0


def fetch_prediction(request_id: str, db_path: Path | None = None) -> dict[str, Any] | None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM predictions WHERE request_id = ?",
            (request_id,),
        ).fetchone()
    return dict(row) if row else None
