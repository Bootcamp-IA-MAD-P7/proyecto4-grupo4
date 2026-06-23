from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import load_config, resolve_path


class Base(DeclarativeBase):
    pass


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    industry = Column(String(255))
    country = Column(String(255))
    continent = Column(String(255))
    year_founded = Column(Float)
    funding_usd = Column(Float)
    company_age = Column(Float)
    predicted_valuation = Column(Float)
    actual_valuation = Column(Float, nullable=True)
    user_rating = Column(Integer, nullable=True)
    notes = Column(String(1000), nullable=True)


class NewObservation(Base):
    __tablename__ = "new_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    payload_json = Column(String(5000))
    source = Column(String(100), default="streamlit")


class ModelMetricSnapshot(Base):
    __tablename__ = "model_metric_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    model_version = Column(String(100))
    rmse = Column(Float)
    mae = Column(Float)
    r2 = Column(Float)
    is_champion = Column(Integer, default=1)


def get_engine():
    config = load_config()
    db_path = resolve_path(config["paths"]["storage_db"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)


def get_session() -> Session:
    init_db()
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)()


def save_prediction_feedback(payload: dict[str, Any]) -> None:
    session = get_session()
    try:
        row = PredictionFeedback(**payload)
        session.add(row)
        session.commit()
    finally:
        session.close()


def save_new_observation(payload: dict[str, Any], source: str = "streamlit") -> None:
    session = get_session()
    try:
        row = NewObservation(payload_json=json.dumps(payload), source=source)
        session.add(row)
        session.commit()
    finally:
        session.close()


def save_metric_snapshot(model_version: str, metrics: dict[str, float], is_champion: bool = True) -> None:
    session = get_session()
    try:
        row = ModelMetricSnapshot(
            model_version=model_version,
            rmse=metrics["rmse"],
            mae=metrics["mae"],
            r2=metrics["r2"],
            is_champion=1 if is_champion else 0,
        )
        session.add(row)
        session.commit()
    finally:
        session.close()
