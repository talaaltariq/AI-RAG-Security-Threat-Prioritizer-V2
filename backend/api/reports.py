"""Report export API routes for ThreatIQ.

Exposes GET /api/reports/export: renders the full current incident queue
(with score factors, LLM explanations, and RAG citations) into a
downloadable PDF.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.api.incidents import (
    _analyst_action_dict,
    _event_dict,
    _incident_summary_dict,
    _llm_explanation_dict,
    _rag_result_dict,
    _score_factors_dict,
)
from backend.database.db import EventModel, IncidentModel, get_db
from backend.reports.report_builder import build_incident_report_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/export")
def export_incident_report(db: Session = Depends(get_db)) -> Response:
    """Export all incidents with full detail as a PDF attachment."""
    try:
        incidents_data = _load_full_incidents(db)
        alert_reduction_pct = _alert_reduction_pct(db)
    except SQLAlchemyError as exc:
        logger.exception("Failed to load incidents for report export.")
        raise HTTPException(
            status_code=500, detail="Failed to load incidents for report"
        ) from exc

    try:
        pdf_bytes = build_incident_report_pdf(incidents_data, alert_reduction_pct)
    except Exception as exc:  # noqa: BLE001 - report any render failure as 500
        logger.exception("Failed to build incident report PDF.")
        raise HTTPException(
            status_code=500, detail="Failed to build report PDF"
        ) from exc

    filename = f"threatiq_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _load_full_incidents(db: Session) -> List[Dict[str, Any]]:
    """Load all incidents with full detail, reusing incidents.py serializers."""
    incidents = (
        db.query(IncidentModel).order_by(IncidentModel.total_score.desc()).all()
    )
    results: List[Dict[str, Any]] = []
    for incident in incidents:
        detail = _incident_summary_dict(
            incident,
            len(incident.events),
            sorted({e.source_ip for e in incident.events if e.source_ip}),
        )
        detail["events"] = [_event_dict(event) for event in incident.events]
        detail["score_factors"] = (
            _score_factors_dict(incident.score_factors)
            if incident.score_factors
            else None
        )
        detail["llm_explanation"] = (
            _llm_explanation_dict(incident.llm_explanation)
            if incident.llm_explanation
            else None
        )
        detail["rag_results"] = [
            _rag_result_dict(result) for result in incident.rag_results
        ]
        detail["analyst_actions"] = [
            _analyst_action_dict(action) for action in incident.analyst_actions
        ]
        results.append(detail)
    return results


def _alert_reduction_pct(db: Session) -> float:
    """Compute the correlation alert-reduction percentage (same as /api/stats)."""
    total_events = db.query(func.count(EventModel.id)).scalar() or 0
    total_incidents = db.query(func.count(IncidentModel.id)).scalar() or 0
    if total_events > 0 and total_incidents <= total_events:
        return round((1 - total_incidents / total_events) * 100, 1)
    return 0.0
