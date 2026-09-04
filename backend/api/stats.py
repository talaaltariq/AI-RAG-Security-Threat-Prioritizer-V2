"""Stats API route for ThreatIQ.

Returns dashboard overview metrics computed from the incident/event
tables: today's event volume, incident totals per severity band, and the
alert reduction percentage produced by correlation.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.db import EventModel, IncidentModel, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])

_SEVERITY_LABELS = ("critical", "high", "medium", "low")


@router.get("")
def get_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return overview metrics for the dashboard stat cards."""
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        total_events_today = (
            db.query(func.count(EventModel.id))
            .filter(EventModel.timestamp >= today_start)
            .scalar()
            or 0
        )
        total_events = db.query(func.count(EventModel.id)).scalar() or 0
        total_incidents = db.query(func.count(IncidentModel.id)).scalar() or 0
        severity_counts = dict(
            db.query(IncidentModel.severity_label, func.count(IncidentModel.id))
            .group_by(IncidentModel.severity_label)
            .all()
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to compute stats.")
        raise HTTPException(
            status_code=500, detail="Failed to compute stats"
        ) from exc

    if total_events > 0 and total_incidents <= total_events:
        alert_reduction_pct = round(
            (1 - total_incidents / total_events) * 100, 1
        )
    else:
        alert_reduction_pct = 0.0

    stats = {
        "total_events": total_events,
        "total_events_today": total_events_today,
        "total_incidents": total_incidents,
        "alert_reduction_pct": alert_reduction_pct,
    }
    for label in _SEVERITY_LABELS:
        stats[f"{label}_count"] = int(severity_counts.get(label, 0))
    return stats
