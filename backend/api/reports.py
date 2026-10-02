"""Report export API routes for ThreatIQ.

Exposes GET /api/reports/export: renders the full current incident queue
(with score factors, LLM explanations, and RAG citations) into a
downloadable PDF.
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
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
from backend.api.llm_config import get_session_llm_config
from backend.database.db import EventModel, IncidentModel, get_db
from backend.reports.report_builder import build_incident_report_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_LLM_TIMEOUT_SECONDS = 25.0
DEFAULT_REPORT_MODEL = "gemini-3.6-flash"
DEFAULT_REPORT_TEMPERATURE = 0.2
GEMINI_FALLBACK_MODELS = (
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
)

REPORT_SUMMARY_SYSTEM_PROMPT = (
    "You are generating an executive security summary from supplied ThreatIQ analysis data.\n\n"
    "CRITICAL GROUNDING RULES:\n"
    "- Use ONLY the provided information.\n"
    "- Do not invent facts.\n"
    "- Do not assume facts that are not present.\n"
    "- Do not create or guess IP addresses, usernames, asset names, CVEs, MITRE IDs, attack stages, or commands not present in the data.\n"
    "- When RAG-derived information is mentioned, only use source IDs (such as MITRE technique IDs or CVE IDs) actually present in the supplied RAG context. Never fabricate source IDs.\n"
    "- If something is unknown or unavailable, say that it is unavailable.\n"
    "- Prefer simple, professional language that a SOC analyst or technical manager can understand quickly.\n"
    "- The goal is to summarize the existing analysis, not to perform a new investigation.\n"
    "- Do NOT explain what ThreatIQ, MITRE ATT&CK, RAG, Isolation Forest, or CVEs are.\n"
    "- Do NOT generate generic cybersecurity filler (e.g. 'Cybersecurity is important...', 'The organization should stay vigilant...').\n"
    "- Every sentence must be connected to the actual supplied report data.\n\n"
    "STYLE AND FORMAT RULES:\n"
    "- overall_security_picture: Exactly 2-3 concise sentences in easy-to-understand professional English summarizing the overall security situation from the data.\n"
    "- key_findings: Up to 3 short bullets. Each must identify a meaningful observation (e.g., key threat pattern, repeatedly affected asset, MITRE technique, critical incident, or alert reduction result).\n"
    "- recommended_actions: 2 to 3 concise, actionable recommendations for analysts or managers grounded in the supplied incident data, affected assets, severities, techniques, and existing incident recommendations.\n"
    "- confidence: 'high', 'medium', or 'low'.\n"
    "- confidence_reason: Exactly one concise sentence explaining the confidence rating."
)


class ReportSummaryResult(BaseModel):
    """Structured report-level executive summary produced by the LLM."""

    overall_security_picture: str
    key_findings: List[str]
    recommended_actions: List[str]
    confidence: Literal["high", "medium", "low"]
    confidence_reason: str


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

    # Generate AI executive summary (failsafe: failure logs error and continues)
    ai_summary: Optional[Dict[str, Any]] = None
    try:
        ai_summary = _generate_report_ai_summary(incidents_data, alert_reduction_pct)
    except Exception as exc:  # noqa: BLE001 - AI summary must never fail export
        logger.warning(
            "Failed to generate AI executive summary for report: %s",
            exc,
            exc_info=True,
        )
        ai_summary = None

    try:
        pdf_bytes = build_incident_report_pdf(
            incidents_data, alert_reduction_pct, ai_summary=ai_summary
        )
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


def _build_report_client() -> Any:
    """Build a structured-output LLM chain for report-level summary.

    Reuses the active session LLM configuration if present; falls back to
    GEMINI_API_KEY/GOOGLE_API_KEY from environment.
    """
    session_config = get_session_llm_config()

    if session_config is not None:
        provider = (session_config.provider or "").strip().lower()
        model = session_config.model
        api_key = session_config.api_key
        base_url = session_config.base_url
    else:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No LLM API key configured: set GEMINI_API_KEY or GOOGLE_API_KEY, "
                "or configure a provider via the settings page."
            )
        provider = "gemini"
        model = os.getenv("LLM_MODEL", DEFAULT_REPORT_MODEL)
        base_url = None

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=DEFAULT_REPORT_TEMPERATURE,
            max_retries=0,
        )
    elif provider in ("openai", "local"):
        from langchain_openai import ChatOpenAI

        kwargs: Dict[str, Any] = {
            "model": model,
            "api_key": api_key,
            "temperature": DEFAULT_REPORT_TEMPERATURE,
            "request_timeout": REPORT_LLM_TIMEOUT_SECONDS,
            "max_retries": 0,
        }
        if base_url:
            kwargs["base_url"] = base_url
        llm = ChatOpenAI(**kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider!r} (expected 'gemini', 'openai', or 'local')"
        )

    return llm.with_structured_output(ReportSummaryResult)


def _invoke_chain_with_timeout(
    chain: Any, messages: List[Any], timeout: float = REPORT_LLM_TIMEOUT_SECONDS
) -> Any:
    """Invoke the LLM chain, enforcing REPORT_LLM_TIMEOUT_SECONDS deadline."""
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(chain.invoke, messages)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeoutError:
        future.cancel()
        raise TimeoutError(
            f"Report AI summary exceeded {timeout}s deadline"
        ) from None
    finally:
        pool.shutdown(wait=False)


def _build_report_context(
    incidents_data: List[Dict[str, Any]],
    alert_reduction_pct: float,
) -> str:
    """Build a compact bounded context string from incidents_data."""
    total_events = sum(
        inc.get("events_count") or len(inc.get("events") or [])
        for inc in incidents_data
    )
    total_incidents = len(incidents_data)
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for inc in incidents_data:
        sev = (inc.get("severity_label") or "").lower()
        if sev in counts:
            counts[sev] += 1

    lines = [
        "=== OVERALL METRICS ===",
        f"Total Events: {total_events}",
        f"Total Incidents: {total_incidents}",
        f"Critical Incidents: {counts['critical']}",
        f"High Incidents: {counts['high']}",
        f"Medium Incidents: {counts['medium']}",
        f"Low Incidents: {counts['low']}",
        f"Correlation Alert Reduction: {alert_reduction_pct}%",
        "",
    ]

    # Top affected assets (using same logic as _top_assets_table)
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    asset_groups: Dict[str, List[Any]] = {}
    for inc in incidents_data:
        asset = str(inc.get("asset") or "unknown").strip()
        sev = (inc.get("severity_label") or "").lower()
        rank = sev_rank.get(sev, 4)
        entry = asset_groups.setdefault(asset, [0, 4])
        entry[0] += 1
        entry[1] = min(entry[1], rank)

    ordered_assets = sorted(
        asset_groups.items(), key=lambda item: (item[1][1], -item[1][0])
    )[:6]
    lines.append("=== TOP AFFECTED ASSETS ===")
    if not ordered_assets:
        lines.append("No affected assets.")
    else:
        sev_order = ("critical", "high", "medium", "low")
        for asset, (cnt, rk) in ordered_assets:
            highest_sev = sev_order[rk] if rk < len(sev_order) else "unknown"
            lines.append(
                f"- Asset: {asset}, Incidents: {cnt}, Highest Severity: {highest_sev}"
            )
    lines.append("")

    # Top MITRE techniques (using same logic as _techniques_table)
    tech_counts: Dict[str, int] = {}
    for inc in incidents_data:
        tech = str(inc.get("mitre_technique") or "").strip()
        if not tech or tech == "-":
            continue
        tech_counts[tech] = tech_counts.get(tech, 0) + 1

    ordered_techs = sorted(
        tech_counts.items(), key=lambda item: item[1], reverse=True
    )[:8]
    lines.append("=== TOP OBSERVED MITRE TECHNIQUES ===")
    if not ordered_techs:
        lines.append("No MITRE techniques tagged.")
    else:
        for tech, cnt in ordered_techs:
            lines.append(f"- {tech}: {cnt} incident(s)")
    lines.append("")

    # Top incidents (highest-scoring, prioritizing critical/high then medium/low, capped at 5)
    crit_high = [
        inc
        for inc in incidents_data
        if (inc.get("severity_label") or "").lower() in ("critical", "high")
    ]
    crit_high_sorted = sorted(
        crit_high, key=lambda inc: inc.get("total_score") or 0, reverse=True
    )
    others = [
        inc
        for inc in incidents_data
        if (inc.get("severity_label") or "").lower() not in ("critical", "high")
    ]
    others_sorted = sorted(
        others, key=lambda inc: inc.get("total_score") or 0, reverse=True
    )
    top_incidents = (crit_high_sorted + others_sorted)[:5]

    lines.append("=== TOP HIGH-PRIORITY INCIDENTS (MAX 5) ===")
    if not top_incidents:
        lines.append("No incidents available.")
    else:
        for inc in top_incidents:
            inc_id = str(inc.get("id") or "unknown")[:8]
            sev = str(inc.get("severity_label") or "unknown").upper()
            score = inc.get("total_score") or 0
            asset = str(inc.get("asset") or "unknown")[:40]
            crit = str(inc.get("asset_criticality") or "unknown")
            tech = str(inc.get("mitre_technique") or "none")[:30]
            events_cnt = inc.get("events_count") or len(inc.get("events") or [])
            latest_time = str(inc.get("latest_event_time") or "unknown")[:30]

            explanation = inc.get("llm_explanation") or {}
            raw_evidence = str(explanation.get("observed_evidence") or "").strip()
            raw_interpretation = str(explanation.get("ai_interpretation") or "").strip()
            raw_action = str(explanation.get("recommended_action") or "").strip()
            confidence = str(explanation.get("confidence") or "").strip()

            if not raw_evidence or raw_evidence.startswith("LLM explanation unavailable"):
                evidence = f"{events_cnt} correlated event(s) recorded on asset {asset}."
            else:
                evidence = raw_evidence[:200]

            if not raw_interpretation or raw_interpretation.startswith("LLM explanation unavailable"):
                interpretation = f"Composite risk score is {score}/100 ({sev}) targeting {crit} asset {asset}."
            else:
                interpretation = raw_interpretation[:200]

            if not raw_action or raw_action.startswith("LLM explanation unavailable"):
                action = f"Investigate priority activity on {asset} ({sev}) and review associated {tech} events."
            else:
                action = raw_action[:200]

            rag_citations: List[str] = []
            for r in (inc.get("rag_results") or []):
                cid = r.get("technique_id") or r.get("cve_id") or r.get("id")
                if cid and str(cid) not in rag_citations:
                    rag_citations.append(str(cid))

            lines.append(f"Incident {inc_id}:")
            lines.append(
                f"  Severity: {sev}, Score: {score}, Asset: {asset} (Criticality: {crit})"
            )
            lines.append(
                f"  MITRE Technique: {tech}, Event Count: {events_cnt}, Latest Event: {latest_time}"
            )
            if evidence:
                lines.append(f"  Observed Evidence: {evidence}")
            if interpretation:
                lines.append(f"  Stored AI Interpretation: {interpretation}")
            if action:
                lines.append(f"  Stored Recommended Action: {action}")
            if confidence:
                lines.append(f"  Stored Confidence: {confidence}")
            if rag_citations:
                lines.append(f"  RAG Citations Available: {', '.join(rag_citations)}")
            lines.append("")

    full_context = "\n".join(lines)
    return full_context[:10000]


def _generate_report_ai_summary(
    incidents_data: List[Dict[str, Any]],
    alert_reduction_pct: float,
) -> Optional[Dict[str, Any]]:
    """Generate a single grounded report-level AI executive summary.

    Uses active session LLM config if present, or falls back to env vars.
    Returns a dict conforming to ReportSummaryResult, or None on failure.
    """
    context = _build_report_context(incidents_data, alert_reduction_pct)
    user_prompt = (
        "Generate a report-level executive security summary from the following "
        "ThreatIQ incident and metrics data:\n\n" + context
    )

    from langchain_core.messages import HumanMessage, SystemMessage

    messages = [
        SystemMessage(content=REPORT_SUMMARY_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    session_config = get_session_llm_config()

    if session_config is not None:
        provider = (session_config.provider or "").strip().lower()
        model = session_config.model
        api_key = session_config.api_key
        base_url = session_config.base_url
    else:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No LLM API key configured: set GEMINI_API_KEY or GOOGLE_API_KEY, "
                "or configure a provider via the settings page."
            )
        provider = "gemini"
        model = os.getenv("LLM_MODEL", DEFAULT_REPORT_MODEL)
        base_url = None

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Try configured model first; if 429 quota exhausted or 503 unavailable, try fallbacks
        candidates = [model]
        for fb in GEMINI_FALLBACK_MODELS:
            if fb not in candidates:
                candidates.append(fb)

        def _invoke_gemini_candidates() -> Any:
            last_err: Optional[Exception] = None
            per_model_timeout = 10.0
            for cand in candidates:
                worker_pool = ThreadPoolExecutor(max_workers=1)
                try:
                    llm = ChatGoogleGenerativeAI(
                        model=cand,
                        api_key=api_key,
                        temperature=DEFAULT_REPORT_TEMPERATURE,
                        max_retries=0,
                    )
                    chain = llm.with_structured_output(ReportSummaryResult)
                    future = worker_pool.submit(chain.invoke, messages)
                    return future.result(timeout=per_model_timeout)
                except Exception as exc:
                    logger.warning(
                        "Report AI summary attempt with model %s failed: %s",
                        cand,
                        exc,
                    )
                    last_err = exc
                finally:
                    worker_pool.shutdown(wait=False)
            if last_err is not None:
                raise last_err
            raise RuntimeError("All Gemini candidate models failed")

        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(_invoke_gemini_candidates)
        try:
            raw_result = future.result(timeout=REPORT_LLM_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            future.cancel()
            raise TimeoutError(
                f"Report AI summary exceeded {REPORT_LLM_TIMEOUT_SECONDS}s deadline"
            ) from None
        finally:
            pool.shutdown(wait=False)

    elif provider in ("openai", "local"):
        from langchain_openai import ChatOpenAI

        kwargs: Dict[str, Any] = {
            "model": model,
            "api_key": api_key,
            "temperature": DEFAULT_REPORT_TEMPERATURE,
            "request_timeout": REPORT_LLM_TIMEOUT_SECONDS,
            "max_retries": 0,
        }
        if base_url:
            kwargs["base_url"] = base_url
        llm = ChatOpenAI(**kwargs)
        chain = llm.with_structured_output(ReportSummaryResult)
        raw_result = _invoke_chain_with_timeout(
            chain, messages, timeout=REPORT_LLM_TIMEOUT_SECONDS
        )
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider!r} (expected 'gemini', 'openai', or 'local')"
        )

    if isinstance(raw_result, ReportSummaryResult):
        return raw_result.model_dump()
    if isinstance(raw_result, dict):
        return ReportSummaryResult.model_validate(raw_result).model_dump()
    return ReportSummaryResult.model_validate(raw_result).model_dump()


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
