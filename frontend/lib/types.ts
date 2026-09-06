/**
 * ThreatIQ — shared TypeScript contracts for the FastAPI backend.
 * Mirrors the serializers in backend/api/stats.py and backend/api/incidents.py.
 */

export type SeverityLabel = "critical" | "high" | "medium" | "low";

export type IncidentStatus =
  | "active"
  | "acknowledged"
  | "escalated"
  | "resolved";

/** Response shape of GET /api/stats (backend/api/stats.py). */
export interface DashboardStats {
  total_events: number;
  total_events_today: number;
  total_incidents: number;
  alert_reduction_pct: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

/** Response item shape of GET /api/incidents (backend/api/incidents.py). */
export interface IncidentSummary {
  id: string;
  created_at: string;
  status: IncidentStatus;
  asset: string;
  asset_criticality: string;
  total_score: number;
  severity_label: SeverityLabel;
  mitre_technique: string | null;
  latest_event_time: string | null;
  events_count: number;
  confidence: string;
  /** Distinct source IPs across the incident's events (for client-side search). */
  source_ips: string[];
}

/** Response shape of GET /api/settings (backend PipelineSettings singleton row). */
export interface PipelineSettings {
  anomaly_threshold: number;
  severity_critical_min: number;
  severity_high_min: number;
  severity_medium_min: number;
  severity_low_min: number;
  rag_top_k: number;
  rag_similarity_cutoff: number;
  enable_precaching: boolean;
  updated_at: string | null;
}

/** Partial update payload for PUT /api/settings. */
export type PipelineSettingsUpdate = Partial<
  Omit<PipelineSettings, "updated_at">
>;

/** Response shape of GET /api/settings/knowledge-base-stats. */
export interface KnowledgeBaseStats {
  mitre_count: number;
  cve_count: number;
}

/** Response shape of GET /api/llm/config (session LLM set via /setup). */
export interface ActiveLLMConfig {
  configured: boolean;
  provider: string | null;
  model: string | null;
}

/** Response shape of GET /api/settings/probe-health. */
export interface ProbeHealth {
  backend: { status: string; latency_ms: number | null };
  database: { status: string; latency_ms: number | null };
  vector_store: { status: string; mitre_count: number; cve_count: number };
  llm: {
    status: string;
    latency_ms?: number | null;
    error_type?: string;
    message?: string;
    /** "session" when the /setup-tested config was probed, "environment" for the backend/.env config. */
    source?: string;
    provider?: string;
    model?: string;
  };
}
