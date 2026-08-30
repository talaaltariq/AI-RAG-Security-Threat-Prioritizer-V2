"""Persistence for analyst actions and incident status transitions.

A self-contained SQLite store (stdlib ``sqlite3``) that satisfies the
Phase 13 requirement that analyst actions are saved to the database and
update the incident status. The ``analyst_actions`` schema mirrors the
Phase 14 SQLAlchemy table (id / incident_id / action / created_at /
analyst_note) so records can be adopted by the full backend later without
loss. Status transitions are validated by the analyst action state
machine before anything is written.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.mitigation.analyst_actions import apply_action, build_action_record

_DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "mitigation.db"
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyst_actions (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('acknowledge', 'escalate', 'resolve')),
    created_at TEXT NOT NULL,
    analyst_note TEXT
);
CREATE INDEX IF NOT EXISTS idx_analyst_actions_incident
    ON analyst_actions (incident_id);
CREATE TABLE IF NOT EXISTS incident_status (
    incident_id TEXT PRIMARY KEY,
    status TEXT NOT NULL
        CHECK (status IN ('active', 'acknowledged', 'escalated', 'resolved')),
    updated_at TEXT NOT NULL
);
"""


class MitigationStore:
    """SQLite-backed store for analyst actions and incident status."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Open (and initialize) the store.

        Args:
            db_path: SQLite file path. Defaults to the MITIGATION_DB_PATH
                env var, then backend/data/mitigation.db. Use ":memory:"
                for tests.
        """
        self.db_path = (
            db_path or os.getenv("MITIGATION_DB_PATH") or str(_DEFAULT_DB_PATH)
        )
        # A :memory: database vanishes when its connection closes, so keep
        # one persistent connection for that case only.
        self._memory_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(self.db_path)
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------------ #
    # Analyst actions
    # ------------------------------------------------------------------ #

    def record_action(
        self,
        incident_id: str,
        action: str,
        analyst_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate, persist, and apply an analyst action to an incident.

        Args:
            incident_id: target incident identifier.
            action: one of "acknowledge", "escalate", "resolve".
            analyst_note: optional free-text note from the analyst.

        Returns:
            {"action": <analyst action record dict>,
             "incident_id": str, "incident_status": <new status>}.

        Raises:
            ValueError: on an unknown action or an action against an
                already-resolved incident (nothing is written).
        """
        current_status = self.get_status(incident_id)
        new_status = apply_action(current_status, action)
        record = build_action_record(incident_id, action, analyst_note)

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO analyst_actions "
                "(id, incident_id, action, created_at, analyst_note) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    record.id,
                    record.incident_id,
                    record.action,
                    record.created_at.isoformat(),
                    record.analyst_note,
                ),
            )
            conn.execute(
                "INSERT INTO incident_status (incident_id, status, updated_at) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(incident_id) DO UPDATE SET "
                "status = excluded.status, updated_at = excluded.updated_at",
                (
                    incident_id,
                    new_status.value,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        return {
            "action": record.model_dump(mode="json"),
            "incident_id": incident_id,
            "incident_status": new_status.value,
        }

    def list_actions(self, incident_id: str) -> List[Dict[str, Any]]:
        """Return all recorded analyst actions for an incident, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, incident_id, action, created_at, analyst_note "
                "FROM analyst_actions WHERE incident_id = ? ORDER BY created_at",
                (incident_id,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "incident_id": row[1],
                "action": row[2],
                "created_at": row[3],
                "analyst_note": row[4],
            }
            for row in rows
        ]

    def get_status(self, incident_id: str) -> str:
        """Return the incident's current status ("active" if unseen)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM incident_status WHERE incident_id = ?",
                (incident_id,),
            ).fetchone()
        return row[0] if row else "active"

    # ------------------------------------------------------------------ #
    # Simulation mode
    # ------------------------------------------------------------------ #

    def mark_mitigated(
        self,
        incident_id: str,
        note: str = "[simulated fix] Recommended mitigation applied",
    ) -> Dict[str, Any]:
        """Remove an incident from the active queue after "Simulate Fix".

        Records a resolve action tagged as simulated and moves the incident
        to the resolved status.

        Returns:
            Same shape as record_action().
        """
        return self.record_action(incident_id, "resolve", analyst_note=note)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _connect(self) -> sqlite3.Connection:
        """Open a transaction-scoped connection (persistent for :memory:)."""
        if self._memory_conn is not None:
            return _PersistentConnection(self._memory_conn)
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        """Create tables if they do not yet exist."""
        with self._connect() as conn:
            conn.executescript(_SCHEMA)


class _PersistentConnection:
    """Context-manager wrapper that commits without closing the connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def __enter__(self) -> sqlite3.Connection:
        return self._conn

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        return False
