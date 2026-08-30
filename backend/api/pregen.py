"""Background LLM explanation pre-generation for ThreatIQ (Phase 22).

After ``POST /api/ingest/demo`` persists its incidents, a FastAPI
background task walks every HIGH+ incident (total_score >= 60) from that
ingest and makes sure a real LLM explanation is stored in the
``llm_explanations`` table:

- Incidents that already hold a successful explanation (live LLM result or
  pre-generated demo cache hit at ingest time) are skipped.
- Incidents whose stored explanation is a deterministic rule-based
  fallback, or carries an error (e.g. the LLM was briefly unavailable at
  ingest time), are regenerated through ``app.state.explainer`` and the
  row is updated in place.

The task runs in its own SQLAlchemy session (the request-scoped session is
closed by the time background tasks execute) and never raises: a failure
on one incident is logged and the pass continues.

The frontend never calls the LLM directly — ``GET /api/incidents/{id}``
always reads the persisted explanation row — so once this pass completes,
incident detail pages serve pre-generated explanations straight from the
DB with no real-time LLM latency.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List

from backend.database.db import (
    IncidentModel,
    LLMExplanationModel,
    SessionLocal,
)
from backend.pipeline import ThreatPipeline
from backend.scoring.score_factors import ScoreFactors

if TYPE_CHECKING:
    from fastapi import BackgroundTasks, FastAPI

logger = logging.getLogger(__name__)

# Marker written by backend.pipeline.generate_rule_based_explanation into
# confidence_reason; used to detect fallback explanations worth upgrading.
RULE_BASED_MARKER = "rule-based"


def schedule_explanation_pregen(
    background_tasks: "BackgroundTasks",
    app: "FastAPI",
    incident_ids: List[str],
) -> int:
    """Queue the pre-generation pass for the HIGH+ incidents of an ingest.

    Returns the number of incident IDs handed to the background task (the
    score filter is applied inside the task, where the DB rows are read).
    """
    if not incident_ids:
        return 0
    background_tasks.add_task(
        pregenerate_explanations,
        app,
        list(incident_ids),
        ThreatPipeline.LLM_SCORE_THRESHOLD,
    )
    return len(incident_ids)


def pregenerate_explanations(
    app: "FastAPI",
    incident_ids: List[str],
    min_score: int = ThreatPipeline.LLM_SCORE_THRESHOLD,
) -> Dict[str, int]:
    """Ensure every HIGH+ incident in ``incident_ids`` has an LLM explanation.

    Runs synchronously; intended to be scheduled as a FastAPI background
    task so the ingest response returns immediately.
    """
    stats = {"checked": 0, "already_cached": 0, "regenerated": 0, "failed": 0}
    explainer = getattr(app.state, "explainer", None)

    db = SessionLocal()
    try:
        for incident_id in incident_ids:
            incident = db.get(IncidentModel, incident_id)
            if incident is None or incident.total_score < min_score:
                continue
            stats["checked"] += 1

            existing = incident.llm_explanation
            if existing is not None and not _needs_regeneration(existing):
                stats["already_cached"] += 1
                continue

            if explainer is None:
                logger.warning(
                    "Pre-generation skipped for incident %s: no explainer.",
                    incident_id,
                )
                stats["failed"] += 1
                continue

            try:
                _regenerate(db, explainer, incident)
                stats["regenerated"] += 1
            except Exception:  # noqa: BLE001 - one failure must not stop the pass
                db.rollback()
                stats["failed"] += 1
                logger.exception(
                    "Pre-generation failed for incident %s.", incident_id
                )
    finally:
        db.close()

    logger.info(
        "Explanation pre-generation complete: %d checked, %d already cached, "
        "%d regenerated, %d failed.",
        stats["checked"],
        stats["already_cached"],
        stats["regenerated"],
        stats["failed"],
    )
    return stats


# ------------------------------------------------------------------ #
# Internals
# ------------------------------------------------------------------ #


def _needs_regeneration(explanation: LLMExplanationModel) -> bool:
    """Return True for fallback/errored explanations worth an LLM upgrade."""
    if explanation.error:
        return True
    return RULE_BASED_MARKER in (explanation.confidence_reason or "")


def _regenerate(db, explainer, incident: IncidentModel) -> None:
    """Regenerate one incident's explanation and upsert the DB row."""
    incident_dict = _incident_prompt_dict(incident)
    score_factors_dict = _score_factors_prompt_dict(incident)
    rag_results_list = _rag_prompt_list(incident)

    result = explainer.explain(incident_dict, score_factors_dict, rag_results_list)
    if result.error is not None:
        # Keep the existing fallback rather than persisting an LLM error.
        raise RuntimeError(f"LLM regeneration returned an error: {result.error}")

    row = incident.llm_explanation
    if row is None:
        row = LLMExplanationModel(incident_id=incident.id)
        db.add(row)
    row.observed_evidence = result.observed_evidence
    row.retrieved_context = result.retrieved_context
    row.ai_interpretation = result.ai_interpretation
    row.recommended_action = result.recommended_action
    row.confidence = result.confidence
    row.confidence_reason = result.confidence_reason
    row.error = result.error
    incident.confidence = result.confidence
    db.commit()
    logger.info("Pre-generated LLM explanation stored for incident %s.", incident.id)


def _incident_prompt_dict(incident: IncidentModel) -> Dict[str, Any]:
    """Rebuild the incident payload the prompt builder expects, from DB rows."""
    events: List[Dict[str, Any]] = []
    for event in incident.events:
        try:
            payload = json.loads(event.raw_data or "{}")
        except (TypeError, ValueError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("event_type", event.event_type)
        payload.setdefault("source_ip", event.source_ip)
        events.append(payload)

    return {
        "id": incident.id,
        "asset": incident.asset,
        "asset_criticality": incident.asset_criticality,
        "latest_event_time": (
            incident.latest_event_time.isoformat()
            if incident.latest_event_time
            else None
        ),
        "mitre_technique": incident.mitre_technique,
        "total_score": incident.total_score,
        "severity_label": incident.severity_label,
        "events": events,
    }


def _score_factors_prompt_dict(incident: IncidentModel) -> Dict[str, Any]:
    """Rebuild a ScoreFactors.to_breakdown_dict()-shaped dict from the DB row.

    The DB persists points only (no reasons), so reasons are left empty —
    the prompt builder treats them as optional.
    """
    row = incident.score_factors
    factors = []
    for meta in ScoreFactors.FACTOR_META:
        factors.append(
            {
                "factor": meta["name"],
                "points": getattr(row, meta["key"]) if row is not None else 0,
                "max_points": meta["max_points"],
                "reason": "",
            }
        )
    return {
        "factors": factors,
        "total_score": incident.total_score,
        "max_total": sum(meta["max_points"] for meta in ScoreFactors.FACTOR_META),
    }


def _rag_prompt_list(incident: IncidentModel) -> List[Dict[str, Any]]:
    """Rebuild RAGResult-shaped dicts from the persisted RAG rows."""
    return [
        {
            "content": r.content,
            "source": r.source,
            "technique_id": r.technique_id,
            "cve_id": r.cve_id,
            "relevance_score": r.relevance_score,
        }
        for r in incident.rag_results
    ]
