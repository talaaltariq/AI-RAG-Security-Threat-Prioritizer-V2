"""Incident API routes for ThreatIQ.

Exposes the correlated incident queue (sorted by composite score), full
incident detail, and the analyst action endpoint that drives incident
status transitions through the mitigation-layer state machine.
"""

import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.db import (
    AnalystActionModel,
    EventModel,
    IncidentModel,
    get_db,
)
from backend.mitigation.analyst_actions import apply_action
from backend.models.analyst_action import AnalystActionCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("")
def list_incidents(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Return all incidents as summaries, sorted by total_score DESC."""
    try:
        incidents = (
            db.query(IncidentModel)
            .order_by(IncidentModel.total_score.desc())
            .all()
        )
        counts = dict(
            db.query(EventModel.incident_id, func.count(EventModel.id))
            .group_by(EventModel.incident_id)
            .all()
        )
    except SQLAlchemyError as exc:
        logger.exception("Failed to list incidents.")
        raise HTTPException(
            status_code=500, detail="Failed to query incidents"
        ) from exc

    return [
        _incident_summary_dict(incident, counts.get(incident.id, 0))
        for incident in incidents
    ]


@router.get("/{incident_id}")
def get_incident(
    incident_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Return the full incident: events, score factors, RAG, LLM, actions."""
    incident = db.get(IncidentModel, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        detail = _incident_summary_dict(incident, len(incident.events))
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
    except SQLAlchemyError as exc:
        logger.exception("Failed to load incident %s detail.", incident_id)
        raise HTTPException(
            status_code=500, detail="Failed to load incident detail"
        ) from exc

    return detail


@router.post("/{incident_id}/action", status_code=200)
def submit_analyst_action(
    incident_id: str,
    payload: AnalystActionCreate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Record an analyst action and transition the incident status."""
    incident = db.get(IncidentModel, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        new_status = apply_action(incident.status, payload.action)
    except ValueError as exc:
        status_code = 409 if "already resolved" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    try:
        action = AnalystActionModel(
            incident_id=incident.id,
            action=payload.action,
            analyst_note=payload.analyst_note,
        )
        incident.status = new_status.value
        db.add(action)
        db.commit()
        db.refresh(action)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to record analyst action on %s.", incident_id)
        raise HTTPException(
            status_code=500, detail="Failed to record analyst action"
        ) from exc

    logger.info(
        "Analyst action %r on incident %s -> status %s.",
        payload.action,
        incident_id,
        incident.status,
    )
    return {
        "status": "updated",
        "incident_id": incident_id,
        "incident_status": incident.status,
        "action": _analyst_action_dict(action),
    }


# ------------------------------------------------------------------ #
# Serializers
# ------------------------------------------------------------------ #


def _incident_summary_dict(
    incident: IncidentModel, events_count: int
) -> Dict[str, Any]:
    """Serialize an IncidentModel to the IncidentSummary shape."""
    return {
        "id": incident.id,
        "created_at": incident.created_at,
        "status": incident.status,
        "asset": incident.asset,
        "asset_criticality": incident.asset_criticality,
        "total_score": incident.total_score,
        "severity_label": incident.severity_label,
        "mitre_technique": incident.mitre_technique,
        "latest_event_time": incident.latest_event_time,
        "events_count": events_count,
        "confidence": incident.confidence,
    }


def _event_dict(event: EventModel) -> Dict[str, Any]:
    """Return the stored raw event payload enriched with DB identifiers."""
    try:
        data = json.loads(event.raw_data or "{}")
    except (TypeError, ValueError):
        data = {}
    data["id"] = event.id
    data["incident_id"] = event.incident_id
    return data


def _score_factors_dict(score_factors) -> Dict[str, Any]:
    """Serialize a ScoreFactorsModel row."""
    return {
        "base_severity": score_factors.base_severity,
        "anomaly_score_pts": score_factors.anomaly_score_pts,
        "asset_criticality_pts": score_factors.asset_criticality_pts,
        "exploitability_pts": score_factors.exploitability_pts,
        "evidence_count_pts": score_factors.evidence_count_pts,
        "recency_pts": score_factors.recency_pts,
        "ti_relevance_pts": score_factors.ti_relevance_pts,
        "anomaly_score_raw": score_factors.anomaly_score_raw,
    }


def _llm_explanation_dict(explanation) -> Dict[str, Any]:
    """Serialize an LLMExplanationModel row."""
    return {
        "observed_evidence": explanation.observed_evidence,
        "retrieved_context": explanation.retrieved_context,
        "ai_interpretation": explanation.ai_interpretation,
        "recommended_action": explanation.recommended_action,
        "confidence": explanation.confidence,
        "confidence_reason": explanation.confidence_reason,
        "error": explanation.error,
    }


def _rag_result_dict(result) -> Dict[str, Any]:
    """Serialize a RAGResultModel row."""
    return {
        "id": result.id,
        "content": result.content,
        "source": result.source,
        "technique_id": result.technique_id,
        "cve_id": result.cve_id,
        "relevance_score": result.relevance_score,
    }


def _analyst_action_dict(action) -> Dict[str, Any]:
    """Serialize an AnalystActionModel row."""
    return {
        "id": action.id,
        "incident_id": action.incident_id,
        "action": action.action,
        "created_at": action.created_at,
        "analyst_note": action.analyst_note,
    }
