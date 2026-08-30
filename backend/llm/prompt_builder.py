"""Prompt construction for the ThreatIQ LLM reasoning layer.

Builds the (system, user) prompt pair sent to the LLM for incident
explanation. The system prompt fixes the analyst-assistant behavior and
output schema; the user prompt carries only grounded evidence: the incident
summary, the composite risk score breakdown, and retrieved threat
intelligence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

if TYPE_CHECKING:
    from backend.rag.rag_retriever import RAGResult

SYSTEM_PROMPT = """You are a precise, evidence-based security analyst assistant.

You will receive:
1. An incident summary with detected events and composite risk score breakdown.
2. Retrieved threat intelligence context (from MITRE ATT&CK and CVE database).

Your job is to produce a structured JSON response with exactly these fields:

{
  "observed_evidence": "A concise 2-3 sentence description of what the system actually detected, using only the provided event data.",
  "retrieved_context": "A 2-3 sentence summary of the retrieved threat intelligence context that is relevant to this incident. Always cite the source ID (e.g., MITRE T1110.001, CVE-XXXX).",
  "ai_interpretation": "A 2-3 sentence analytical conclusion connecting the observed evidence to the retrieved context and explaining why this incident has a high composite risk score.",
  "recommended_action": "One specific, actionable recommendation for the analyst. Be concrete: name the asset, the action, and the expected outcome.",
  "confidence": "high | medium | low based on the strength of evidence",
  "confidence_reason": "One sentence explaining the confidence level."
}

RULES:
- Never invent event details not present in the input.
- Never cite sources you did not receive in the retrieved context.
- If evidence is weak, state so explicitly and lower confidence.
- Use professional security analyst language, not casual language.
- Do not explain what MITRE ATT&CK is — assume the analyst knows."""

# Rough 4-chars-per-token budget to keep the user prompt under 2000 tokens.
MAX_USER_PROMPT_CHARS = 8000
MAX_RAG_CONTENT_CHARS = 400
MAX_RAG_RESULTS = 6


def build_incident_prompt(
    incident_dict: Dict[str, Any],
    score_factors_dict: Dict[str, Any],
    rag_results_list: List[RAGResult],
) -> Tuple[str, str]:
    """Build the (system_prompt, user_prompt) pair for an incident.

    Args:
        incident_dict: incident payload (id/incident_id, asset,
            asset_criticality, latest_event_time, mitre_technique, events).
        score_factors_dict: ScoreFactors.to_breakdown_dict() output with
            ``factors`` (points/max_points/reason) and ``total_score``.
        rag_results_list: retrieved RAGResult entries from the RAG layer.

    Returns:
        (system_prompt, user_prompt) where the user prompt stays within a
        ~2000-token character budget.
    """
    user_prompt = "\n\n".join(
        [
            _incident_summary_block(incident_dict),
            _risk_score_block(score_factors_dict),
            _threat_intel_block(rag_results_list),
        ]
    )
    if len(user_prompt) > MAX_USER_PROMPT_CHARS:
        user_prompt = user_prompt[:MAX_USER_PROMPT_CHARS] + "\n[... truncated]"
    return SYSTEM_PROMPT, user_prompt


# ------------------------------------------------------------------ #
# Section builders
# ------------------------------------------------------------------ #


def _incident_summary_block(incident_dict: Dict[str, Any]) -> str:
    """Format the INCIDENT SUMMARY section from the incident payload."""
    events = [e for e in incident_dict.get("events") or [] if isinstance(e, dict)]
    event_types = sorted({str(e.get("event_type")) for e in events if e.get("event_type")})
    source_ips = sorted({str(e.get("source_ip")) for e in events if e.get("source_ip")})

    incident_id = incident_dict.get("incident_id") or incident_dict.get("id") or "unknown"
    mitre_technique = incident_dict.get("mitre_technique") or "unknown"

    lines = [
        "INCIDENT SUMMARY:",
        f"- incident_id: {incident_id}",
        f"- latest_event_time: {incident_dict.get('latest_event_time', 'unknown')}",
        f"- asset: {incident_dict.get('asset', 'unknown')}",
        f"- asset_criticality: {incident_dict.get('asset_criticality', 'unknown')}",
        f"- event_types_detected: [{', '.join(event_types) or 'none'}]",
        f"- source_ips: [{', '.join(source_ips) or 'none'}]",
        f"- mitre_technique_if_known: {mitre_technique}",
    ]
    return "\n".join(lines)


def _risk_score_block(score_factors_dict: Dict[str, Any]) -> str:
    """Format the COMPOSITE RISK SCORE section with per-factor points."""
    total = score_factors_dict.get("total_score", 0)
    lines = [
        "COMPOSITE RISK SCORE:",
        f"- total_score: {total}/100",
    ]
    for factor in score_factors_dict.get("factors") or []:
        name = factor.get("factor", "Unknown Factor")
        points = factor.get("points", 0)
        max_points = factor.get("max_points", 0)
        reason = factor.get("reason") or ""
        line = f"- {name}: {points}/{max_points}"
        if reason:
            line += f" ({reason})"
        lines.append(line)
    return "\n".join(lines)


def _threat_intel_block(rag_results_list: List[RAGResult]) -> str:
    """Format the RETRIEVED THREAT INTELLIGENCE section (<=6 docs)."""
    lines = ["RETRIEVED THREAT INTELLIGENCE:"]
    results = list(rag_results_list or [])[:MAX_RAG_RESULTS]
    if not results:
        lines.append("[Source: system] No specific threat intelligence retrieved.")
        return "\n".join(lines)
    for result in results:
        source = (
            result.get("technique_id")
            or result.get("cve_id")
            or result.get("source")
            or "unknown"
        )
        content = str(result.get("content", ""))[:MAX_RAG_CONTENT_CHARS]
        lines.append(f"[Source: {source}]")
        lines.append(content)
    return "\n".join(lines)
