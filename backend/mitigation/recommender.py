"""Recommendation engine for the ThreatIQ mitigation layer.

Guarantees one specific, conservative, urgency-ranked recommendation per
incident. The LLM-generated ``recommended_action`` (Phase 12) is preferred,
but it must pass two gates before being shown to an analyst:

- Specificity: names the asset, uses an action verb, and states an outcome.
- Conservatism: recommends isolation/investigation, never autonomous
  blocking or destructive changes.

If the LLM action fails either gate (or no LLM explanation exists), a
deterministic rule-based fallback is produced from the MITRE technique or
the detected event types, so every incident always has an actionable
recommendation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel


class RecommendationUrgency(str, Enum):
    """Urgency ranking derived from incident severity."""

    IMMEDIATE = "immediate"  # CRITICAL incidents — act now
    HIGH = "high"            # HIGH incidents — act today
    MEDIUM = "medium"        # MEDIUM incidents — schedule investigation
    MONITOR = "monitor"      # LOW incidents — monitoring only


class Recommendation(BaseModel):
    """One specific, actionable recommendation for an incident."""

    incident_id: str
    action: str
    urgency: RecommendationUrgency
    expected_outcome: str
    source: Literal["llm", "fallback"]
    conservative: bool = True
    rationale: str = ""


# ------------------------------------------------------------------ #
# Urgency ranking
# ------------------------------------------------------------------ #

_URGENCY_BY_SEVERITY: Dict[str, RecommendationUrgency] = {
    "critical": RecommendationUrgency.IMMEDIATE,
    "high": RecommendationUrgency.HIGH,
    "medium": RecommendationUrgency.MEDIUM,
    "low": RecommendationUrgency.MONITOR,
}

# Score thresholds used when no severity label is available.
_URGENCY_SCORE_BANDS: List[Tuple[int, RecommendationUrgency]] = [
    (80, RecommendationUrgency.IMMEDIATE),
    (60, RecommendationUrgency.HIGH),
    (40, RecommendationUrgency.MEDIUM),
]

# ------------------------------------------------------------------ #
# Conservatism and specificity gates
# ------------------------------------------------------------------ #

# Phrases that indicate autonomous blocking / destructive change. The layer
# recommends isolation and investigation, never these.
_DESTRUCTIVE_PATTERNS: Tuple[str, ...] = (
    "block the ip",
    "block ip",
    "drop all traffic",
    "drop packets",
    "deny all",
    "blackhole",
    "delete the account",
    "delete account",
    "shut down",
    "shutdown",
    "kill the process",
    "kill process",
    "wipe",
    "erase",
    "format the",
    "permanently ban",
)

_ACTION_VERBS: Tuple[str, ...] = (
    "isolate",
    "investigate",
    "review",
    "reset",
    "collect",
    "monitor",
    "contain",
    "verify",
    "audit",
    "inspect",
    "restrict",
    "enable",
    "enforce",
    "capture",
    "preserve",
    "escalate",
)

_MIN_SPECIFIC_ACTION_CHARS = 40

# ------------------------------------------------------------------ #
# Rule-based fallback templates (per MITRE technique / event type)
# ------------------------------------------------------------------ #

_TECHNIQUE_FALLBACKS: Dict[str, Tuple[str, str]] = {
    "T1110.001": (
        "Isolate {asset} from the network segment, enforce a password reset "
        "and MFA enrollment check for all accounts targeted from {source_ips}, "
        "and review authentication logs on {asset} for any successful logins "
        "during the attack window",
        "Credential-guessing attempts are contained and any compromised "
        "credentials are invalidated before lateral movement occurs",
    ),
    "T1046": (
        "Isolate {asset} behind a temporary ACL restricting inbound traffic, "
        "then investigate which services the scan from {source_ips} enumerated "
        "and close or patch any unexpectedly exposed ports",
        "Reconnaissance is contained and the exposed attack surface on "
        "{asset} is reduced before exploitation is attempted",
    ),
    "T1041": (
        "Isolate {asset} from outbound network access, preserve egress and "
        "proxy logs involving {source_ips}, and investigate which data left "
        "the host during the exfiltration window",
        "Data exfiltration is stopped and forensic evidence is preserved "
        "for scoping the impact",
    ),
    "T1059": (
        "Collect the full process tree and command-line history on {asset}, "
        "run an EDR scan for persistence mechanisms, and restrict script "
        "execution policy on {asset} while the origin of the commands from "
        "{source_ips} is investigated",
        "Malicious command execution is halted and persistence mechanisms "
        "are identified for removal",
    ),
}

_EVENT_TYPE_FALLBACKS: Dict[str, Tuple[str, str]] = {
    "authentication_failure": _TECHNIQUE_FALLBACKS["T1110.001"],
    "port_scan": _TECHNIQUE_FALLBACKS["T1046"],
    "data_exfiltration": _TECHNIQUE_FALLBACKS["T1041"],
    "process_spawn": _TECHNIQUE_FALLBACKS["T1059"],
}

_GENERIC_FALLBACK: Tuple[str, str] = (
    "Isolate {asset} from non-essential network traffic, collect the full "
    "event logs involving {source_ips}, and open an investigation ticket to "
    "triage the correlated events",
    "The suspicious activity is contained while analysts determine scope "
    "and root cause",
)


class RecommendationEngine:
    """Produces one validated recommendation per incident."""

    def recommend(
        self,
        incident_dict: Dict[str, Any],
        score_factors_dict: Optional[Dict[str, Any]] = None,
        llm_explanation: Optional[Any] = None,
    ) -> Recommendation:
        """Return the recommendation for an incident.

        Prefers the LLM-generated action when it passes the specificity and
        conservatism gates; otherwise falls back to a deterministic template.
        Never returns an empty action.

        Args:
            incident_dict: incident payload (id/incident_id, asset,
                severity_label or severity, mitre_technique, events).
            score_factors_dict: optional ScoreFactors breakdown dict, used
                for urgency ranking when no severity label is present.
            llm_explanation: optional ExplanationResult or dict with a
                ``recommended_action`` field.

        Returns:
            A fully populated Recommendation with a non-empty action.
        """
        incident_id = str(
            incident_dict.get("incident_id") or incident_dict.get("id") or "unknown"
        )
        urgency = self._rank_urgency(incident_dict, score_factors_dict)

        llm_action = self._extract_llm_action(llm_explanation)
        if llm_action and self._passes_gates(llm_action, incident_dict):
            return Recommendation(
                incident_id=incident_id,
                action=self._frame_urgency(llm_action, urgency),
                urgency=urgency,
                expected_outcome="",
                source="llm",
                rationale=(
                    "LLM-generated action validated as specific and conservative"
                ),
            )

        action, outcome, template_source = self._fallback_action(
            incident_dict, urgency
        )
        rationale = (
            "Rule-based fallback used because no specific, conservative "
            "LLM action was available"
        )
        if llm_action:
            rationale = (
                "LLM action rejected by validation gates "
                f"({template_source}); deterministic fallback applied"
            )
        return Recommendation(
            incident_id=incident_id,
            action=action,
            urgency=urgency,
            expected_outcome=outcome,
            source="fallback",
            rationale=rationale,
        )

    # ------------------------------------------------------------------ #
    # Urgency ranking
    # ------------------------------------------------------------------ #

    def _rank_urgency(
        self,
        incident_dict: Dict[str, Any],
        score_factors_dict: Optional[Dict[str, Any]],
    ) -> RecommendationUrgency:
        """Rank urgency from the severity label, falling back to score."""
        label = str(
            incident_dict.get("severity_label")
            or incident_dict.get("severity")
            or ""
        ).lower()
        if label in _URGENCY_BY_SEVERITY:
            return _URGENCY_BY_SEVERITY[label]

        total = 0
        if score_factors_dict:
            try:
                total = int(score_factors_dict.get("total_score", 0))
            except (TypeError, ValueError):
                total = 0
        for threshold, urgency in _URGENCY_SCORE_BANDS:
            if total >= threshold:
                return urgency
        return RecommendationUrgency.MONITOR

    # ------------------------------------------------------------------ #
    # LLM action validation gates
    # ------------------------------------------------------------------ #

    def _extract_llm_action(self, llm_explanation: Optional[Any]) -> Optional[str]:
        """Pull recommended_action from an ExplanationResult or dict."""
        if llm_explanation is None:
            return None
        if isinstance(llm_explanation, dict):
            action = llm_explanation.get("recommended_action")
        else:
            action = getattr(llm_explanation, "recommended_action", None)
        if not action or not isinstance(action, str):
            return None
        action = action.strip()
        return action or None

    def _passes_gates(self, action: str, incident_dict: Dict[str, Any]) -> bool:
        """An LLM action must be both conservative and specific."""
        return self._is_conservative(action) and self._is_specific(
            action, incident_dict
        )

    def _is_conservative(self, action: str) -> bool:
        """Reject actions that imply autonomous blocking or destruction."""
        lowered = action.lower()
        return not any(pattern in lowered for pattern in _DESTRUCTIVE_PATTERNS)

    def _is_specific(self, action: str, incident_dict: Dict[str, Any]) -> bool:
        """Require the asset name, an action verb, and minimal length."""
        lowered = action.lower()
        asset = str(incident_dict.get("asset") or "").strip().lower()
        names_asset = bool(asset) and asset in lowered
        has_verb = any(verb in lowered for verb in _ACTION_VERBS)
        long_enough = len(action) >= _MIN_SPECIFIC_ACTION_CHARS
        return names_asset and has_verb and long_enough

    # ------------------------------------------------------------------ #
    # Fallback templates
    # ------------------------------------------------------------------ #

    def _fallback_action(
        self, incident_dict: Dict[str, Any], urgency: RecommendationUrgency
    ) -> Tuple[str, str, str]:
        """Build a deterministic recommendation; monitoring for LOW urgency.

        Returns:
            (action, expected_outcome, template_source) where
            template_source identifies which template produced the action.
        """
        asset = str(incident_dict.get("asset") or "the affected asset")
        source_ips = self._source_ips_text(incident_dict)

        if urgency is RecommendationUrgency.MONITOR:
            event_types = self._event_types_text(incident_dict)
            return (
                f"Place {asset} under enhanced monitoring for the next 48 "
                f"hours: alert on repeated {event_types} activity from "
                f"{source_ips}, and investigate only if the pattern recurs "
                "or escalates",
                "Recurrence is detected early without disrupting normal "
                f"operations on {asset}",
                "monitoring template (low severity)",
            )

        technique = str(incident_dict.get("mitre_technique") or "").strip()
        template = _TECHNIQUE_FALLBACKS.get(technique)
        source = f"MITRE {technique} template"
        if template is None:
            template = self._event_type_template(incident_dict)
            source = "event-type template"
        if template is None:
            template = _GENERIC_FALLBACK
            source = "generic template"

        action = template[0].format(asset=asset, source_ips=source_ips)
        outcome = template[1].format(asset=asset, source_ips=source_ips)
        return self._frame_urgency(action, urgency), outcome, source

    def _event_type_template(
        self, incident_dict: Dict[str, Any]
    ) -> Optional[Tuple[str, str]]:
        """Pick a fallback template from the detected event types."""
        events = incident_dict.get("events") or []
        for event in events:
            if isinstance(event, dict):
                template = _EVENT_TYPE_FALLBACKS.get(str(event.get("event_type")))
                if template is not None:
                    return template
        return None

    def _frame_urgency(self, action: str, urgency: RecommendationUrgency) -> str:
        """Prefix the action with an urgency cue unless already framed."""
        if urgency is RecommendationUrgency.IMMEDIATE and not action.lower().startswith(
            "immediately"
        ):
            return f"Immediately: {action}"
        return action

    # ------------------------------------------------------------------ #
    # Formatting helpers
    # ------------------------------------------------------------------ #

    def _source_ips_text(self, incident_dict: Dict[str, Any]) -> str:
        """Comma-joined unique source IPs, or a placeholder."""
        events = incident_dict.get("events") or []
        ips = sorted(
            {
                str(e.get("source_ip"))
                for e in events
                if isinstance(e, dict) and e.get("source_ip")
            }
        )
        return ", ".join(ips) if ips else "the observed source"

    def _event_types_text(self, incident_dict: Dict[str, Any]) -> str:
        """Comma-joined unique event types, or a placeholder."""
        events = incident_dict.get("events") or []
        types = sorted(
            {
                str(e.get("event_type"))
                for e in events
                if isinstance(e, dict) and e.get("event_type")
            }
        )
        return ", ".join(types) if types else "suspicious"
