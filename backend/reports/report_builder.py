"""PDF incident report builder for ThreatIQ.

Renders the current incident queue (the same full-detail shape returned by
GET /api/incidents/{id}) into a short, scannable analyst summary PDF:

1. Executive Summary  -- KPIs, top affected assets, techniques observed
2. Priority Action Queue -- deduplicated CRITICAL/HIGH groups (max 20 rows)
3. Critical Incident Briefings -- compact narratives for the top 5 deduped
   CRITICAL incidents

Hard caps everywhere keep the report under ~10 pages regardless of how many
incidents exist in the database.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fpdf import FPDF

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = ("critical", "high", "medium", "low")
_SEVERITY_RANK = {label: rank for rank, label in enumerate(_SEVERITY_ORDER)}

# (R, G, B) text colors per severity label.
_SEVERITY_COLORS = {
    "critical": (200, 30, 30),
    "high": (230, 126, 0),
    "medium": (200, 170, 0),
    "low": (40, 100, 220),
}

_SCORE_FACTOR_LABELS = (
    ("base_severity", "Base"),
    ("anomaly_score_pts", "Anomaly"),
    ("asset_criticality_pts", "Asset"),
    ("exploitability_pts", "Exploit"),
    ("evidence_count_pts", "Evidence"),
    ("recency_pts", "Recency"),
    ("ti_relevance_pts", "TI"),
)

_TOP_ASSETS_CAP = 6
_TOP_TECHNIQUES_CAP = 8
_QUEUE_CAP = 20
_BRIEFING_CAP = 5
_EVIDENCE_DEDUP_PREFIX = 60


def _safe_text(value: Any) -> str:
    """Coerce any value to a latin-1-safe string for core PDF fonts."""
    if value is None:
        return ""
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _short_id(value: Any) -> str:
    """Truncate an incident ID to 8 chars + ellipsis for display."""
    text = _safe_text(value)
    return f"{text[:8]}..." if text else "-"


def _severity_of(incident: Dict[str, Any]) -> str:
    return (incident.get("severity_label") or "").lower()


def _score_of(incident: Dict[str, Any]) -> float:
    return incident.get("total_score") or 0


class _ReportPDF(FPDF):
    """FPDF subclass adding the confidential footer to every page."""

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("helvetica", size=8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0,
            8,
            f"Page {self.page_no()}  |  ThreatIQ - Confidential",
            align="C",
        )
        self.set_text_color(0, 0, 0)


def build_incident_report_pdf(
    incidents_data: List[Dict[str, Any]],
    alert_reduction_pct: Optional[float] = None,
) -> bytes:
    """Build the analyst incident report PDF and return it as raw bytes.

    ``incidents_data`` is a list of full incident dicts (the shape returned
    by GET /api/incidents/{id}). ``alert_reduction_pct`` is the correlation
    alert-reduction metric from GET /api/stats, if available.
    """
    pdf = _ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    _executive_summary_section(pdf, incidents_data, alert_reduction_pct)
    _priority_queue_section(pdf, incidents_data)
    _critical_briefings_section(pdf, incidents_data)

    return bytes(pdf.output())


# ------------------------------------------------------------------ #
# Section 1 -- Executive Summary (fits on page 1)
# ------------------------------------------------------------------ #


def _executive_summary_section(
    pdf: FPDF,
    incidents_data: List[Dict[str, Any]],
    alert_reduction_pct: Optional[float],
) -> None:
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 12, "ThreatIQ Incident Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(
        0,
        6,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    _kpi_block(pdf, incidents_data, alert_reduction_pct)
    pdf.ln(2)
    _top_assets_table(pdf, incidents_data)
    pdf.ln(2)
    _techniques_table(pdf, incidents_data)


def _kpi_block(
    pdf: FPDF,
    incidents_data: List[Dict[str, Any]],
    alert_reduction_pct: Optional[float],
) -> None:
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 8, "Key Metrics", new_x="LMARGIN", new_y="NEXT")

    total_events = sum(incident.get("events_count") or 0 for incident in incidents_data)
    counts: Dict[str, int] = {label: 0 for label in _SEVERITY_ORDER}
    for incident in incidents_data:
        label = _severity_of(incident)
        counts[label] = counts.get(label, 0) + 1

    pdf.set_font("helvetica", size=11)
    pdf.cell(
        0, 6, f"Total events processed: {total_events}", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.cell(
        0, 6, f"Total incidents: {len(incidents_data)}", new_x="LMARGIN", new_y="NEXT"
    )

    x_line: List[Tuple[str, str]] = [
        (label, f"{label.capitalize()}: {counts.get(label, 0)}")
        for label in _SEVERITY_ORDER
    ]
    for index, (label, text) in enumerate(x_line):
        color = _SEVERITY_COLORS[label]
        pdf.set_text_color(*color)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(pdf.get_string_width(text) + 2, 7, text)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", size=11)
        if index < len(x_line) - 1:
            pdf.cell(6, 7, "|")
    pdf.ln()

    if alert_reduction_pct is not None:
        pdf.cell(
            0,
            6,
            f"Alert reduction: {alert_reduction_pct}%",
            new_x="LMARGIN",
            new_y="NEXT",
        )
    pdf.ln(2)


def _top_assets_table(pdf: FPDF, incidents_data: List[Dict[str, Any]]) -> None:
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 8, "Top Affected Assets", new_x="LMARGIN", new_y="NEXT")

    if not incidents_data:
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "No incidents to report.")
        return

    # asset -> [count, highest severity rank]
    groups: Dict[str, List[Any]] = {}
    for incident in incidents_data:
        asset = _safe_text(incident.get("asset") or "unknown")
        rank = _SEVERITY_RANK.get(_severity_of(incident), len(_SEVERITY_ORDER))
        entry = groups.setdefault(asset, [0, len(_SEVERITY_ORDER)])
        entry[0] += 1
        entry[1] = min(entry[1], rank)

    ordered = sorted(groups.items(), key=lambda item: (item[1][1], -item[1][0]))

    widths = (100, 40, 40)
    pdf.set_font("helvetica", "B", 10)
    for header, width in zip(("Asset", "Incidents", "Highest Severity"), widths):
        pdf.cell(width, 7, header, border=1)
    pdf.ln()

    for asset, (count, rank) in ordered[:_TOP_ASSETS_CAP]:
        label = _SEVERITY_ORDER[rank] if rank < len(_SEVERITY_ORDER) else "unknown"
        pdf.set_font("courier", size=9)
        pdf.cell(widths[0], 6, asset[:48], border=1)
        pdf.set_font("helvetica", size=9)
        pdf.cell(widths[1], 6, str(count), border=1)
        pdf.set_text_color(*_SEVERITY_COLORS.get(label, (0, 0, 0)))
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(widths[2], 6, label.upper(), border=1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    remaining = len(ordered) - _TOP_ASSETS_CAP
    if remaining > 0:
        pdf.set_font("helvetica", "I", 9)
        pdf.cell(
            0,
            6,
            f"+{remaining} additional assets, see dashboard",
            new_x="LMARGIN",
            new_y="NEXT",
        )


def _techniques_table(pdf: FPDF, incidents_data: List[Dict[str, Any]]) -> None:
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 8, "Techniques Observed", new_x="LMARGIN", new_y="NEXT")

    counts: Dict[str, int] = {}
    untagged = 0
    for incident in incidents_data:
        technique = _safe_text(incident.get("mitre_technique") or "").strip()
        if not technique or technique == "-":
            untagged += 1
            continue
        counts[technique] = counts.get(technique, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    if not ordered:
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "No MITRE techniques tagged on any incident.")
    else:
        widths = (60, 30)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(widths[0], 7, "Technique", border=1)
        pdf.cell(widths[1], 7, "Count", border=1)
        pdf.ln()
        for technique, count in ordered[:_TOP_TECHNIQUES_CAP]:
            pdf.set_font("courier", size=9)
            pdf.cell(widths[0], 6, technique[:30], border=1)
            pdf.set_font("helvetica", size=9)
            pdf.cell(widths[1], 6, str(count), border=1)
            pdf.ln()

    if incidents_data and untagged / len(incidents_data) > 0.30:
        pdf.set_font("helvetica", "I", 9)
        pdf.cell(
            0,
            6,
            f"{untagged} incidents had no MITRE technique mapped",
            new_x="LMARGIN",
            new_y="NEXT",
        )


# ------------------------------------------------------------------ #
# Section 2 -- Priority Action Queue (deduplicated, capped)
# ------------------------------------------------------------------ #


def _priority_queue_section(pdf: FPDF, incidents_data: List[Dict[str, Any]]) -> None:
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Priority Action Queue", new_x="LMARGIN", new_y="NEXT")

    # Deduplicate by (asset, technique, severity).
    groups: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for incident in incidents_data:
        label = _severity_of(incident)
        if label not in ("critical", "high"):
            continue
        key = (
            _safe_text(incident.get("asset") or "unknown"),
            _safe_text(incident.get("mitre_technique") or "-") or "-",
            label,
        )
        group = groups.setdefault(
            key,
            {"scores": [], "statuses": set(), "count": 0, "id": incident.get("id")},
        )
        group["scores"].append(_score_of(incident))
        group["statuses"].add(_safe_text(incident.get("status") or ""))
        group["count"] += 1

    ordered = sorted(
        groups.items(), key=lambda item: max(item[1]["scores"] or [0]), reverse=True
    )

    if not ordered:
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "No CRITICAL or HIGH incident groups.")
        return

    widths = (26, 62, 34, 22, 16, 24)
    headers = ("Severity", "Asset", "Technique", "Score", "Count", "Status")
    pdf.set_font("helvetica", "B", 9)
    for header, width in zip(headers, widths):
        pdf.cell(width, 7, header, border=1)
    pdf.ln()

    for (asset, technique, label), group in ordered[:_QUEUE_CAP]:
        scores = group["scores"]
        score_text = (
            f"{min(scores):g}-{max(scores):g}"
            if min(scores) != max(scores)
            else f"{max(scores):g}"
        )
        statuses = group["statuses"]
        status_text = (
            next(iter(statuses)) if len(statuses) == 1 else "mixed"
        )

        pdf.set_text_color(*_SEVERITY_COLORS[label])
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(widths[0], 6, label.upper(), border=1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("courier", size=8)
        pdf.cell(widths[1], 6, asset[:36], border=1)
        pdf.cell(widths[2], 6, technique[:18], border=1)
        pdf.cell(widths[3], 6, score_text, border=1)
        pdf.set_font("helvetica", size=9)
        pdf.cell(widths[4], 6, f"x{group['count']}", border=1)
        pdf.cell(widths[5], 6, status_text[:12], border=1)
        pdf.ln()

    remaining = len(ordered) - _QUEUE_CAP
    if remaining > 0:
        pdf.ln(2)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(
            0,
            6,
            f"+{remaining} additional high-priority incident groups not shown - "
            "see full queue in the dashboard",
        )


# ------------------------------------------------------------------ #
# Section 3 -- Critical Incident Briefings (deduplicated, capped)
# ------------------------------------------------------------------ #


def _critical_briefings_section(pdf: FPDF, incidents_data: List[Dict[str, Any]]) -> None:
    critical = [
        incident
        for incident in incidents_data
        if _severity_of(incident) == "critical"
    ]
    if not critical:
        return

    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Critical Incident Briefings", new_x="LMARGIN", new_y="NEXT")

    # Deduplicate: same asset + technique + first 60 chars of observed_evidence.
    clusters: List[Dict[str, Any]] = []
    for incident in sorted(critical, key=_score_of, reverse=True):
        explanation = incident.get("llm_explanation") or {}
        evidence_key = _safe_text(explanation.get("observed_evidence") or "")[
            :_EVIDENCE_DEDUP_PREFIX
        ]
        key = (
            _safe_text(incident.get("asset") or "unknown"),
            _safe_text(incident.get("mitre_technique") or "-") or "-",
            evidence_key,
        )
        for cluster in clusters:
            if cluster["key"] == key:
                cluster["count"] += 1
                break
        else:
            clusters.append({"key": key, "incident": incident, "count": 1})

    for cluster in clusters[:_BRIEFING_CAP]:
        _briefing_block(pdf, cluster["incident"], cluster["count"])

    remaining = len(clusters) - _BRIEFING_CAP
    if remaining > 0:
        pdf.ln(2)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(
            0,
            6,
            f"{remaining} additional critical incidents follow the same pattern - "
            "full detail available in the dashboard",
        )


def _briefing_block(pdf: FPDF, incident: Dict[str, Any], similar_count: int) -> None:
    pdf.ln(3)

    # a. Header line: truncated ID, asset, score, "(N similar)" if applicable.
    # multi_cell with markdown bold so long headers wrap instead of clipping.
    similar = f"  ({similar_count} similar incidents detected)" if similar_count > 1 else ""
    header = (
        f"**{_short_id(incident.get('id'))}  "
        f"{_safe_text(incident.get('asset', 'unknown'))}  |  "
        f"Score {_score_of(incident):g}  |  CRITICAL**"
    )
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(
        0,
        6,
        _safe_text(header + similar),
        markdown=True,
        wrapmode="CHAR",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)

    # b. Score breakdown as one inline line.
    factors = incident.get("score_factors") or {}
    parts = [f"{label} {factors.get(key, 0)}" for key, label in _SCORE_FACTOR_LABELS]
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", size=9)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(
        0, 5, _safe_text("  \u00b7  ".join(parts)),
        wrapmode="CHAR", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_text_color(0, 0, 0)

    # c. AI Interpretation (fallback: observed_evidence truncated to 2 sentences).
    explanation = incident.get("llm_explanation") or {}
    interpretation = _safe_text(explanation.get("ai_interpretation") or "").strip()
    if not interpretation:
        interpretation = _first_sentences(
            _safe_text(explanation.get("observed_evidence") or ""), 2
        ) or "No AI interpretation available."
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, "AI Interpretation", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0, 5, interpretation,
        wrapmode="CHAR", new_x="LMARGIN", new_y="NEXT",
    )

    # d. Recommended Action, in full.
    action = _safe_text(explanation.get("recommended_action") or "").strip()
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, "Recommended Action", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0, 5, action or "No recommended action available.",
        wrapmode="CHAR", new_x="LMARGIN", new_y="NEXT",
    )

    # e. RAG citations as a single-line bullet of technique/CVE IDs.
    citation_ids: List[str] = []
    for result in incident.get("rag_results") or []:
        source_id = (
            result.get("technique_id") or result.get("cve_id") or result.get("id")
        )
        if source_id and str(source_id) not in citation_ids:
            citation_ids.append(str(source_id))
    if citation_ids:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("courier", size=9)
        pdf.multi_cell(
            0, 5, _safe_text("  \u00b7  ".join(citation_ids)),
            wrapmode="CHAR", new_x="LMARGIN", new_y="NEXT",
        )

    # f. Thin horizontal rule between briefings (not a page break).
    pdf.ln(2)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.set_draw_color(0, 0, 0)


def _first_sentences(text: str, count: int) -> str:
    """Return the first ``count`` sentences of ``text`` (rough split)."""
    text = text.strip()
    if not text:
        return ""
    sentences: List[str] = []
    start = 0
    for index, char in enumerate(text):
        if char in ".!?" and (index + 1 == len(text) or text[index + 1] == " "):
            sentences.append(text[start : index + 1].strip())
            start = index + 1
            if len(sentences) >= count:
                break
    if not sentences:
        sentences.append(text[:200])
    return " ".join(sentences)
