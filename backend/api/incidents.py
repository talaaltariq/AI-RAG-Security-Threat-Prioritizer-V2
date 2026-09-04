"""Incident API routes for ThreatIQ.

Exposes the correlated incident queue (sorted by composite score), full
incident detail, and the analyst action endpoint that drives incident
status transitions through the mitigation-layer state machine.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.db import (
    AnalystActionModel,
    EventModel,
    IncidentModel,
    LLMExplanationModel,
    get_db,
)
from backend.mitigation.analyst_actions import apply_action
from backend.models.analyst_action import AnalystActionCreate
from backend.models_config.pipeline_settings import get_settings
from backend.pipeline import RULE_BASED_MARKER
from backend.scoring.score_factors import ScoreFactors

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
        ip_rows = (
            db.query(EventModel.incident_id, EventModel.source_ip)
            .filter(EventModel.source_ip.isnot(None))
            .distinct()
            .all()
        )
        source_ips: Dict[str, List[str]] = {}
        for incident_id, ip in ip_rows:
            source_ips.setdefault(incident_id, []).append(ip)
    except SQLAlchemyError as exc:
        logger.exception("Failed to list incidents.")
        raise HTTPException(
            status_code=500, detail="Failed to query incidents"
        ) from exc

    return [
        _incident_summary_dict(
            incident,
            counts.get(incident.id, 0),
            source_ips.get(incident.id, []),
        )
        for incident in incidents
    ]


@router.get("/{incident_id}")
def get_incident(
    incident_id: str, request: Request, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Return the full incident: events, score factors, RAG, LLM, actions.

    When LLM pre-caching is disabled, the ingest pipeline stores only a
    deterministic rule-based explanation; the first detail view upgrades
    it to an LLM-generated one (persisted, so later views are cached).
    """
    incident = db.get(IncidentModel, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    _maybe_generate_lazy_explanation(request, db, incident)

    try:
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
# Lazy LLM explanation (pre-caching disabled)
# ------------------------------------------------------------------ #


def _maybe_generate_lazy_explanation(
    request: Request, db: Session, incident: IncidentModel
) -> None:
    """Generate and persist the LLM explanation on first detail view.

    Only runs when ``enable_precaching`` is off and the stored explanation
    is still the deterministic rule-based one; any failure leaves the
    rule-based explanation in place so the endpoint never breaks.
    """
    stored = incident.llm_explanation
    if stored is not None and RULE_BASED_MARKER not in (
        stored.confidence_reason or ""
    ):
        return  # already an LLM-generated (cached) explanation

    if get_settings(db).enable_precaching:
        return  # pre-caching on: rule-based bands stay rule-based

    explainer = getattr(request.app.state, "explainer", None)
    if explainer is None:
        return

    try:
        result = explainer.explain(
            _lazy_incident_payload(incident),
            _lazy_score_breakdown(incident),
            [_rag_result_dict(r) for r in incident.rag_results],
        )
    except Exception:  # noqa: BLE001 - lazy generation must not break reads
        logger.exception(
            "Lazy LLM explanation failed for incident %s.", incident.id
        )
        return
    if result.error is not None:
        logger.warning(
            "Lazy LLM explanation for incident %s returned error: %s",
            incident.id,
            result.error,
        )
        return

    try:
        row = stored or LLMExplanationModel(incident_id=incident.id)
        row.observed_evidence = result.observed_evidence
        row.retrieved_context = result.retrieved_context
        row.ai_interpretation = result.ai_interpretation
        row.recommended_action = result.recommended_action
        row.confidence = result.confidence
        row.confidence_reason = result.confidence_reason
        row.error = result.error
        if stored is None:
            db.add(row)
        incident.llm_explanation = row
        db.commit()
        logger.info("Lazy LLM explanation persisted for incident %s.", incident.id)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to persist lazy explanation for incident %s.", incident.id
        )


def _lazy_incident_payload(incident: IncidentModel) -> Dict[str, Any]:
    """Rebuild the incident payload the explainer expects from DB rows."""
    events = [_event_dict(event) for event in incident.events]
    max_anomaly = max(
        (float(e.get("anomaly_score") or 0.0) for e in events), default=0.0
    )
    return {
        "id": incident.id,
        "asset": incident.asset,
        "asset_criticality": incident.asset_criticality,
        "severity": incident.severity_label,
        "severity_label": incident.severity_label,
        "total_score": incident.total_score,
        "mitre_technique": incident.mitre_technique,
        "latest_event_time": (
            incident.latest_event_time.isoformat()
            if incident.latest_event_time
            else None
        ),
        "max_anomaly_score": max_anomaly,
        "events": events,
    }


def _lazy_score_breakdown(incident: IncidentModel) -> Dict[str, Any]:
    """Rebuild the score breakdown dict from the stored factor row."""
    row = incident.score_factors
    if row is None:
        return {"factors": [], "total_score": incident.total_score, "max_total": 100}
    factors = ScoreFactors(
        base_severity=row.base_severity,
        anomaly_score_pts=row.anomaly_score_pts,
        asset_criticality_pts=row.asset_criticality_pts,
        exploitability_pts=row.exploitability_pts,
        evidence_count_pts=row.evidence_count_pts,
        recency_pts=row.recency_pts,
        ti_relevance_pts=row.ti_relevance_pts,
        total_score=incident.total_score,
    )
    return factors.to_breakdown_dict()


# ------------------------------------------------------------------ #
# Serializers
# ------------------------------------------------------------------ #


def _incident_summary_dict(
    incident: IncidentModel,
    events_count: int,
    source_ips: Optional[List[str]] = None,
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
        "source_ips": source_ips or [],
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
