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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year_founded INTEGER NOT NULL,
                funding_usd REAL NOT NULL,
                company_age INTEGER NOT NULL,
                industry TEXT NOT NULL,
                country TEXT NOT NULL,
                continent TEXT NOT NULL,
                predicted_valuation_usd REAL NOT NULL,
                actual_valuation_usd REAL,
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def save_feedback(record: dict[str, Any], db_path: Path | None = None) -> int | None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO predictions (
                year_founded,
                funding_usd,
                company_age,
                industry,
                country,
                continent,
                predicted_valuation_usd,
                actual_valuation_usd,
                comment,
                created_at
            )
            VALUES (
                :year_founded,
                :funding_usd,
                :company_age,
                :industry,
                :country,
                :continent,
                :predicted_valuation_usd,
                :actual_valuation_usd,
                :comment,
                :created_at
            )
            """,
            record,
        )
        return cursor.lastrowid


def save_prediction(record: dict[str, Any], db_path: Path | None = None) -> None:
    save_feedback(record, db_path)


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
            SET actual_valuation_usd = :actual_valuation_usd,
                comment = :comment
            WHERE id = :request_id
            """,
            {
                "request_id": request_id,
                "actual_valuation_usd": (
                    actual_valuation_b * 1_000_000_000 if actual_valuation_b is not None else None
                ),
                "comment": comments,
            },
        )
        return result.rowcount > 0


def fetch_prediction(request_id: str, db_path: Path | None = None) -> dict[str, Any] | None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM predictions WHERE id = ?",
            (request_id,),
        ).fetchone()
    return dict(row) if row else None
