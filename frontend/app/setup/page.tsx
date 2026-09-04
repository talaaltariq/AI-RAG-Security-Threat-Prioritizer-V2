"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import {
  CheckCircle2,
  CircleDashed,
  Cpu,
  FileUp,
  Loader2,
  Play,
  ShieldCheck,
} from "lucide-react";
import { clsx } from "clsx";

import { ConnectionStatus, type ConnectionTestStatus } from "@/components/setup/ConnectionStatus";
import { FileUploadCard } from "@/components/setup/FileUploadCard";
import {
  SETUP_COMPLETE_KEY,
  testLLMConnection,
  type LLMProvider,
  type LLMTestResult,
  type UploadResult,
} from "@/lib/setup";

/** Sensible default models per provider for the setup form. */
const PROVIDER_DEFAULTS: Record<LLMProvider, { model: string; placeholder: string }> = {
  gemini: { model: "gemini-1.5-flash", placeholder: "gemini-1.5-flash" },
  openai: { model: "gpt-4o-mini", placeholder: "gpt-4o-mini" },
  local: { model: "llama3", placeholder: "llama3" },
};

const PROVIDER_LABELS: Record<LLMProvider, string> = {
  gemini: "Google Gemini",
  openai: "OpenAI",
  local: "Local (OpenAI-compatible)",
};

/**
 * ThreatIQ setup flow — the landing page that runs before the dashboard.
 *
 * Section 1 uploads a .json/.csv event file through POST /api/ingest/upload
 * (the pipeline runs inline); Section 2 verifies the LLM configuration via
 * POST /api/llm/test-connection. "Run Analysis" stays disabled until BOTH
 * the upload has succeeded AND the connection test has passed, then routes
 * to /threats.
 */
export default function SetupPage() {
  const router = useRouter();

  // Section 1 — upload state (owned by FileUploadCard, lifted via callbacks)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  // Section 2 — LLM form state
  const [provider, setProvider] = useState<LLMProvider>("gemini");
  const [model, setModel] = useState<string>(PROVIDER_DEFAULTS.gemini.model);
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");

  // Section 2 — connection probe state
  const [connStatus, setConnStatus] = useState<ConnectionTestStatus>("idle");
  const [connResult, setConnResult] = useState<LLMTestResult | null>(null);
  const [connErrorFallback, setConnErrorFallback] = useState<string | null>(null);

  // Run Analysis
  const [launching, setLaunching] = useState(false);

  const isLocal = provider === "local";
  const formComplete =
    model.trim().length > 0 &&
    apiKey.trim().length > 0 &&
    (!isLocal || baseUrl.trim().length > 0);

  // Any edit to the LLM form invalidates a previous successful probe.
  const invalidateTest = () => {
    setConnStatus("idle");
    setConnResult(null);
  };

  const handleProviderChange = (next: LLMProvider) => {
    setProvider(next);
    setModel(PROVIDER_DEFAULTS[next].model);
    invalidateTest();
  };

  const handleTestConnection = async () => {
    setConnStatus("loading");
    setConnResult(null);
    try {
      const result = await testLLMConnection({
        provider,
        model: model.trim(),
        api_key: apiKey.trim(),
        base_url: isLocal && baseUrl.trim() ? baseUrl.trim() : null,
      });
      setConnResult(result);
      setConnStatus(result.status === "ok" ? "ok" : "error");
    } catch (err) {
      // Network-level failure (backend unreachable / client timeout) —
      // the endpoint itself always returns a structured payload.
      setConnResult(null);
      setConnStatus("error");
      setConnErrorFallback(
        axios.isAxiosError(err)
          ? "Couldn't reach the ThreatIQ backend. Make sure the API server is running."
          : "Something went wrong connecting to this model."
      );
    }
  };

  // "Run Analysis" gate: BOTH the file upload AND the connection test
  // must have succeeded. The upload endpoint already ran the full
  // pipeline, so its result is the analysis launch payload.
  const readyToRun = uploadResult !== null && connStatus === "ok";

  const handleRunAnalysis = () => {
    if (!readyToRun || launching) return;
    setLaunching(true);
    // Mark setup complete so the dashboard (/) no longer redirects here.
    localStorage.setItem(SETUP_COMPLETE_KEY, "1");
    router.push("/threats");
  };

  const inputClasses =
    "w-full rounded-full border border-black/[0.08] bg-white px-4 py-2.5 text-xs font-medium text-[#0D0D10] placeholder-[#8A8F98] shadow-sm transition-all focus:border-[#0D0D10] focus:ring-2 focus:ring-[#0D0D10]/10 outline-none";

  return (
    <div className="flex flex-col gap-7 pb-12">
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#0D0D10] lg:text-[28px]">
            Welcome to ThreatIQ
          </h1>
          <p className="mt-0.5 text-xs font-medium text-[#8A8F98] sm:text-sm">
            Connect your telemetry and AI reasoning engine to launch your first prioritized threat analysis
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[#0D0D10] px-3.5 py-1.5 text-[11px] font-extrabold text-[#D7FF3F]">
          <ShieldCheck className="h-3.5 w-3.5" />
          First-Run Setup
        </span>
      </header>

      {/* Two setup sections, side by side on large screens */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Section 1: Upload your data */}
        <section className="rounded-[24px] border border-black/[0.04] bg-white p-6 shadow-[0_2px_12px_rgba(0,0,0,0.02)] sm:p-7">
          <div className="flex items-center justify-between border-b border-black/[0.06] pb-4">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0D0D10] text-xs font-extrabold text-[#D7FF3F]">
                1
              </span>
              <div>
                <h2 className="text-base font-extrabold text-[#0D0D10]">Upload your data</h2>
                <p className="mt-0.5 text-xs text-[#8A8F98]">
                  Raw security events (.json or .csv) are normalized, correlated, and risk-scored on upload
                </p>
              </div>
            </div>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#36C6AF]/15 text-[#2EB39E]">
              <FileUp className="h-4 w-4" />
            </span>
          </div>

          <div className="mt-5">
            <FileUploadCard
              onUploaded={(result) => setUploadResult(result)}
              onReset={() => setUploadResult(null)}
            />
          </div>
        </section>

        {/* Section 2: Configure your LLM */}
        <section className="rounded-[24px] border border-black/[0.04] bg-white p-6 shadow-[0_2px_12px_rgba(0,0,0,0.02)] sm:p-7">
          <div className="flex items-center justify-between border-b border-black/[0.06] pb-4">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0D0D10] text-xs font-extrabold text-[#D7FF3F]">
                2
              </span>
              <div>
                <h2 className="text-base font-extrabold text-[#0D0D10]">Configure your LLM</h2>
                <p className="mt-0.5 text-xs text-[#8A8F98]">
                  Pick the reasoning model that will explain and prioritize your incidents
                </p>
              </div>
            </div>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#D7FF3F]/25 text-[#0D0D10]">
              <Cpu className="h-4 w-4" />
            </span>
          </div>

          <div className="mt-5 flex flex-col gap-4">
            {/* Provider */}
            <div className="flex flex-col gap-2">
              <label htmlFor="setup-provider" className="text-xs font-bold text-[#0D0D10]">
                Provider
              </label>
              <select
                id="setup-provider"
                value={provider}
                onChange={(e) => handleProviderChange(e.target.value as LLMProvider)}
                className={inputClasses}
              >
                {(Object.keys(PROVIDER_LABELS) as LLMProvider[]).map((p) => (
                  <option key={p} value={p}>
                    {PROVIDER_LABELS[p]}
                  </option>
                ))}
              </select>
            </div>

            {/* Model name */}
            <div className="flex flex-col gap-2">
              <label htmlFor="setup-model" className="text-xs font-bold text-[#0D0D10]">
                Model name
              </label>
              <input
                id="setup-model"
                type="text"
                value={model}
                placeholder={PROVIDER_DEFAULTS[provider].placeholder}
                onChange={(e) => {
                  setModel(e.target.value);
                  invalidateTest();
                }}
                className={inputClasses}
              />
            </div>

            {/* API key */}
            <div className="flex flex-col gap-2">
              <label htmlFor="setup-api-key" className="text-xs font-bold text-[#0D0D10]">
                API key
              </label>
              <input
                id="setup-api-key"
                type="password"
                value={apiKey}
                placeholder={isLocal ? "Any placeholder value (local servers ignore keys)" : "Paste your provider API key"}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  invalidateTest();
                }}
                className={inputClasses}
              />
              <p className="text-[11px] text-[#8A8F98]">
                Used only for the connection test — never stored or persisted.
              </p>
            </div>

            {/* Base URL — only for local/OpenAI-compatible providers */}
            {isLocal && (
              <div className="flex flex-col gap-2">
                <label htmlFor="setup-base-url" className="text-xs font-bold text-[#0D0D10]">
                  Base URL <span className="font-semibold text-[#8A8F98]">(required for Local)</span>
                </label>
                <input
                  id="setup-base-url"
                  type="url"
                  value={baseUrl}
                  placeholder="http://localhost:11434/v1"
                  onChange={(e) => {
                    setBaseUrl(e.target.value);
                    invalidateTest();
                  }}
                  className={inputClasses}
                />
              </div>
            )}

            {/* Test Connection */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={connStatus === "loading" || !formComplete}
                className={clsx(
                  "inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-xs font-extrabold shadow-sm transition-all duration-150 active:scale-[0.98]",
                  connStatus === "loading" || !formComplete
                    ? "cursor-not-allowed bg-black/[0.06] text-[#8A8F98]"
                    : "bg-[#0D0D10] text-[#D7FF3F] hover:bg-[#1A1A20] hover:scale-[1.02]"
                )}
              >
                {connStatus === "loading" ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Test Connection
                  </>
                )}
              </button>
              {!formComplete && (
                <span className="text-[11px] font-medium text-[#8A8F98]">
                  Fill in all fields to enable the connection test.
                </span>
              )}
            </div>

            <ConnectionStatus
              status={connStatus}
              latencyMs={connResult?.status === "ok" ? connResult.latency_ms : undefined}
              errorType={connResult?.status === "error" ? connResult.error_type : undefined}
              message={
                connResult?.status === "error"
                  ? connResult.message
                  : connStatus === "error"
                    ? connErrorFallback ?? "Something went wrong connecting to this model."
                    : undefined
              }
              rawDetail={connResult?.status === "error" ? connResult.raw_detail : undefined}
            />
          </div>
        </section>
      </div>

      {/* Launch bar — Run Analysis stays disabled until both gates pass */}
      <div className="flex flex-col items-center justify-between gap-4 rounded-[24px] border border-black/[0.04] bg-[#0D0D10] p-6 text-white shadow-[0_4px_20px_rgba(0,0,0,0.08)] sm:flex-row">
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-extrabold text-white">Ready to prioritize your threats?</h3>
          <div className="flex flex-wrap items-center gap-2">
            <ReadinessChip
              done={uploadResult !== null}
              label={uploadResult ? `${uploadResult.events_processed} events uploaded` : "Upload your data"}
            />
            <ReadinessChip
              done={connStatus === "ok"}
              label={connStatus === "ok" ? "LLM connection verified" : "Verify LLM connection"}
            />
          </div>
        </div>

        <button
          type="button"
          onClick={handleRunAnalysis}
          disabled={!readyToRun || launching}
          title={
            readyToRun
              ? "View your prioritized threat queue"
              : "Upload a data file and pass the connection test to continue"
          }
          className={clsx(
            "inline-flex shrink-0 items-center gap-2 rounded-full px-7 py-3 text-sm font-extrabold transition-all duration-150 active:scale-[0.98]",
            readyToRun
              ? "bg-[#D7FF3F] text-[#0D0D10] shadow-[0_4px_16px_rgba(215,255,63,0.35)] hover:bg-[#C7F02B] hover:scale-[1.02]"
              : "cursor-not-allowed bg-white/10 text-white/40"
          )}
        >
          {launching ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Launching...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Run Analysis
            </>
          )}
        </button>
      </div>
    </div>
  );
}

/** Small readiness pill for the launch bar (dark surface). */
function ReadinessChip({ done, label }: { done: boolean; label: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-bold",
        done ? "bg-[#D7FF3F] text-[#0D0D10]" : "bg-white/10 text-white/60"
      )}
    >
      {done ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : (
        <CircleDashed className="h-3 w-3" />
      )}
      {label}
    </span>
  );
}
