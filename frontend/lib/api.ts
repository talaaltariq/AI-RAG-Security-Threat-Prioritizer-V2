import axios from "axios";

import type {
  ActiveLLMConfig,
  DashboardStats,
  IncidentSummary,
  KnowledgeBaseStats,
  PipelineSettings,
  PipelineSettingsUpdate,
  ProbeHealth,
} from "@/lib/types";

/**
 * ThreatIQ API client.
 * Base URL comes from NEXT_PUBLIC_API_URL (.env.local), defaulting to the
 * local FastAPI backend.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    "ngrok-skip-browser-warning": "true",
  },
});

/** GET /api/stats — dashboard overview metrics. */
export async function fetchStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/api/stats");
  return data;
}

/** GET /api/incidents — incident queue, sorted by total_score DESC. */
export async function fetchIncidents(): Promise<IncidentSummary[]> {
  const { data } = await api.get<IncidentSummary[]>("/api/incidents");
  return data;
}

/** GET /api/reports/export — full incident-queue PDF report as a blob. */
export async function exportReport(): Promise<Blob> {
  const { data } = await api.get<Blob>("/api/reports/export", {
    responseType: "blob",
    // PDF rendering walks every incident + LLM explanation; allow extra time.
    timeout: 30_000,
  });
  return data;
}

/** GET /api/settings — persisted pipeline configuration. */
export async function fetchSettings(): Promise<PipelineSettings> {
  const { data } = await api.get<PipelineSettings>("/api/settings");
  return data;
}

/** PUT /api/settings — partial update of pipeline configuration. */
export async function updateSettings(
  patch: PipelineSettingsUpdate
): Promise<PipelineSettings> {
  const { data } = await api.put<PipelineSettings>("/api/settings", patch);
  return data;
}

/** GET /api/settings/knowledge-base-stats — live ChromaDB doc counts. */
export async function fetchKnowledgeBaseStats(): Promise<KnowledgeBaseStats> {
  const { data } = await api.get<KnowledgeBaseStats>(
    "/api/settings/knowledge-base-stats"
  );
  return data;
}

/** GET /api/settings/probe-health — live per-component health probe. */
export async function probeHealth(): Promise<ProbeHealth> {
  const { data } = await api.get<ProbeHealth>("/api/settings/probe-health", {
    // The LLM probe enforces its own 8s deadline; leave headroom above it.
    timeout: 15_000,
  });
  return data;
}

/** GET /api/llm/config — LLM configured via /setup this session. */
export async function fetchActiveLLMConfig(): Promise<ActiveLLMConfig> {
  const { data } = await api.get<ActiveLLMConfig>("/api/llm/config");
  return data;
}
