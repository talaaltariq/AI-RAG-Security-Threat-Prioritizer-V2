import { api } from "@/lib/api";
import type { IncidentStatus, IncidentSummary } from "@/lib/types";

/**
 * ThreatIQ — incident detail contracts.
 * Mirrors the serializers in backend/api/incidents.py (GET /api/incidents/{id}
 * and POST /api/incidents/{id}/action).
 */

/** Flat per-factor point record as stored by ScoreFactorsModel. */
export interface ScoreFactorsRecord {
  base_severity: number;
  anomaly_score_pts: number;
  asset_criticality_pts: number;
  exploitability_pts: number;
  evidence_count_pts: number;
  recency_pts: number;
  ti_relevance_pts: number;
  anomaly_score_raw: number;
}

/** One renderable factor row for the score breakdown list. */
export interface ScoreFactorItem {
  key: keyof ScoreFactorsRecord | "total";
  name: string;
  pts_earned: number;
  pts_max: number;
  reason: string;
}

/** Structured LLM analyst explanation (backend.llm.explainer.ExplanationResult). */
export interface LLMExplanation {
  observed_evidence: string;
  retrieved_context: string;
  ai_interpretation: string;
  recommended_action: string;
  confidence: "high" | "medium" | "low";
  confidence_reason: string;
  error: string | null;
}

/** One retrieved threat-intelligence document linked to an incident. */
export interface RAGCitation {
  id: string;
  content: string;
  source: string;
  technique_id: string | null;
  cve_id: string | null;
  relevance_score: number;
}

/** Normalized security event (raw_data payload enriched with DB identifiers). */
export interface IncidentEvent {
  id: string;
  incident_id: string;
  timestamp?: string;
  source_ip?: string;
  dest_ip?: string | null;
  event_type?: string;
  username?: string | null;
  attempts?: number;
  bytes_transferred?: number;
  port?: number;
  asset?: string;
  protocol?: string | null;
  anomaly_score?: number;
  is_anomaly?: boolean;
  [key: string]: unknown;
}

/** Recorded analyst lifecycle action. */
export interface AnalystAction {
  id: string;
  incident_id: string;
  action: string;
  created_at: string;
  analyst_note: string | null;
}

/** Full incident payload returned by GET /api/incidents/{id}. */
export interface IncidentDetail extends IncidentSummary {
  events: IncidentEvent[];
  score_factors: ScoreFactorsRecord | null;
  llm_explanation: LLMExplanation | null;
  rag_results: RAGCitation[];
  analyst_actions: AnalystAction[];
}

export type AnalystActionType = "acknowledge" | "escalate" | "resolve";

/** Response shape of POST /api/incidents/{id}/action. */
export interface IncidentActionResponse {
  status: string;
  incident_id: string;
  incident_status: IncidentStatus;
  action: AnalystAction;
}

/** GET /api/incidents/{id} — full incident detail. */
export async function fetchIncident(id: string): Promise<IncidentDetail> {
  const { data } = await api.get<IncidentDetail>(`/api/incidents/${id}`);
  return data;
}

/** POST /api/incidents/{id}/action — record an analyst action. */
export async function postIncidentAction(
  id: string,
  action: AnalystActionType
): Promise<IncidentActionResponse> {
  const { data } = await api.post<IncidentActionResponse>(
    `/api/incidents/${id}/action`,
    { action }
  );
  return data;
}

/* ------------------------------------------------------------------ */
/* Score factor mapping                                                */
/* ------------------------------------------------------------------ */

/**
 * Max points per factor — mirrors backend/scoring/risk_scorer.py weights
 * (20 + 20 + 20 + 15 + 10 + 10 + 5 = 100).
 */
export const SCORE_FACTOR_MAX = {
  base_severity: 20,
  anomaly_score_pts: 20,
  asset_criticality_pts: 20,
  exploitability_pts: 15,
  evidence_count_pts: 10,
  recency_pts: 10,
  ti_relevance_pts: 5,
} as const;

export const SCORE_TOTAL_MAX = 100;

const SEVERITY_FROM_PTS: Record<number, string> = {
  20: "CRITICAL",
  15: "HIGH",
  10: "MEDIUM",
  5: "LOW",
};

const CRITICALITY_FROM_PTS: Record<number, string> = {
  20: "CRITICAL",
  14: "HIGH",
  8: "MEDIUM",
  4: "LOW",
};

/**
 * Reason strings mirror backend/scoring/risk_scorer.py — the API persists
 * only the point values, so the narrative is reconstructed client-side.
 */
function factorReasons(record: ScoreFactorsRecord): Record<string, string> {
  const exploit =
    record.exploitability_pts >= 15
      ? "An active exploit is being used in the wild"
      : record.exploitability_pts >= 8
        ? "A known proof-of-concept exploit exists"
        : "No known exploit for this technique";

  const evidence =
    record.evidence_count_pts >= 10
      ? "4+ correlated events support this incident"
      : record.evidence_count_pts >= 5
        ? "2-3 correlated events support this incident"
        : record.evidence_count_pts >= 2
          ? "1 correlated event supports this incident"
          : "No correlated events support this incident";

  const recency =
    record.recency_pts >= 10
      ? "Most recent event was less than 10 minutes ago"
      : record.recency_pts >= 8
        ? "Most recent event was 10-60 minutes ago"
        : record.recency_pts >= 5
          ? "Most recent event was 1-24 hours ago"
          : record.recency_pts >= 2
            ? "Most recent event was more than 24 hours ago"
            : "No event timestamp available";

  const ti =
    record.ti_relevance_pts >= 5
      ? "Technique appears in high-relevance threat intelligence"
      : record.ti_relevance_pts >= 3
        ? "MITRE ATT&CK technique matched in threat intelligence"
        : "No matching threat intelligence";

  return {
    base_severity: `Primary event severity is ${
      SEVERITY_FROM_PTS[record.base_severity] ?? "LOW"
    }`,
    anomaly_score_pts: `Isolation Forest anomaly score is ${record.anomaly_score_raw.toFixed(2)}`,
    asset_criticality_pts: `Targeted asset criticality is ${
      CRITICALITY_FROM_PTS[record.asset_criticality_pts] ?? "LOW"
    }`,
    exploitability_pts: exploit,
    evidence_count_pts: evidence,
    recency_pts: recency,
    ti_relevance_pts: ti,
  };
}

/** Expand the flat ScoreFactorsRecord into the 7 display rows. */
export function toScoreFactorItems(
  record: ScoreFactorsRecord
): ScoreFactorItem[] {
  const reasons = factorReasons(record);
  const defs: Array<{
    key: keyof typeof SCORE_FACTOR_MAX;
    name: string;
  }> = [
    { key: "base_severity", name: "Base Severity" },
    { key: "anomaly_score_pts", name: "Anomaly Score" },
    { key: "asset_criticality_pts", name: "Asset Criticality" },
    { key: "exploitability_pts", name: "Exploitability" },
    { key: "evidence_count_pts", name: "Evidence Count" },
    { key: "recency_pts", name: "Recency" },
    { key: "ti_relevance_pts", name: "TI Relevance" },
  ];
  return defs.map(({ key, name }) => ({
    key,
    name,
    pts_earned: record[key],
    pts_max: SCORE_FACTOR_MAX[key],
    reason: reasons[key],
  }));
}

/** Sum of all factor points (the composite 0-100 score). */
export function totalFactorPoints(record: ScoreFactorsRecord): number {
  return toScoreFactorItems(record).reduce((sum, f) => sum + f.pts_earned, 0);
}
