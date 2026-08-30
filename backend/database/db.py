"""SQLAlchemy database layer for the ThreatIQ FastAPI backend.

Defines the engine (SQLite by default), the SessionLocal factory, the
declarative Base, and the ORM models backing the API: incidents, events,
score_factors, rag_results, llm_explanations, and analyst_actions.

The connection URL comes from the DATABASE_URL environment variable
(loaded from backend/.env via python-dotenv); no credentials are
hard-coded here.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Generator, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./threatiq.db")

_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if DATABASE_URL.startswith("sqlite"):
    # SQLite ignores foreign key constraints unless they are explicitly
    # enabled per connection; without this the FK relationships below
    # would not be enforced.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _uuid_str() -> str:
    """Return a fresh UUID4 string for primary keys."""
    return str(uuid4())


def _utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (SQLite-friendly)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Declarative base for all ThreatIQ ORM models."""


class IncidentModel(Base):
    """A correlated group of security events with its composite score."""

    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'acknowledged', 'escalated', 'resolved')",
            name="ck_incidents_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")
    severity_label: Mapped[str] = mapped_column(String(20), default="low")
    latest_event_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    asset: Mapped[str] = mapped_column(String(255), default="unknown")
    asset_criticality: Mapped[str] = mapped_column(String(20), default="low")
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    mitre_technique: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="low")

    events: Mapped[List["EventModel"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    score_factors: Mapped[Optional["ScoreFactorsModel"]] = relationship(
        back_populates="incident", uselist=False, cascade="all, delete-orphan"
    )
    llm_explanation: Mapped[Optional["LLMExplanationModel"]] = relationship(
        back_populates="incident", uselist=False, cascade="all, delete-orphan"
    )
    rag_results: Mapped[List["RAGResultModel"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    analyst_actions: Mapped[List["AnalystActionModel"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class EventModel(Base):
    """A single normalized security event belonging to an incident."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id"), index=True
    )
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    source_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dest_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), default="unknown")
    # Full normalized event payload serialized as JSON text.
    raw_data: Mapped[str] = mapped_column(Text, default="{}")

    incident: Mapped[IncidentModel] = relationship(back_populates="events")


class ScoreFactorsModel(Base):
    """Per-factor point breakdown of an incident's composite risk score."""

    __tablename__ = "score_factors"

    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id"), primary_key=True
    )
    base_severity: Mapped[int] = mapped_column(Integer, default=0)
    anomaly_score_pts: Mapped[int] = mapped_column(Integer, default=0)
    asset_criticality_pts: Mapped[int] = mapped_column(Integer, default=0)
    exploitability_pts: Mapped[int] = mapped_column(Integer, default=0)
    evidence_count_pts: Mapped[int] = mapped_column(Integer, default=0)
    recency_pts: Mapped[int] = mapped_column(Integer, default=0)
    ti_relevance_pts: Mapped[int] = mapped_column(Integer, default=0)
    anomaly_score_raw: Mapped[float] = mapped_column(Float, default=0.0)

    incident: Mapped[IncidentModel] = relationship(back_populates="score_factors")


class LLMExplanationModel(Base):
    """Structured LLM-generated analyst explanation for an incident."""

    __tablename__ = "llm_explanations"

    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id"), primary_key=True
    )
    observed_evidence: Mapped[str] = mapped_column(Text, default="")
    retrieved_context: Mapped[str] = mapped_column(Text, default="")
    ai_interpretation: Mapped[str] = mapped_column(Text, default="")
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String(20), default="low")
    confidence_reason: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped[IncidentModel] = relationship(back_populates="llm_explanation")


class RAGResultModel(Base):
    """One retrieved threat-intelligence document linked to an incident."""

    __tablename__ = "rag_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id"), index=True
    )
    content: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(64), default="")
    technique_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cve_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)

    incident: Mapped[IncidentModel] = relationship(back_populates="rag_results")


class AnalystActionModel(Base):
    """An analyst lifecycle action (acknowledge/escalate/resolve)."""

    __tablename__ = "analyst_actions"
    __table_args__ = (
        CheckConstraint(
            "action IN ('acknowledge', 'escalate', 'resolve')",
            name="ck_analyst_actions_action",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    analyst_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped[IncidentModel] = relationship(back_populates="analyst_actions")


def init_db() -> None:
    """Create all tables if they do not yet exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized (%s).", DATABASE_URL)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
