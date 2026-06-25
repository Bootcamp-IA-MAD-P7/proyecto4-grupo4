from __future__ import annotations

import os
from typing import Any

from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


class Prediction(Base):
    """ORM model for the predictions table (PostgreSQL in production)."""

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
    created_at = Column(String(50), nullable=False)


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


def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(get_engine())


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
