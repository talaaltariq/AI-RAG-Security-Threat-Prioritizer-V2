"""Analyst action state machine for the ThreatIQ mitigation layer.

Implements the human-in-the-loop approval flow: an analyst responds to an
incident with one of three actions (acknowledge / escalate / resolve), and
each action drives the incident to its next lifecycle status. Resolved is a
terminal state — no further actions are accepted afterwards.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from backend.models.analyst_action import AnalystActionResponse
from backend.models.incident import IncidentStatus

ACTION_TO_STATUS: Dict[str, IncidentStatus] = {
    "acknowledge": IncidentStatus.ACKNOWLEDGED,
    "escalate": IncidentStatus.ESCALATED,
    "resolve": IncidentStatus.RESOLVED,
}

VALID_ACTIONS = tuple(ACTION_TO_STATUS.keys())


def apply_action(current_status: str, action: str) -> IncidentStatus:
    """Return the incident status resulting from an analyst action.

    Args:
        current_status: current incident status value (defaults to active
            semantics for unknown/empty input).
        action: one of "acknowledge", "escalate", "resolve".

    Returns:
        The new IncidentStatus.

    Raises:
        ValueError: if the action is unknown or the incident is already
            resolved (terminal state).
    """
    normalized = str(action or "").strip().lower()
    if normalized not in ACTION_TO_STATUS:
        raise ValueError(
            f"Unknown analyst action {action!r}; expected one of {VALID_ACTIONS}"
        )
    try:
        current = IncidentStatus(str(current_status or "active").lower())
    except ValueError:
        current = IncidentStatus.ACTIVE
    if current is IncidentStatus.RESOLVED:
        raise ValueError(
            "Incident is already resolved; no further analyst actions are allowed"
        )
    return ACTION_TO_STATUS[normalized]


def build_action_record(
    incident_id: str,
    action: str,
    analyst_note: Optional[str] = None,
) -> AnalystActionResponse:
    """Create a persisted-shape record for an analyst action.

    Args:
        incident_id: target incident identifier.
        action: one of "acknowledge", "escalate", "resolve".
        analyst_note: optional free-text note from the analyst.

    Returns:
        An AnalystActionResponse with a fresh UUID and UTC timestamp.
    """
    normalized = str(action or "").strip().lower()
    if normalized not in ACTION_TO_STATUS:
        raise ValueError(
            f"Unknown analyst action {action!r}; expected one of {VALID_ACTIONS}"
        )
    return AnalystActionResponse(
        id=str(uuid4()),
        incident_id=incident_id,
        action=normalized,
        created_at=datetime.now(timezone.utc),
        analyst_note=analyst_note,
    )
