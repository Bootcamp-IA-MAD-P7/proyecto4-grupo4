from __future__ import annotations

import logging
import os
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


class Prediction(Base):
    """ORM model for the predictions table (PostgreSQL in production).

    Phase-7 additions:
      - ``predicted_multiple``: ratio valuation_usd / funding_usd predicted by
        the model at inference time.  Stored as a non-nullable float (default
        0.0 used only as a DB-level safety net; application code always
        provides a real value).
      - ``actual_multiple``: ratio computed from the ground-truth valuation
        supplied via PUT /predictions/{id}.  Nullable until feedback arrives.
      - ``model_version``: slug that identifies which model variant produced
        the prediction ("prod" or "candidate"), enabling A/B metric tracking.
    """

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year_founded = Column(Integer, nullable=False)
    funding_usd = Column(Float, nullable=False)
    company_age = Column(Integer, nullable=False)
    industry = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    continent = Column(String(50), nullable=False)
    predicted_valuation_usd = Column(Float, nullable=False)
    actual_valuation_usd = Column(Float, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    # ── Phase-7 MLOps columns ──────────────────────────────────────────────
    predicted_multiple: Column = Column(
        Float, nullable=False, default=0.0,
        comment="valuation_usd / funding_usd predicted by the model",
    )
    actual_multiple: Column = Column(
        Float, nullable=True,
        comment="valuation_usd / funding_usd from ground-truth feedback",
    )
    model_version: Column = Column(
        String(50), nullable=False, default="prod",
        comment="model variant that produced the prediction: 'prod' or 'candidate'",
    )


_engine = None


def get_engine():
    """Return the SQLAlchemy engine, creating it on first call.

    Raises RuntimeError if DATABASE_URL is not set in the environment.
    """
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        _engine = create_engine(url)
    return _engine


def get_session() -> Session:
    """Return a new SQLAlchemy session bound to the engine."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal()


_PHASE7_MIGRATION = [
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS predicted_multiple DOUBLE PRECISION NOT NULL DEFAULT 0.0",
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS actual_multiple DOUBLE PRECISION",
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS model_version VARCHAR(50) NOT NULL DEFAULT 'prod'",
]


def init_db() -> None:
    """Create all tables if they do not already exist, then apply Phase-7 migration.

    ``create_all`` only creates missing tables; it never alters existing ones.
    The explicit ALTER TABLE statements below are idempotent (``ADD COLUMN IF
    NOT EXISTS``) so they are safe to run on every startup against both fresh
    and pre-existing databases.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for stmt in _PHASE7_MIGRATION:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                logger.warning("Migration statement skipped (%s): %s", stmt[:60], exc)


def save_feedback(record: dict[str, Any]) -> int | None:
    """Persist one feedback record and return its auto-generated id."""
    init_db()
    session = get_session()
    try:
        row = Prediction(**record)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """FastAPI dependency: yield a DB session and close it on exit."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def fetch_prediction(record_id: int) -> dict[str, Any] | None:
    """Return a prediction row by id, or None if it does not exist."""
    init_db()
    session = get_session()
    try:
        row = session.get(Prediction, int(record_id))
        if row is None:
            return None
        return {col.name: getattr(row, col.name) for col in row.__table__.columns}
    finally:
        session.close()
