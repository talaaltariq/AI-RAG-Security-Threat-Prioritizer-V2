"use client";

import useSWR from "swr";

import {
  fetchActiveLLMConfig,
  fetchIncidents,
  fetchKnowledgeBaseStats,
  fetchSettings,
  fetchStats,
} from "@/lib/api";
import { fetchIncident, type IncidentDetail } from "@/lib/incident";
import type {
  ActiveLLMConfig,
  DashboardStats,
  IncidentSummary,
  KnowledgeBaseStats,
  PipelineSettings,
} from "@/lib/types";

/**
 * ThreatIQ SWR data hooks (Phase 22 — frontend performance).
 *
 * Every API read goes through SWR, giving automatic client-side caching,
 * deduplication, and background revalidation: navigating Dashboard ->
 * Threat Queue -> back re-renders instantly from cache while SWR quietly
 * refreshes stale data.
 *
 * The shared config is tuned for demo stability: no refetch on window
 * focus or reconnect (the demo tab stays open and must not churn), a
 * generous deduping interval, and previous data kept on screen during
 * revalidation so the UI never flashes back to skeletons.
 */
const SWR_CONFIG = {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  keepPreviousData: true,
  dedupingInterval: 30_000,
  shouldRetryOnError: true,
  errorRetryCount: 2,
} as const;

/** GET /api/stats — dashboard overview metrics. */
export function useStats() {
  return useSWR<DashboardStats>("/api/stats", fetchStats, SWR_CONFIG);
}

/** GET /api/incidents — incident queue, sorted by total_score DESC. */
export function useIncidents() {
  return useSWR<IncidentSummary[]>("/api/incidents", fetchIncidents, SWR_CONFIG);
}

/** GET /api/incidents/{id} — full incident detail (null key = skip). */
export function useIncident(id: string | null | undefined) {
  return useSWR<IncidentDetail>(
    id ? `/api/incidents/${id}` : null,
    () => fetchIncident(id as string),
    SWR_CONFIG
  );
}

/** GET /api/settings — persisted pipeline configuration. */
export function useSettings() {
  return useSWR<PipelineSettings>("/api/settings", fetchSettings, SWR_CONFIG);
}

/** GET /api/settings/knowledge-base-stats — live ChromaDB doc counts. */
export function useKnowledgeBaseStats() {
  return useSWR<KnowledgeBaseStats>(
    "/api/settings/knowledge-base-stats",
    fetchKnowledgeBaseStats,
    SWR_CONFIG
  );
}

/** GET /api/llm/config — LLM configured via /setup this session. */
export function useActiveLLMConfig() {
  return useSWR<ActiveLLMConfig>("/api/llm/config", fetchActiveLLMConfig, SWR_CONFIG);
}
