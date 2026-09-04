"""End-to-end ingestion pipeline orchestrator for ThreatIQ.

Wires every backend module into a single processing flow:

    normalize -> anomaly detection -> correlation -> risk scoring
    -> RAG retrieval -> LLM explanation -> persistence

The pipeline is a thin orchestrator: all detection, grouping, scoring,
retrieval, and explanation logic lives in the individual modules. When
``enable_precaching`` is on, LLM explanations are requested at ingest
time for incidents scoring at or above the configured
``severity_high_min`` (default 60); everything below that band gets a
deterministic rule-based explanation instead. When pre-caching is off,
no LLM calls happen at ingest time and explanations are generated lazily
on first incident detail view (see backend/api/incidents.py).

Scoring-flag derivation: the RiskScorer consumes ``has_known_exploit``,
``has_active_exploit`` and ``high_relevance_ti`` inputs that no upstream
module populates. The pipeline derives them deterministically from the
grounded event evidence (event ``details`` text), so incidents whose own
telemetry reports attack tooling / threat-intel hits are scored in the
CRITICAL band as the playbook intends.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.db import (
    EventModel,
    IncidentModel,
    LLMExplanationModel,
    RAGResultModel,
    ScoreFactorsModel,
)
from backend.llm.explainer import ExplanationResult
from backend.models.event import EventInput, normalize_event
from backend.models_config.pipeline_settings import (
    PipelineSettings,
    load_settings,
)
from backend.scoring.score_factors import ScoreFactors

if TYPE_CHECKING:
    from backend.correlation.correlator import EventCorrelator
    from backend.detection.anomaly_detector import AnomalyDetector
    from backend.llm.explainer import ThreatExplainer
    from backend.rag.rag_retriever import RAGResult, RAGRetriever
    from backend.scoring.risk_scorer import RiskScorer

logger = logging.getLogger(__name__)


def score_to_label(
    total_score: int, settings: Optional[PipelineSettings] = None
) -> str:
    """Map a 0-100 composite score to a severity label band.

    Thresholds come from the persisted PipelineSettings row (defaults:
    >=80 critical, >=60 high, >=40 medium, else low); when no settings
    object is passed, the current row is loaded from the database.
    """
    if settings is None:
        settings = load_settings()
    if total_score >= settings.severity_critical_min:
        return "critical"
    if total_score >= settings.severity_high_min:
        return "high"
    if total_score >= settings.severity_medium_min:
        return "medium"
    return "low"


# Substring marking rule-based (non-LLM) explanations; used by the
# incidents API to detect which rows still need lazy LLM generation.
RULE_BASED_MARKER = "deterministic rule-based analysis"


def generate_rule_based_explanation(incident: Dict[str, Any]) -> ExplanationResult:
    """Build a deterministic ExplanationResult without calling the LLM.

    Used for incidents below the LLM score threshold and as a fallback
    when no LLM explainer is configured or the LLM call fails outright.
    """
    events = incident.get("events") or []
    score_factors: Optional[ScoreFactors] = incident.get("score_factors")
    total_score = int(incident.get("total_score") or 0)
    severity_label = str(incident.get("severity_label") or "low")
    asset = str(incident.get("asset") or "unknown")
    criticality = str(incident.get("asset_criticality") or "low")
    max_anomaly = float(incident.get("max_anomaly_score") or 0.0)

    event_types = sorted(
        {str(e.get("event_type") or "unknown") for e in events if isinstance(e, dict)}
    )
    observed_evidence = (
        f"{len(events)} correlated event(s) involving asset {asset} "
        f"({criticality} criticality): {', '.join(event_types) or 'unknown'}. "
        f"Strongest reported severity is "
        f"{str(incident.get('severity') or 'low').upper()}; peak anomaly "
        f"score is {max_anomaly:.2f}."
    )

    rag_results = incident.get("rag_results") or []
    citations = [
        str(r.get("technique_id") or r.get("cve_id") or r.get("source") or "")
        for r in rag_results[:3]
        if isinstance(r, dict)
    ]
    citations = [c for c in citations if c]
    if citations:
        retrieved_context = (
            f"Retrieved {len(rag_results)} threat-intelligence document(s); "
            f"top sources: {', '.join(citations)}."
        )
    else:
        retrieved_context = "No threat intelligence retrieved for this incident."

    drivers = ""
    if score_factors is not None:
        points = {
            meta["key"]: getattr(score_factors, meta["key"])
            for meta in ScoreFactors.FACTOR_META
        }
        top_keys = sorted(points, key=lambda k: points[k], reverse=True)[:2]
        drivers = "; ".join(
            score_factors.reasons.get(k, "") for k in top_keys if points[k] > 0
        )
    ai_interpretation = (
        f"Composite risk score is {total_score}/100 ({severity_label.upper()} band)."
        + (f" Main scoring drivers: {drivers}." if drivers else "")
    )

    recommended_action = _rule_based_action(severity_label, asset)
    confidence = "medium" if total_score >= 40 else "low"

    return ExplanationResult(
        observed_evidence=observed_evidence,
        retrieved_context=retrieved_context,
        ai_interpretation=ai_interpretation,
        recommended_action=recommended_action,
        confidence=confidence,
        confidence_reason=(
            f"Generated by {RULE_BASED_MARKER} without LLM "
            "reasoning (score below the LLM threshold or LLM unavailable)."
        ),
    )


def _rule_based_action(severity_label: str, asset: str) -> str:
    """Return a concrete recommended action for a severity band."""
    if severity_label == "critical":
        return (
            f"Immediately isolate {asset} from the network, preserve forensic "
            "evidence, and escalate to the incident response team."
        )
    if severity_label == "high":
        return (
            f"Prioritize investigation of {asset} within the hour: verify "
            "account integrity, review authentication logs, and block the "
            "source at the perimeter."
        )
    if severity_label == "medium":
        return (
            f"Investigate the activity on {asset} within 24 hours and tune "
            "detection thresholds if it is confirmed benign."
        )
    return f"Log and monitor {asset}; no immediate action required."


class ThreatPipeline:
    """Orchestrates the full raw-event-to-persisted-incident flow."""

    # LLM explanations are only generated for HIGH and CRITICAL incidents.
    # This is the default band cutoff; the live value is read from
    # PipelineSettings.severity_high_min on every pipeline run.
    LLM_SCORE_THRESHOLD = 60

    # Deterministic scoring-flag indicators matched against the lowercased
    # event details of an incident. They only fire on explicit, grounded
    # evidence reported by the telemetry itself (attack tooling, C2
    # infrastructure, threat-intel confirmations).
    ACTIVE_EXPLOIT_INDICATORS = (
        "meterpreter",
        "reverse shell",
        "reverse tcp",
        "c2 domain",
        "c2 channel",
        "c2 infrastructure",
        "known-malicious",
    )
    KNOWN_EXPLOIT_INDICATORS = (
        "exploit",
        "proof-of-concept",
        "poc exploit",
    )
    HIGH_TI_INDICATORS = (
        "threat-intelligence hit",
        "threat intelligence hit",
        "known-malicious",
    )

    def __init__(
        self,
        detector: Optional[AnomalyDetector],
        correlator: EventCorrelator,
        scorer: RiskScorer,
        rag_retriever: Optional[RAGRetriever] = None,
        explainer: Optional[ThreatExplainer] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Store the component services; ``db`` is bound per request."""
        self.detector = detector
        self.correlator = correlator
        self.scorer = scorer
        self.rag_retriever = rag_retriever
        self.explainer = explainer
        self.db = db
        # Stats for the most recent process() call (per-instance, so a
        # request-scoped clone never races with other requests).
        self.last_run: Dict[str, int] = {}

    def with_db(
        self,
        db: Session,
        *,
        rag_retriever: Optional[RAGRetriever] = None,
        explainer: Optional[ThreatExplainer] = None,
    ) -> "ThreatPipeline":
        """Return a request-scoped clone sharing the heavy components.

        The optional services are passed explicitly (rather than copied)
        so callers can honor runtime reconfiguration of ``app.state``.
        """
        return ThreatPipeline(
            detector=self.detector,
            correlator=self.correlator,
            scorer=self.scorer,
            rag_retriever=rag_retriever,
            explainer=explainer,
            db=db,
        )

    # ------------------------------------------------------------------ #
    # Pipeline
    # ------------------------------------------------------------------ #

    def process(self, raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run the full pipeline and persist every correlated incident.

        Args:
            raw_events: raw event dicts; both the demo dataset schema
                (``destination_ip``, ``destination_asset``,
                ``failed_attempts``, ``raw_severity``, ``details``) and the
                EventInput schema (``dest_ip``, ``asset``, ``attempts``)
                are accepted.

        Returns:
            A list of saved incident summary dicts (each carries ``id``,
            ``total_score``, ``severity_label``, ``asset``, ...).

        Raises:
            RuntimeError: if the anomaly detector or DB session is missing.
            ValidationError: if a raw event cannot be coerced to EventInput.
        """
        if self.detector is None:
            raise RuntimeError("Anomaly detector is not available")
        if self.db is None:
            raise RuntimeError(
                "Database session is not bound; use with_db() per request"
            )

        # Runtime configuration (anomaly threshold, severity bands,
        # pre-caching switch) loaded once per run from the settings row.
        settings = load_settings()

        # Steps 1-2: normalize each raw event, then run anomaly detection.
        working = [
            self._normalize_and_detect(raw, settings) for raw in raw_events
        ]

        # Step 3: correlate events into incidents.
        incidents = self.correlator.correlate(working)

        # Steps 4-7: score, retrieve threat intel, explain, and persist.
        summaries: List[Dict[str, Any]] = []
        failed = 0
        for incident in incidents:
            try:
                summaries.append(self._process_incident(incident, settings))
            except SQLAlchemyError:
                self.db.rollback()
                failed += 1
                logger.exception(
                    "Failed to persist incident %s; rolled back.",
                    incident.get("id"),
                )

        self.last_run = {
            "events_received": len(raw_events),
            "incidents_created": len(summaries),
            "incidents_failed": failed,
        }
        logger.info(
            "Pipeline complete: %d events -> %d incidents (%d persisted, %d failed).",
            len(raw_events),
            len(incidents),
            len(summaries),
            failed,
        )
        return summaries

    # ------------------------------------------------------------------ #
    # Steps 1-2: normalization and anomaly detection
    # ------------------------------------------------------------------ #

    def _normalize_and_detect(
        self, raw: Dict[str, Any], settings: PipelineSettings
    ) -> Dict[str, Any]:
        """Normalize one raw event dict and attach anomaly scores."""
        event_input = self._to_event_input(raw)
        event_dict = normalize_event(event_input).model_dump(mode="json")
        event_dict["severity"] = str(
            raw.get("raw_severity") or raw.get("severity") or "low"
        ).lower()
        event_dict["details"] = str(raw.get("details") or "")
        detection = self.detector.detect(
            event_dict, threshold=settings.anomaly_threshold
        )
        event_dict["anomaly_score"] = detection["anomaly_score"]
        event_dict["is_anomaly"] = detection["is_anomaly"]
        return event_dict

    @staticmethod
    def _to_event_input(raw: Dict[str, Any]) -> EventInput:
        """Coerce a raw event dict (demo or EventInput schema) to EventInput."""
        return EventInput(
            event_id=str(raw.get("event_id") or uuid4()),
            timestamp=raw.get("timestamp"),
            source_ip=raw.get("source_ip"),
            dest_ip=raw.get("dest_ip") or raw.get("destination_ip"),
            event_type=str(raw.get("event_type") or "unknown"),
            username=raw.get("username"),
            attempts=int(raw.get("attempts") or raw.get("failed_attempts") or 0),
            bytes_transferred=int(raw.get("bytes_transferred") or 0),
            port=int(raw.get("port") or 0),
            asset=raw.get("asset") or raw.get("destination_asset") or "unknown",
            asset_criticality=str(raw.get("asset_criticality") or "low").lower(),
            protocol=raw.get("protocol") or "TCP",
            raw_payload=raw,
        )

    # ------------------------------------------------------------------ #
    # Steps 4-7: score, retrieve, explain, persist (per incident)
    # ------------------------------------------------------------------ #

    def _process_incident(
        self, incident: Dict[str, Any], settings: PipelineSettings
    ) -> Dict[str, Any]:
        """Enrich and persist one incident; return its summary dict."""
        events = incident.get("events") or []
        max_anomaly = max(
            (float(e.get("anomaly_score") or 0.0) for e in events), default=0.0
        )
        incident["max_anomaly_score"] = max_anomaly

        # Step 4: composite risk scoring.
        score_factors = self.scorer.calculate(
            self._scoring_input(incident, events), max_anomaly
        )
        incident["score_factors"] = score_factors
        incident["total_score"] = score_factors.total_score
        incident["severity_label"] = score_to_label(
            score_factors.total_score, settings
        )

        # Step 5: RAG retrieval (skipped gracefully when KB is unavailable).
        rag_results: List[RAGResult] = []
        if self.rag_retriever is not None:
            try:
                rag_results = self.rag_retriever.retrieve(incident)
            except Exception:  # noqa: BLE001 - retrieval must not break ingest
                logger.exception(
                    "RAG retrieval failed for incident %s.", incident["id"]
                )
        incident["rag_results"] = rag_results

        # Step 6: LLM explanation for incidents at or above the configured
        # high-severity band, and only when pre-caching is enabled; when it
        # is disabled, no LLM call happens at ingest time and the stored
        # rule-based explanation is upgraded lazily on first detail view.
        explanation: Optional[ExplanationResult] = None
        if (
            settings.enable_precaching
            and incident["total_score"] >= settings.severity_high_min
            and self.explainer is not None
        ):
            try:
                explanation = self.explainer.explain(
                    incident, score_factors.to_breakdown_dict(), rag_results
                )
            except Exception:  # noqa: BLE001 - explanation must not break ingest
                logger.exception(
                    "LLM explanation failed for incident %s.", incident["id"]
                )
        if explanation is None:
            explanation = generate_rule_based_explanation(incident)
        incident["explanation"] = explanation

        # Step 7: persist the incident aggregate in one transaction.
        return self._save_incident(incident, events, score_factors, rag_results,
                                   explanation, max_anomaly)

    def _scoring_input(
        self, incident: Dict[str, Any], events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build the RiskScorer input, deriving exploit/TI flags from evidence."""
        details_blob = " ".join(
            str(e.get("details") or "").lower() for e in events if isinstance(e, dict)
        )
        has_active_exploit = any(
            indicator in details_blob for indicator in self.ACTIVE_EXPLOIT_INDICATORS
        )
        has_known_exploit = has_active_exploit or any(
            indicator in details_blob for indicator in self.KNOWN_EXPLOIT_INDICATORS
        )
        high_relevance_ti = any(
            indicator in details_blob for indicator in self.HIGH_TI_INDICATORS
        )
        return {
            "severity": incident.get("severity"),
            "asset_criticality": incident.get("asset_criticality"),
            "has_known_exploit": has_known_exploit,
            "has_active_exploit": has_active_exploit,
            "events": events,
            "latest_event_time": incident.get("latest_event_time"),
            "mitre_technique_matched": bool(incident.get("mitre_technique")),
            "high_relevance_ti": high_relevance_ti,
        }

    def _save_incident(
        self,
        incident: Dict[str, Any],
        events: List[Dict[str, Any]],
        score_factors: ScoreFactors,
        rag_results: List[RAGResult],
        explanation: ExplanationResult,
        max_anomaly: float,
    ) -> Dict[str, Any]:
        """Persist one incident aggregate; return its summary dict."""
        created_at = incident.get("created_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc).replace(tzinfo=None)

        row = IncidentModel(
            id=incident["id"],
            created_at=created_at,
            status="active",
            severity_label=incident["severity_label"],
            latest_event_time=incident.get("latest_event_time"),
            asset=incident.get("asset") or "unknown",
            asset_criticality=incident.get("asset_criticality") or "low",
            total_score=incident["total_score"],
            mitre_technique=incident.get("mitre_technique"),
            confidence=explanation.confidence,
        )
        row.events = [
            self._build_event_row(incident["id"], event) for event in events
        ]
        row.score_factors = ScoreFactorsModel(
            incident_id=incident["id"],
            base_severity=score_factors.base_severity,
            anomaly_score_pts=score_factors.anomaly_score_pts,
            asset_criticality_pts=score_factors.asset_criticality_pts,
            exploitability_pts=score_factors.exploitability_pts,
            evidence_count_pts=score_factors.evidence_count_pts,
            recency_pts=score_factors.recency_pts,
            ti_relevance_pts=score_factors.ti_relevance_pts,
            anomaly_score_raw=max_anomaly,
        )
        row.rag_results = [
            RAGResultModel(
                incident_id=incident["id"],
                content=str(r.get("content") or ""),
                source=str(r.get("source") or ""),
                technique_id=r.get("technique_id"),
                cve_id=r.get("cve_id"),
                relevance_score=float(r.get("relevance_score") or 0.0),
            )
            for r in rag_results
        ]
        row.llm_explanation = LLMExplanationModel(
            incident_id=incident["id"],
            observed_evidence=explanation.observed_evidence,
            retrieved_context=explanation.retrieved_context,
            ai_interpretation=explanation.ai_interpretation,
            recommended_action=explanation.recommended_action,
            confidence=explanation.confidence,
            confidence_reason=explanation.confidence_reason,
            error=explanation.error,
        )

        self.db.add(row)
        self.db.commit()

        return {
            "id": incident["id"],
            "created_at": created_at.isoformat(),
            "status": "active",
            "asset": row.asset,
            "asset_criticality": row.asset_criticality,
            "total_score": row.total_score,
            "severity_label": row.severity_label,
            "mitre_technique": row.mitre_technique,
            "latest_event_time": (
                row.latest_event_time.isoformat() if row.latest_event_time else None
            ),
            "events_count": len(events),
            "confidence": row.confidence,
        }

    @staticmethod
    def _build_event_row(incident_id: str, event: Dict[str, Any]) -> EventModel:
        """Build an EventModel row; a fresh UUID is used so re-ingesting the
        same source data never collides on the primary key."""
        timestamp = event.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = None
        if isinstance(timestamp, datetime):
            timestamp = timestamp.replace(tzinfo=None)
        else:
            timestamp = None

        return EventModel(
            id=str(uuid4()),
            incident_id=incident_id,
            timestamp=timestamp,
            source_ip=event.get("source_ip"),
            dest_ip=event.get("dest_ip"),
            event_type=str(event.get("event_type") or "unknown"),
            raw_data=json.dumps(event, default=str),
        )
