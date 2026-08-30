"""Ingestion API routes for ThreatIQ.

Accepts raw security events and runs them through the shared
ThreatPipeline orchestrator (backend/pipeline.py):

normalize -> anomaly detection -> correlation -> risk scoring -> RAG
retrieval -> LLM explanation -> persistence.

The pipeline is assembled once at application startup and stored on
``request.app.state.pipeline``; each request rebinds it to the
request-scoped DB session and the current optional services via
``with_db()``.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.api.pregen import schedule_explanation_pregen
from backend.database.db import get_db
from backend.models.event import EventInput
from backend.pipeline import ThreatPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

DEMO_EVENTS_PATH = (
    Path(__file__).resolve().parents[1] / "demo_data" / "demo_events.json"
)

# Phase 19 input-validation guard: cap batch size to prevent memory
# exhaustion from oversized ingestion payloads.
MAX_EVENTS_PER_REQUEST = 1000


@router.post("", status_code=201)
def ingest_events(
    events: List[EventInput],
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Process a batch of raw events through the threat pipeline."""
    if len(events) > MAX_EVENTS_PER_REQUEST:
        raise HTTPException(
            status_code=413,
            detail=f"Too many events: maximum {MAX_EVENTS_PER_REQUEST} per request",
        )
    raws = [_validated_event_to_raw(event) for event in events]
    return _run_pipeline(raws, request, db)


@router.post("/demo", status_code=201)
def ingest_demo(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Load backend/demo_data/demo_events.json and run the same pipeline.

    Phase 22: once the ingest response has been sent, a background pass
    pre-generates and persists LLM explanations for every HIGH+ incident
    (total_score >= 60), upgrading any rule-based fallback or errored
    explanation left by the inline pass. The frontend always reads
    explanations from the DB, so after this pass the demo never waits on
    a live LLM call.
    """
    if not DEMO_EVENTS_PATH.exists():
        raise HTTPException(status_code=404, detail="Demo data file not found")
    with open(DEMO_EVENTS_PATH, "r", encoding="utf-8") as f:
        raw_events = json.load(f)
    if len(raw_events) > MAX_EVENTS_PER_REQUEST:
        raise HTTPException(
            status_code=413,
            detail=f"Too many events: maximum {MAX_EVENTS_PER_REQUEST} per request",
        )
    result = _run_pipeline(raw_events, request, db)
    result["explanations_pregen_queued"] = schedule_explanation_pregen(
        background_tasks, request.app, result["incident_ids"]
    )
    return result


# ------------------------------------------------------------------ #
# Pipeline invocation
# ------------------------------------------------------------------ #


def _run_pipeline(
    raws: List[Dict[str, Any]],
    request: Request,
    db: Session,
) -> Dict[str, Any]:
    """Run the shared ThreatPipeline and summarize what was persisted."""
    pipeline: ThreatPipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=503, detail="Threat pipeline is not available"
        )

    # Rebind to the request-scoped session and the current optional
    # services, so runtime stubbing of app.state.rag_retriever /
    # app.state.explainer (e.g. in offline tests) is honored.
    pipeline = pipeline.with_db(
        db,
        rag_retriever=getattr(request.app.state, "rag_retriever", None),
        explainer=getattr(request.app.state, "explainer", None),
    )

    try:
        summaries = pipeline.process(raws)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid event payload: {exc}"
        ) from exc
    except RuntimeError as exc:  # detector or DB session unavailable
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "events_received": len(raws),
        "incidents_created": len(summaries),
        "incidents_failed": pipeline.last_run.get("incidents_failed", 0),
        "incident_ids": [summary["id"] for summary in summaries],
    }


def _validated_event_to_raw(event: EventInput) -> Dict[str, Any]:
    """Merge a validated EventInput with its raw payload into one dict.

    Validated fields win over the raw payload; the raw payload still
    contributes source-only fields such as ``raw_severity`` and
    ``details``.
    """
    raw = dict(event.raw_payload or {})
    validated = event.model_dump(mode="json", exclude={"raw_payload"})
    return {**raw, **validated}
