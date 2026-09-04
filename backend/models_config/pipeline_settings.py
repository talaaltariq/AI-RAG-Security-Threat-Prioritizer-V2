"""Persisted pipeline configuration for ThreatIQ.

A single-row SQLAlchemy model (``pipeline_settings``, always id=1) holding
the runtime-tunable knobs of the detection/scoring/explanation pipeline:
the anomaly threshold, the severity band cutoffs, the RAG retrieval
parameters, and the LLM pre-caching switch.

``get_settings(db_session)`` returns the singleton row, creating it with
defaults on first use. ``load_settings()`` opens a short-lived session for
callers that do not already hold one (detector, scoring helpers) and falls
back to the hard defaults when the database is unavailable, so detection
and scoring never fail on a settings lookup.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, Session, mapped_column

from backend.database.db import Base, SessionLocal

logger = logging.getLogger(__name__)

SINGLETON_ID = 1

# Python-side defaults shared by the column definitions, first-use row
# creation, and the no-database fallback snapshot.
DEFAULTS = {
    "anomaly_threshold": 0.5,
    "severity_critical_min": 80,
    "severity_high_min": 60,
    "severity_medium_min": 40,
    "severity_low_min": 20,
    "rag_top_k": 3,
    "rag_similarity_cutoff": 0.0,
    "enable_precaching": True,
}


def _utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (SQLite-friendly)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PipelineSettings(Base):
    """Singleton row of runtime pipeline configuration (always id=1)."""

    __tablename__ = "pipeline_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=SINGLETON_ID)
    anomaly_threshold: Mapped[float] = mapped_column(
        Float, default=DEFAULTS["anomaly_threshold"]
    )
    severity_critical_min: Mapped[int] = mapped_column(
        Integer, default=DEFAULTS["severity_critical_min"]
    )
    severity_high_min: Mapped[int] = mapped_column(
        Integer, default=DEFAULTS["severity_high_min"]
    )
    severity_medium_min: Mapped[int] = mapped_column(
        Integer, default=DEFAULTS["severity_medium_min"]
    )
    severity_low_min: Mapped[int] = mapped_column(
        Integer, default=DEFAULTS["severity_low_min"]
    )
    rag_top_k: Mapped[int] = mapped_column(Integer, default=DEFAULTS["rag_top_k"])
    rag_similarity_cutoff: Mapped[float] = mapped_column(
        Float, default=DEFAULTS["rag_similarity_cutoff"]
    )
    enable_precaching: Mapped[bool] = mapped_column(
        Boolean, default=DEFAULTS["enable_precaching"]
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


def get_settings(db_session: Session) -> PipelineSettings:
    """Return the singleton settings row, creating it with defaults if missing."""
    row = db_session.get(PipelineSettings, SINGLETON_ID)
    if row is None:
        row = PipelineSettings(id=SINGLETON_ID)
        db_session.add(row)
        db_session.commit()
        db_session.refresh(row)
        logger.info("Created default pipeline settings row.")
    return row


def load_settings() -> PipelineSettings:
    """Return a detached settings snapshot via a short-lived session.

    Falls back to the hard defaults when the database is unavailable so
    detection/scoring paths never fail on a settings lookup.
    """
    try:
        session = SessionLocal()
        try:
            row = get_settings(session)
            session.expunge(row)
            return row
        finally:
            session.close()
    except Exception:  # noqa: BLE001 - settings must never break detection
        logger.exception("Pipeline settings unavailable; using defaults.")
        return PipelineSettings(id=SINGLETON_ID, **DEFAULTS, updated_at=_utcnow())
