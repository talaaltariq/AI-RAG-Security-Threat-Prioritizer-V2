import type { IncidentStatus, SeverityLabel } from "@/lib/types";

/**
 * ThreatIQ — risk severity palette.
 *
 * Score boundaries strictly mirror the backend banding in
 * backend/api/ingest.py::_severity_label (critical >= 80, high >= 60,
 * medium >= 40, low < 40).
 *
 * Colors map exclusively onto DESIGN_SYSTEM.md tokens:
 *  - critical -> coral red status accent (DESIGN_SYSTEM.md §5, destructive token)
 *  - high     -> solid obsidian capsule with Electric Lime text (§4.7 sales pill)
 *  - medium   -> Cyber Teal accent (#36C6AF, §2.1)
 *  - low      -> soft Cyber Teal pill (#A7EDE0, §2.1 cyber-teal-pill)
 */
export const SEVERITY_ORDER: SeverityLabel[] = [
  "critical",
  "high",
  "medium",
  "low",
];

/** Map a 0-100 composite risk score to its severity band. */
export function severityFromScore(score: number): SeverityLabel {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 40) return "medium";
  return "low";
}

/** Pill classes per severity band (soft tinted pill chips). */
export const SEVERITY_BADGE_CLASSES: Record<SeverityLabel, string> = {
  critical: "bg-rose-50 text-rose-700 border border-rose-200/80 shadow-[0_1px_4px_rgba(225,29,72,0.06)]",
  high: "bg-orange-50 text-orange-700 border border-orange-200/80 shadow-[0_1px_4px_rgba(234,88,12,0.06)]",
  medium: "bg-teal-50 text-teal-700 border border-teal-200/80 shadow-[0_1px_4px_rgba(13,148,136,0.06)]",
  low: "bg-emerald-50 text-emerald-700 border border-emerald-200/80 shadow-[0_1px_4px_rgba(16,185,129,0.06)]",
};

/** Human-readable severity labels. */
export const SEVERITY_LABELS: Record<SeverityLabel, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

/** Soft badge classes per incident status. */
export const STATUS_BADGE_CLASSES: Record<IncidentStatus, string> = {
  active: "bg-[#D7FF3F]/30 text-[#2E4A00] border border-[#D7FF3F]/70 shadow-[0_1px_4px_rgba(215,255,63,0.15)]",
  acknowledged: "bg-teal-50 text-teal-700 border border-teal-200/80 shadow-[0_1px_4px_rgba(13,148,136,0.06)]",
  escalated: "bg-rose-50 text-rose-700 border border-rose-200/80 shadow-[0_1px_4px_rgba(225,29,72,0.06)]",
  resolved: "bg-gray-100 text-gray-600 border border-gray-200 shadow-[0_1px_4px_rgba(0,0,0,0.03)]",
};

/** Human-readable incident status labels. */
export const STATUS_LABELS: Record<IncidentStatus, string> = {
  active: "Active",
  acknowledged: "Acknowledged",
  escalated: "Escalated",
  resolved: "Resolved",
};
