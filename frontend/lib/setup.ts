import axios from "axios";

import { api } from "@/lib/api";

/**
 * ThreatIQ setup-flow API helpers.
 *
 * Backs the /setup landing page: multipart event-file uploads
 * (POST /api/ingest/upload) and live LLM connection probes
 * (POST /api/llm/test-connection). Kept separate from lib/api.ts so the
 * setup flow can be iterated on without touching the dashboard client.
 */

/** localStorage flag marking that the setup flow has been completed. */
export const SETUP_COMPLETE_KEY = "threatiq_setup_complete";

export type LLMProvider = "gemini" | "openai" | "local";

/** Request shape of POST /api/llm/test-connection (backend LLMConfig). */
export interface LLMConfigPayload {
  provider: LLMProvider;
  model: string;
  api_key: string;
  base_url?: string | null;
}

/** Success payload of POST /api/llm/test-connection. */
export interface LLMTestSuccess {
  status: "ok";
  latency_ms: number;
}

/** Classified failure payload of POST /api/llm/test-connection. */
export interface LLMTestError {
  status: "error";
  error_type: "auth" | "timeout" | "not_found" | "rate_limit" | "connection" | "unknown";
  message: string;
  raw_detail: string;
}

export type LLMTestResult = LLMTestSuccess | LLMTestError;

/** Response shape of POST /api/ingest/upload (backend/api/upload.py). */
export interface UploadResult {
  incidents_created: number;
  events_processed: number;
  incident_ids: string[];
}

/**
 * POST /api/ingest/upload — send a .json/.csv event file through the
 * threat pipeline. Reports multipart upload progress via `onProgress`.
 *
 * On a 4xx/5xx rejection the backend's `detail` message is rethrown
 * verbatim so the UI can surface it unchanged.
 */
export async function uploadEventsFile(
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const { data } = await api.post<UploadResult>("/api/ingest/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      // The pipeline runs inline (detection -> correlation -> scoring ->
      // RAG -> LLM), so allow a much wider envelope than the default 10s.
      timeout: 120_000,
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.min(100, Math.round((event.loaded / event.total) * 100)));
        }
      },
    });
    return data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        throw new Error(detail);
      }
      if (detail) {
        throw new Error(JSON.stringify(detail));
      }
    }
    throw err;
  }
}

/**
 * POST /api/llm/test-connection — probe a candidate provider/model/key
 * combination. The backend always answers with a structured payload
 * (never raises), so both halves of the union are returned, not thrown.
 */
export async function testLLMConnection(
  config: LLMConfigPayload
): Promise<LLMTestResult> {
  // Backend enforces its own 8s probe deadline; leave headroom above it.
  const { data } = await api.post<LLMTestResult>("/api/llm/test-connection", config, {
    timeout: 15_000,
  });
  return data;
}
