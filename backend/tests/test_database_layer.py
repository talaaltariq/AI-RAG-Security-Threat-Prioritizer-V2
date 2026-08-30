"""Script-style test for the ThreatIQ SQLAlchemy database layer.

Covers the Phase 16 Definition of Done:
  1. All tables are created on first startup (init_db()).
  2. Foreign key relationships work correctly (enforced + ORM loading).
  3. No data loss between restarts (fresh engine over the same file).

Runs against a temporary SQLite database. Run from the repository root::

    venv/Scripts/python backend/test_database_layer.py
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Isolate the test database before any backend.database import.
_TMP_DIR = Path(tempfile.mkdtemp())
_TMP_DB = _TMP_DIR / "test_threatiq.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from sqlalchemy import create_engine, event, inspect  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from backend.database.db import (  # noqa: E402
    AnalystActionModel,
    EventModel,
    IncidentModel,
    LLMExplanationModel,
    RAGResultModel,
    ScoreFactorsModel,
    SessionLocal,
    engine,
    init_db,
)

CHECKS = []

EXPECTED_TABLES = {
    "incidents",
    "events",
    "score_factors",
    "llm_explanations",
    "rag_results",
    "analyst_actions",
}


def check(name: str, condition: bool) -> None:
    CHECKS.append((name, condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")


def _seed_incident(session) -> str:
    """Insert one incident with one child row in each related table."""
    incident = IncidentModel(
        status="active",
        asset="prod-db-01",
        asset_criticality="critical",
        total_score=85,
        severity_label="high",
        mitre_technique="T1046",
        latest_event_time=datetime(2026, 8, 29, 10, 5, 0),
        confidence="high",
    )
    session.add(incident)
    session.flush()  # assign incident.id before children reference it
    session.add_all(
        [
            EventModel(
                incident_id=incident.id,
                timestamp=datetime(2026, 8, 29, 10, 0, 0),
                source_ip="203.0.113.9",
                dest_ip="10.0.0.5",
                event_type="port_scan",
                raw_data='{"port": 3306}',
            ),
            ScoreFactorsModel(
                incident_id=incident.id,
                base_severity=40,
                anomaly_score_pts=15,
                asset_criticality_pts=15,
                exploitability_pts=5,
                evidence_count_pts=5,
                recency_pts=3,
                ti_relevance_pts=2,
                anomaly_score_raw=-0.42,
            ),
            LLMExplanationModel(
                incident_id=incident.id,
                observed_evidence="scan burst",
                retrieved_context="T1046 Network Service Discovery",
                ai_interpretation="likely reconnaissance",
                recommended_action="block source IP",
                confidence="high",
                confidence_reason="multiple corroborating events",
                error=None,
            ),
            RAGResultModel(
                incident_id=incident.id,
                content="Network Service Discovery...",
                source="mitre_attack",
                technique_id="T1046",
                cve_id=None,
                relevance_score=0.91,
            ),
            AnalystActionModel(
                incident_id=incident.id,
                action="acknowledge",
                analyst_note="triaging",
            ),
        ]
    )
    session.commit()
    return incident.id


def main() -> int:
    # 1. All tables created on first startup.
    init_db()
    tables = set(inspect(engine).get_table_names())
    check("init_db() creates all 6 tables", EXPECTED_TABLES.issubset(tables))

    # Calling init_db() again must be a safe no-op (idempotent startup).
    init_db()
    check("init_db() is idempotent", EXPECTED_TABLES.issubset(
        set(inspect(engine).get_table_names())
    ))

    # 2. Foreign key relationships work correctly.
    with SessionLocal() as session:
        incident_id = _seed_incident(session)
        loaded = session.get(IncidentModel, incident_id)
        check("incident.events loads 1 event", len(loaded.events) == 1)
        check(
            "incident.score_factors loads 1:1 row",
            loaded.score_factors is not None
            and loaded.score_factors.anomaly_score_raw == -0.42,
        )
        check(
            "incident.llm_explanation loads 1:1 row",
            loaded.llm_explanation is not None
            and loaded.llm_explanation.confidence == "high",
        )
        check("incident.rag_results loads 1 row", len(loaded.rag_results) == 1)
        check(
            "incident.analyst_actions loads 1 row",
            len(loaded.analyst_actions) == 1,
        )
        check(
            "child -> parent back-reference resolves",
            loaded.events[0].incident.id == incident_id,
        )

    # FK enforcement: a child row referencing a missing incident must fail.
    with SessionLocal() as session:
        session.add(
            EventModel(incident_id="no-such-incident", event_type="port_scan")
        )
        try:
            session.commit()
            fk_enforced = False
        except IntegrityError:
            session.rollback()
            fk_enforced = True
    check("orphan event insert rejected by FK constraint", fk_enforced)

    # Check constraints on enumerated columns.
    with SessionLocal() as session:
        session.add(IncidentModel(status="bogus-status"))
        try:
            session.commit()
            status_checked = False
        except IntegrityError:
            session.rollback()
            status_checked = True
    check("invalid incident status rejected by CHECK constraint", status_checked)

    # Cascade delete: removing an incident removes all child rows.
    with SessionLocal() as session:
        incident = session.get(IncidentModel, incident_id)
        session.delete(incident)
        session.commit()
        orphans = (
            session.query(EventModel).count()
            + session.query(ScoreFactorsModel).count()
            + session.query(LLMExplanationModel).count()
            + session.query(RAGResultModel).count()
            + session.query(AnalystActionModel).count()
        )
        check("deleting incident cascades to all child tables", orphans == 0)

    # 3. No data loss between restarts: seed again, then read through a
    # brand-new engine pointing at the same file (simulates a restart).
    with SessionLocal() as session:
        incident_id = _seed_incident(session)
    engine.dispose()

    restart_engine = create_engine(f"sqlite:///{_TMP_DB}")
    event.listen(
        restart_engine,
        "connect",
        lambda conn, _rec: conn.cursor().execute("PRAGMA foreign_keys=ON"),
    )
    RestartSession = sessionmaker(bind=restart_engine)
    with RestartSession() as session:
        persisted = session.get(IncidentModel, incident_id)
        check(
            "incident survives restart via fresh engine",
            persisted is not None and persisted.total_score == 85,
        )
        check(
            "child rows survive restart",
            persisted is not None
            and len(persisted.events) == 1
            and persisted.score_factors is not None
            and persisted.llm_explanation is not None
            and len(persisted.rag_results) == 1
            and len(persisted.analyst_actions) == 1,
        )
    restart_engine.dispose()

    failed = [name for name, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
