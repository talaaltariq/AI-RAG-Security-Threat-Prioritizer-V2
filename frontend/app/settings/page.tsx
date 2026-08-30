"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Bell,
  BookOpen,
  Check,
  CheckCircle2,
  Cpu,
  Database,
  Layers,
  Loader2,
  RefreshCw,
  RotateCcw,
  Save,
  Send,
  Shield,
  ShieldAlert,
  Sliders,
  Sparkles,
  Terminal,
  User,
  Zap,
} from "lucide-react";
import { clsx } from "clsx";

import { saveSettings, testConnectionDiagnostics } from "@/lib/api";
import { useSettings } from "@/lib/hooks";
import type {
  AnalystTier,
  ConnectionDiagnostics,
  RefreshInterval,
  ThreatIQSettings,
} from "@/lib/types";

const DEFAULT_SETTINGS: ThreatIQSettings = {
  llm_model: "gemini-1.5-flash",
  anomaly_sensitivity: 0.85,
  enable_fast_detector: true,
  cache_explanations: true,
  top_k_documents: 3,
  similarity_threshold: 0.65,
  index_mitre_attack: true,
  index_cve_database: true,
  critical_score_threshold: 80,
  high_score_threshold: 60,
  medium_score_threshold: 30,
  crown_jewel_multiplier: 2.0,
  webhook_enabled: false,
  webhook_url: "",
  auto_escalate_critical: true,
  email_digest: false,
  notify_email: "soc-ops@threatiq.internal",
  analyst_name: "SOC Lead Analyst",
  analyst_tier: "Tier 2 Incident Response",
  refresh_interval: "30s",
  sound_alerts: true,
};

type SettingsTab = "ai_engine" | "rag_intel" | "scoring" | "alerts" | "workspace";

interface TabDef {
  id: SettingsTab;
  label: string;
  icon: typeof Cpu;
  badge?: string;
}

const TABS: TabDef[] = [
  { id: "ai_engine", label: "AI & Detection Engine", icon: Sparkles },
  { id: "rag_intel", label: "RAG & Threat Intel", icon: Database, badge: "1,214 Docs" },
  { id: "scoring", label: "Risk Scoring & Rules", icon: Sliders },
  { id: "alerts", label: "Alerts & Webhooks", icon: Bell },
  { id: "workspace", label: "Analyst Workspace", icon: User },
];

export default function SettingsPage() {
  const { data: serverSettings, mutate } = useSettings();

  const [activeTab, setActiveTab] = useState<SettingsTab>("ai_engine");
  const [form, setForm] = useState<ThreatIQSettings>(DEFAULT_SETTINGS);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Diagnostics test state
  const [testingDiagnostics, setTestingDiagnostics] = useState(false);
  const [diagnosticsResult, setDiagnosticsResult] = useState<ConnectionDiagnostics | null>(null);
  const [testWebhookSuccess, setTestWebhookSuccess] = useState(false);

  // Synchronize initial server settings
  useEffect(() => {
    if (serverSettings) {
      setForm(serverSettings);
    }
  }, [serverSettings]);

  const hasChanges = JSON.stringify(form) !== JSON.stringify(serverSettings || DEFAULT_SETTINGS);

  const handleFieldChange = <K extends keyof ThreatIQSettings>(
    key: K,
    value: ThreatIQSettings[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSaveSuccess(false);
    setSaveError(null);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      const updated = await saveSettings(form);
      setForm(updated);
      mutate(updated, false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3500);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save configuration settings");
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (window.confirm("Reset all settings to recommended defaults?")) {
      setForm(DEFAULT_SETTINGS);
      setSaveSuccess(false);
    }
  };

  const runDiagnostics = async () => {
    setTestingDiagnostics(true);
    try {
      const res = await testConnectionDiagnostics();
      setDiagnosticsResult(res);
    } catch (err) {
      console.error("Diagnostics check failed", err);
    } finally {
      setTestingDiagnostics(false);
    }
  };

  const simulateWebhookTest = () => {
    if (!form.webhook_url) {
      alert("Please enter a Webhook URL first.");
      return;
    }
    setTestWebhookSuccess(true);
    setTimeout(() => setTestWebhookSuccess(false), 4000);
  };

  return (
    <div className="flex flex-col gap-7 pb-12">
      {/* Top Application Bar matching Dashboard & Queue */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#0D0D10] lg:text-[28px]">
            Pipeline & Workspace Settings
          </h1>
          <p className="mt-0.5 text-xs font-medium text-[#8A8F98] sm:text-sm">
            Fine-tune AI reasoning engines, RAG knowledge vectors, risk scoring thresholds, and SOC integrations
          </p>
        </div>

        {/* Global Save / Reset Action Bar */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-1.5 rounded-full border border-black/[0.08] bg-white px-4 py-2 text-xs font-bold text-[#0D0D10] shadow-sm transition-all duration-150 hover:bg-[#F6F7F9] hover:scale-[1.02] active:scale-[0.98]"
          >
            <RotateCcw className="h-3.5 w-3.5 text-[#8A8F98]" />
            Reset Defaults
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className={clsx(
              "inline-flex items-center gap-2 rounded-full px-5 py-2 text-xs font-extrabold shadow-sm transition-all duration-150 active:scale-[0.98]",
              saveSuccess
                ? "bg-emerald-500 text-white"
                : "bg-[#D7FF3F] text-[#0D0D10] hover:bg-[#C7F02B] hover:scale-[1.02]"
            )}
          >
            {isSaving ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Saving...
              </>
            ) : saveSuccess ? (
              <>
                <Check className="h-4 w-4 stroke-[3]" />
                Saved Successfully!
              </>
            ) : (
              <>
                <Save className="h-3.5 w-3.5" />
                Save Changes {hasChanges && <span className="h-2 w-2 rounded-full bg-[#0D0D10]" />}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Save Success / Error Toast Alerts */}
      {saveSuccess && (
        <div className="flex items-center gap-3 rounded-[18px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-semibold text-emerald-800 shadow-sm animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>ThreatIQ pipeline configuration updated and synchronized with active detection nodes.</span>
        </div>
      )}

      {saveError && (
        <div className="flex items-center gap-3 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-semibold text-rose-800 shadow-sm">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>Error saving configuration: {saveError}</span>
        </div>
      )}

      {/* Pipeline Telemetry & Live Status Strip (Hero KPI Style) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* KPI 1: AI Model */}
        <div className="flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-white p-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8A8F98]">
              AI Reasoner
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#D7FF3F]/20 text-[#0D0D10]">
              <Sparkles className="h-3.5 w-3.5" />
            </span>
          </div>
          <div className="mt-3">
            <div className="text-base font-extrabold text-[#0D0D10]">
              {form.llm_model === "gemini-1.5-flash"
                ? "Gemini 1.5 Flash"
                : form.llm_model === "gemini-1.5-pro"
                ? "Gemini 1.5 Pro"
                : "Llama 3 Security"}
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {form.cache_explanations ? "Hybrid Pre-Gen Cache Active" : "Direct Live Inference"}
            </div>
          </div>
        </div>

        {/* KPI 2: Anomaly Engine */}
        <div className="flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-white p-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8A8F98]">
              Anomaly Engine
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#36C6AF]/20 text-[#0D0D10]">
              <Zap className="h-3.5 w-3.5 text-teal-700" />
            </span>
          </div>
          <div className="mt-3">
            <div className="text-base font-extrabold text-[#0D0D10]">
              {form.enable_fast_detector ? "Fast Vectorized (C)" : "Standard Scikit-Learn"}
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-[11px] font-medium text-[#8A8F98]">
              <span>Sensitivity Threshold:</span>
              <span className="font-bold text-[#0D0D10]">{(form.anomaly_sensitivity * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* KPI 3: RAG Knowledge Vectors */}
        <div className="flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-white p-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8A8F98]">
              RAG Vector Index
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-100 text-violet-700">
              <Database className="h-3.5 w-3.5" />
            </span>
          </div>
          <div className="mt-3">
            <div className="text-base font-extrabold text-[#0D0D10]">
              14 MITRE · 1.2k CVEs
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-[11px] font-semibold text-teal-600">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
              Top-{form.top_k_documents} Retrieval (Cosine &ge; {form.similarity_threshold})
            </div>
          </div>
        </div>

        {/* KPI 4: Threat Scoring */}
        <div className="flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-[#0D0D10] p-5 text-white shadow-[0_4px_20px_rgba(0,0,0,0.08)]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-white/60">
              Critical Threshold
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#D7FF3F] text-[#0D0D10]">
              <ShieldAlert className="h-3.5 w-3.5" />
            </span>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-1.5 text-base font-extrabold text-white">
              <span>Score &ge; {form.critical_score_threshold}</span>
              <span className="text-xs font-normal text-white/50">/ 100</span>
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-[11px] font-medium text-[#D7FF3F]">
              <span>Crown Jewel Multiplier: {form.crown_jewel_multiplier.toFixed(1)}x</span>
            </div>
          </div>
        </div>
      </div>

      {/* Segmented Pill Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 rounded-full bg-[#ECEEF2] p-1.5 shadow-inner">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold transition-all duration-150",
                active
                  ? "bg-[#D7FF3F] text-[#0D0D10] shadow-sm"
                  : "text-[#7E8695] hover:text-[#0D0D10] hover:bg-white/60"
              )}
            >
              <Icon className={clsx("h-3.5 w-3.5", active ? "text-[#0D0D10]" : "text-[#8A8F98]")} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={clsx(
                    "rounded-full px-2 py-0.5 text-[10px] font-extrabold",
                    active ? "bg-black/10 text-[#0D0D10]" : "bg-black/5 text-[#7E8695]"
                  )}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content Panels */}
      <div className="grid grid-cols-1 gap-7 lg:grid-cols-12">
        {/* Main Settings Form on Left/Center (8 cols) */}
        <div className="flex flex-col gap-6 lg:col-span-8">
          {/* TAB 1: AI & Detection Engine */}
          {activeTab === "ai_engine" && (
            <div className="flex flex-col gap-6 animate-in fade-in duration-200">
              {/* Section: LLM Model Selection */}
              <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
                  <div>
                    <h2 className="text-base font-extrabold text-[#0D0D10]">
                      LLM Threat Explanation Engine
                    </h2>
                    <p className="mt-0.5 text-xs text-[#8A8F98]">
                      Select the generative AI reasoning model powering incident summaries and mitigation steps
                    </p>
                  </div>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#D7FF3F]/20 text-[#0D0D10]">
                    <Cpu className="h-4 w-4" />
                  </span>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
                  {[
                    {
                      id: "gemini-1.5-flash",
                      name: "Gemini 1.5 Flash",
                      tag: "Recommended",
                      desc: "Ultra-fast (<150ms), cost-efficient security reasoning model.",
                      speed: "Ultra-Fast",
                    },
                    {
                      id: "gemini-1.5-pro",
                      name: "Gemini 1.5 Pro",
                      tag: "Deep Reasoning",
                      desc: "Complex multi-stage APT attack narrative synthesis.",
                      speed: "Moderate",
                    },
                    {
                      id: "local-ollama-llama3",
                      name: "Llama 3 Security",
                      tag: "Air-Gapped",
                      desc: "Local on-premise execution for strict privacy requirements.",
                      speed: "Local GPU",
                    },
                  ].map((m) => {
                    const selected = form.llm_model === m.id;
                    return (
                      <div
                        key={m.id}
                        onClick={() => handleFieldChange("llm_model", m.id)}
                        className={clsx(
                          "relative cursor-pointer rounded-[20px] border p-4 transition-all duration-150 hover:scale-[1.01]",
                          selected
                            ? "border-[#0D0D10] bg-[#F6F7F9] shadow-sm ring-2 ring-[#0D0D10]/10"
                            : "border-black/[0.06] bg-white hover:border-black/20"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-[#0D0D10]">{m.name}</span>
                          <span
                            className={clsx(
                              "rounded-full px-2 py-0.5 text-[10px] font-extrabold",
                              selected
                                ? "bg-[#0D0D10] text-[#D7FF3F]"
                                : "bg-black/[0.05] text-[#8A8F98]"
                            )}
                          >
                            {m.tag}
                          </span>
                        </div>
                        <p className="mt-2 text-[11px] leading-relaxed text-[#8A8F98]">{m.desc}</p>
                        <div className="mt-3 flex items-center justify-between pt-2 border-t border-black/[0.04]">
                          <span className="text-[10px] font-semibold text-[#7E8695]">Speed: {m.speed}</span>
                          <div
                            className={clsx(
                              "flex h-4 w-4 items-center justify-center rounded-full border",
                              selected
                                ? "border-[#0D0D10] bg-[#0D0D10] text-[#D7FF3F]"
                                : "border-black/20 bg-white"
                            )}
                          >
                            {selected && <Check className="h-2.5 w-2.5 stroke-[3]" />}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Explanation Cache Toggle */}
                <div className="mt-6 flex items-center justify-between rounded-[18px] bg-[#F6F7F9] p-4">
                  <div className="pr-4">
                    <div className="text-xs font-bold text-[#0D0D10]">
                      Enable Explanation Pre-Generation & Incident Caching
                    </div>
                    <div className="text-[11px] text-[#8A8F98]">
                      Instantly serve pre-calculated reasoning from SQLite and memory without waiting for live LLM turnaround during analyst reviews.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleFieldChange("cache_explanations", !form.cache_explanations)}
                    className={clsx(
                      "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                      form.cache_explanations ? "bg-[#0D0D10]" : "bg-black/20"
                    )}
                  >
                    <span
                      className={clsx(
                        "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                        form.cache_explanations ? "translate-x-5" : "translate-x-0 bg-white"
                      )}
                    />
                  </button>
                </div>
              </div>

              {/* Section: Anomaly Detection Engine */}
              <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
                  <div>
                    <h2 className="text-base font-extrabold text-[#0D0D10]">
                      Telemetry Anomaly Detection
                    </h2>
                    <p className="mt-0.5 text-xs text-[#8A8F98]">
                      Isolation Forest hyperparameters and vectorized inference configuration
                    </p>
                  </div>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#36C6AF]/20 text-teal-800">
                    <Zap className="h-4 w-4" />
                  </span>
                </div>

                {/* Fast Detector Toggle */}
                <div className="mt-5 flex items-center justify-between rounded-[18px] border border-black/[0.06] p-4">
                  <div className="pr-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#0D0D10]">
                        Vectorized C-Compiled Inference Engine
                      </span>
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-extrabold text-emerald-800">
                        &lt;1 ms / event
                      </span>
                    </div>
                    <div className="mt-0.5 text-[11px] text-[#8A8F98]">
                      Compiles 100 decision trees into vectorized memory layout for zero-overhead event filtering.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleFieldChange("enable_fast_detector", !form.enable_fast_detector)}
                    className={clsx(
                      "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                      form.enable_fast_detector ? "bg-[#0D0D10]" : "bg-black/20"
                    )}
                  >
                    <span
                      className={clsx(
                        "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                        form.enable_fast_detector ? "translate-x-5" : "translate-x-0 bg-white"
                      )}
                    />
                  </button>
                </div>

                {/* Sensitivity Slider */}
                <div className="mt-6 flex flex-col gap-2.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-[#0D0D10]">
                      Anomaly Cutoff Sensitivity Threshold
                    </label>
                    <span className="rounded-full bg-[#0D0D10] px-2.5 py-0.5 text-xs font-extrabold text-[#D7FF3F]">
                      {(form.anomaly_sensitivity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.50"
                    max="0.99"
                    step="0.01"
                    value={form.anomaly_sensitivity}
                    onChange={(e) => handleFieldChange("anomaly_sensitivity", parseFloat(e.target.value))}
                    className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-[#ECEEF2] accent-[#0D0D10]"
                  />
                  <div className="flex justify-between text-[10px] font-semibold text-[#8A8F98]">
                    <span>50% (High Recall / More Alerts)</span>
                    <span>85% (Optimal Balanced)</span>
                    <span>99% (High Precision / Strict)</span>
                  </div>
                  <p className="text-[11px] text-[#8A8F98]">
                    Security events with Isolation Forest anomaly score &ge; {(form.anomaly_sensitivity * 100).toFixed(0)}% are routed into the correlation and RAG analysis pipeline.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: RAG & Threat Intelligence */}
          {activeTab === "rag_intel" && (
            <div className="flex flex-col gap-6 animate-in fade-in duration-200">
              <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
                  <div>
                    <h2 className="text-base font-extrabold text-[#0D0D10]">
                      RAG Knowledge Base & Embeddings
                    </h2>
                    <p className="mt-0.5 text-xs text-[#8A8F98]">
                      Configure vector collections, semantic retrieval depth, and threat intelligence sources
                    </p>
                  </div>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100 text-violet-800">
                    <Database className="h-4 w-4" />
                  </span>
                </div>

                {/* Knowledge Collections */}
                <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="flex items-start justify-between rounded-[20px] border border-black/[0.06] bg-[#F6F7F9] p-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-[#0D0D10]" />
                        <span className="text-xs font-bold text-[#0D0D10]">MITRE ATT&CK Matrix v14</span>
                      </div>
                      <p className="mt-1 text-[11px] text-[#8A8F98]">
                        14 curated enterprise adversary techniques mapped for real-time technique classification.
                      </p>
                      <span className="mt-2 inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                        Indexed & Active
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleFieldChange("index_mitre_attack", !form.index_mitre_attack)}
                      className={clsx(
                        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                        form.index_mitre_attack ? "bg-[#0D0D10]" : "bg-black/20"
                      )}
                    >
                      <span
                        className={clsx(
                          "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                          form.index_mitre_attack ? "translate-x-5" : "translate-x-0 bg-white"
                        )}
                      />
                    </button>
                  </div>

                  <div className="flex items-start justify-between rounded-[20px] border border-black/[0.06] bg-[#F6F7F9] p-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-[#0D0D10]" />
                        <span className="text-xs font-bold text-[#0D0D10]">NVD CVE Vulnerability DB</span>
                      </div>
                      <p className="mt-1 text-[11px] text-[#8A8F98]">
                        1,200+ CVE vectors for matching exploits, CVSS scores, and known vulnerability vectors.
                      </p>
                      <span className="mt-2 inline-block rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-bold text-teal-800">
                        Indexed & Active
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleFieldChange("index_cve_database", !form.index_cve_database)}
                      className={clsx(
                        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                        form.index_cve_database ? "bg-[#0D0D10]" : "bg-black/20"
                      )}
                    >
                      <span
                        className={clsx(
                          "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                          form.index_cve_database ? "translate-x-5" : "translate-x-0 bg-white"
                        )}
                      />
                    </button>
                  </div>
                </div>

                {/* Retrieval Hyperparameters */}
                <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
                  {/* Top-K Slider */}
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-[#0D0D10]">
                        Top-K Retrieved Documents
                      </label>
                      <span className="rounded-full bg-[#0D0D10] px-2.5 py-0.5 text-xs font-extrabold text-[#D7FF3F]">
                        {form.top_k_documents} Docs
                      </span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      step="1"
                      value={form.top_k_documents}
                      onChange={(e) => handleFieldChange("top_k_documents", parseInt(e.target.value, 10))}
                      className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-[#ECEEF2] accent-[#0D0D10]"
                    />
                    <span className="text-[10px] text-[#8A8F98]">
                      Maximum number of threat intel citations attached to each incident reasoning payload.
                    </span>
                  </div>

                  {/* Similarity Cutoff Slider */}
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-[#0D0D10]">
                        Similarity Confidence Cutoff
                      </label>
                      <span className="rounded-full bg-[#0D0D10] px-2.5 py-0.5 text-xs font-extrabold text-[#D7FF3F]">
                        {form.similarity_threshold.toFixed(2)}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0.30"
                      max="0.95"
                      step="0.05"
                      value={form.similarity_threshold}
                      onChange={(e) => handleFieldChange("similarity_threshold", parseFloat(e.target.value))}
                      className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-[#ECEEF2] accent-[#0D0D10]"
                    />
                    <span className="text-[10px] text-[#8A8F98]">
                      Minimum cosine similarity required before including a technique or CVE citation.
                    </span>
                  </div>
                </div>

                {/* Embedding Model Notice */}
                <div className="mt-6 flex items-center justify-between rounded-[18px] bg-slate-50 border border-slate-200/60 p-4">
                  <div className="flex items-center gap-3">
                    <Layers className="h-5 w-5 text-slate-700" />
                    <div>
                      <div className="text-xs font-bold text-[#0D0D10]">Vector Embedding Model</div>
                      <div className="font-mono text-[11px] text-[#8A8F98]">models/gemini-embedding-001 (768-dim)</div>
                    </div>
                  </div>
                  <span className="rounded-full bg-slate-200/80 px-2.5 py-0.5 text-[10px] font-bold text-slate-700">
                    ChromaDB Vector Store
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Risk Scoring & Rules */}
          {activeTab === "scoring" && (
            <div className="flex flex-col gap-6 animate-in fade-in duration-200">
              <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
                  <div>
                    <h2 className="text-base font-extrabold text-[#0D0D10]">
                      Composite Risk Scoring Thresholds
                    </h2>
                    <p className="mt-0.5 text-xs text-[#8A8F98]">
                      Define the 0-100 composite point boundaries that categorize threats into triage tiers
                    </p>
                  </div>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-100 text-rose-800">
                    <ShieldAlert className="h-4 w-4" />
                  </span>
                </div>

                {/* Severity Threshold Sliders */}
                <div className="mt-6 flex flex-col gap-5">
                  {/* Critical Band */}
                  <div className="flex flex-col gap-2 rounded-[18px] border border-rose-200/60 bg-rose-50/40 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
                        <span className="text-xs font-extrabold text-rose-900">
                          Critical Severity Threshold
                        </span>
                      </div>
                      <span className="rounded-full bg-rose-600 px-3 py-0.5 text-xs font-black text-white">
                        &ge; {form.critical_score_threshold} pts
                      </span>
                    </div>
                    <input
                      type="range"
                      min="70"
                      max="95"
                      step="1"
                      value={form.critical_score_threshold}
                      onChange={(e) => handleFieldChange("critical_score_threshold", parseInt(e.target.value, 10))}
                      className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-rose-200 accent-rose-600"
                    />
                    <span className="text-[11px] text-rose-700/80">
                      Immediate P1 SOC incident requiring real-time analyst containment and containment runbooks.
                    </span>
                  </div>

                  {/* High Band */}
                  <div className="flex flex-col gap-2 rounded-[18px] border border-amber-200/60 bg-amber-50/40 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                        <span className="text-xs font-extrabold text-amber-900">
                          High Severity Threshold
                        </span>
                      </div>
                      <span className="rounded-full bg-amber-600 px-3 py-0.5 text-xs font-black text-white">
                        &ge; {form.high_score_threshold} pts
                      </span>
                    </div>
                    <input
                      type="range"
                      min="45"
                      max="79"
                      step="1"
                      value={form.high_score_threshold}
                      onChange={(e) => handleFieldChange("high_score_threshold", parseInt(e.target.value, 10))}
                      className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-amber-200 accent-amber-600"
                    />
                    <span className="text-[11px] text-amber-700/80">
                      Significant threats with active exploitation indicators or targeted internal assets.
                    </span>
                  </div>

                  {/* Medium Band */}
                  <div className="flex flex-col gap-2 rounded-[18px] border border-teal-200/60 bg-teal-50/40 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-teal-500" />
                        <span className="text-xs font-extrabold text-teal-900">
                          Medium Severity Threshold
                        </span>
                      </div>
                      <span className="rounded-full bg-teal-700 px-3 py-0.5 text-xs font-black text-white">
                        &ge; {form.medium_score_threshold} pts
                      </span>
                    </div>
                    <input
                      type="range"
                      min="15"
                      max="59"
                      step="1"
                      value={form.medium_score_threshold}
                      onChange={(e) => handleFieldChange("medium_score_threshold", parseInt(e.target.value, 10))}
                      className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-teal-200 accent-teal-700"
                    />
                    <span className="text-[11px] text-teal-800/80">
                      Suspicious anomalies monitored by standard automated rules.
                    </span>
                  </div>
                </div>

                {/* Crown Jewel Multiplier */}
                <div className="mt-6 flex flex-col gap-2 pt-6 border-t border-black/[0.06]">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-xs font-bold text-[#0D0D10]">
                        Crown Jewel Asset Criticality Multiplier
                      </label>
                      <p className="text-[11px] text-[#8A8F98]">
                        Boosts risk scoring for mission-critical infrastructure (e.g., Domain Controllers, Payment Gateways)
                      </p>
                    </div>
                    <span className="rounded-full bg-[#D7FF3F] px-3 py-1 text-xs font-extrabold text-[#0D0D10]">
                      {form.crown_jewel_multiplier.toFixed(1)}x
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1.0"
                    max="3.0"
                    step="0.1"
                    value={form.crown_jewel_multiplier}
                    onChange={(e) => handleFieldChange("crown_jewel_multiplier", parseFloat(e.target.value))}
                    className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-[#ECEEF2] accent-[#0D0D10]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Alerts & Webhooks */}
          {activeTab === "alerts" && (
            <div className="flex flex-col gap-6 animate-in fade-in duration-200">
              <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
                  <div>
                    <h2 className="text-base font-extrabold text-[#0D0D10]">
                      Notification Integrations & Webhooks
                    </h2>
                    <p className="mt-0.5 text-xs text-[#8A8F98]">
                      Forward prioritized security incidents to SIEM, Slack, Microsoft Teams, or SOC pagers
                    </p>
                  </div>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-amber-800">
                    <Bell className="h-4 w-4" />
                  </span>
                </div>

                {/* Webhook Configuration */}
                <div className="mt-5 flex flex-col gap-4">
                  <div className="flex items-center justify-between rounded-[18px] bg-[#F6F7F9] p-4">
                    <div>
                      <div className="text-xs font-bold text-[#0D0D10]">
                        Enable Real-Time Webhook Forwarding
                      </div>
                      <div className="text-[11px] text-[#8A8F98]">
                        Automatically POST payload to external webhook on CRITICAL threat creation
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleFieldChange("webhook_enabled", !form.webhook_enabled)}
                      className={clsx(
                        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                        form.webhook_enabled ? "bg-[#0D0D10]" : "bg-black/20"
                      )}
                    >
                      <span
                        className={clsx(
                          "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                          form.webhook_enabled ? "translate-x-5" : "translate-x-0 bg-white"
                        )}
                      />
                    </button>
                  </div>

                  {/* Webhook URL Input */}
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold text-[#0D0D10]">
                      Outgoing Webhook Endpoint (Slack / Teams / SIEM)
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="url"
                        placeholder="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
                        value={form.webhook_url}
                        onChange={(e) => handleFieldChange("webhook_url", e.target.value)}
                        className="w-full rounded-full border border-black/[0.08] bg-white px-4 py-2.5 text-xs font-medium text-[#0D0D10] placeholder-[#8A8F98] shadow-sm transition-all focus:border-[#0D0D10] focus:ring-2 focus:ring-[#0D0D10]/10 outline-none"
                      />
                      <button
                        type="button"
                        onClick={simulateWebhookTest}
                        className="shrink-0 inline-flex items-center gap-1.5 rounded-full border border-black/[0.08] bg-[#F6F7F9] px-4 py-2.5 text-xs font-bold text-[#0D0D10] hover:bg-black/10 transition-colors"
                      >
                        <Send className="h-3 w-3" />
                        Test Ping
                      </button>
                    </div>
                    {testWebhookSuccess && (
                      <span className="text-[11px] font-semibold text-emerald-600 animate-in fade-in">
                        ✓ Test webhook payload dispatched successfully (HTTP 200 OK).
                      </span>
                    )}
                  </div>

                  {/* Auto-Escalate Critical Threats */}
                  <div className="mt-2 flex items-center justify-between rounded-[18px] border border-black/[0.06] p-4">
                    <div>
                      <div className="text-xs font-bold text-[#0D0D10]">
                        Auto-Escalate Critical Severity Incidents
                      </div>
                      <div className="text-[11px] text-[#8A8F98]">
                        Automatically transitions incident status to &apos;escalated&apos; when composite score exceeds {form.critical_score_threshold}.
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleFieldChange("auto_escalate_critical", !form.auto_escalate_critical)}
                      className={clsx(
                        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                        form.auto_escalate_critical ? "bg-[#0D0D10]" : "bg-black/20"
                      )}
                    >
                      <span
                        className={clsx(
                          "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                          form.auto_escalate_critical ? "translate-x-5" : "translate-x-0 bg-white"
                        )}
                      />
                    </button>
                  </div>

                  {/* Email Digest */}
                  <div className="mt-2 flex flex-col gap-2 rounded-[18px] border border-black/[0.06] p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-bold text-[#0D0D10]">
                          Daily Executive Threat Briefing
                        </div>
                        <div className="text-[11px] text-[#8A8F98]">
                          Send a scheduled 24-hour summary of resolved & pending threats to SOC leadership.
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleFieldChange("email_digest", !form.email_digest)}
                        className={clsx(
                          "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                          form.email_digest ? "bg-[#0D0D10]" : "bg-black/20"
                        )}
                      >
                        <span
                          className={clsx(
                            "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                            form.email_digest ? "translate-x-5" : "translate-x-0 bg-white"
                          )}
                        />
                      </button>
                    </div>

                    {form.email_digest && (
                      <div className="mt-2 pt-2 border-t border-black/[0.06]">
                        <label className="text-[11px] font-bold text-[#0D0D10]">SOC Recipient Email</label>
                        <input
                          type="email"
                          value={form.notify_email}
                          onChange={(e) => handleFieldChange("notify_email", e.target.value)}
                          className="mt-1 w-full rounded-full border border-black/[0.08] bg-white px-4 py-2 text-xs font-medium text-[#0D0D10] focus:outline-none focus:ring-2 focus:ring-[#0D0D10]/10"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Analyst Workspace */}
          {activeTab === "workspace" && (
            <div className="flex flex-col gap-6 animate-in fade-in duration-200">
              <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
                  <div>
                    <h2 className="text-base font-extrabold text-[#0D0D10]">
                      Analyst Session & Workbench Preferences
                    </h2>
                    <p className="mt-0.5 text-xs text-[#8A8F98]">
                      Personalize your identity, operational role, and interface telemetry polling
                    </p>
                  </div>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-100 text-sky-800">
                    <User className="h-4 w-4" />
                  </span>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
                  {/* Analyst Name */}
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold text-[#0D0D10]">Analyst Name</label>
                    <input
                      type="text"
                      value={form.analyst_name}
                      onChange={(e) => handleFieldChange("analyst_name", e.target.value)}
                      className="w-full rounded-full border border-black/[0.08] bg-white px-4 py-2.5 text-xs font-medium text-[#0D0D10] shadow-sm focus:border-[#0D0D10] focus:ring-2 focus:ring-[#0D0D10]/10 outline-none"
                    />
                  </div>

                  {/* Operational Tier */}
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold text-[#0D0D10]">Operational Tier</label>
                    <select
                      value={form.analyst_tier}
                      onChange={(e) => handleFieldChange("analyst_tier", e.target.value as AnalystTier)}
                      className="w-full rounded-full border border-black/[0.08] bg-white px-4 py-2.5 text-xs font-medium text-[#0D0D10] shadow-sm focus:border-[#0D0D10] focus:ring-2 focus:ring-[#0D0D10]/10 outline-none"
                    >
                      <option value="Tier 1 Triage">Tier 1 Triage</option>
                      <option value="Tier 2 Incident Response">Tier 2 Incident Response</option>
                      <option value="Tier 3 Threat Hunting">Tier 3 Threat Hunting</option>
                      <option value="SOC Lead">SOC Lead</option>
                    </select>
                  </div>

                  {/* Auto-Refresh Rate */}
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold text-[#0D0D10]">
                      Telemetry Stream Polling Rate
                    </label>
                    <select
                      value={form.refresh_interval}
                      onChange={(e) => handleFieldChange("refresh_interval", e.target.value as RefreshInterval)}
                      className="w-full rounded-full border border-black/[0.08] bg-white px-4 py-2.5 text-xs font-medium text-[#0D0D10] shadow-sm focus:border-[#0D0D10] focus:ring-2 focus:ring-[#0D0D10]/10 outline-none"
                    >
                      <option value="10s">Every 10 seconds (Real-Time)</option>
                      <option value="30s">Every 30 seconds (Standard)</option>
                      <option value="60s">Every 60 seconds (Conservative)</option>
                      <option value="off">Manual Refresh Only</option>
                    </select>
                  </div>

                  {/* Audio Alerts */}
                  <div className="flex items-center justify-between rounded-[20px] border border-black/[0.06] bg-[#F6F7F9] p-4">
                    <div>
                      <div className="text-xs font-bold text-[#0D0D10]">
                        Critical Alert Sound Chime
                      </div>
                      <div className="text-[11px] text-[#8A8F98]">
                        Audible alert on incoming Critical incident
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleFieldChange("sound_alerts", !form.sound_alerts)}
                      className={clsx(
                        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                        form.sound_alerts ? "bg-[#0D0D10]" : "bg-black/20"
                      )}
                    >
                      <span
                        className={clsx(
                          "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#D7FF3F] shadow ring-0 transition duration-200 ease-in-out",
                          form.sound_alerts ? "translate-x-5" : "translate-x-0 bg-white"
                        )}
                      />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Diagnostic & Quick Actions Panel (4 cols) */}
        <div className="flex flex-col gap-6 lg:col-span-4">
          {/* Live Engine Diagnostics Card */}
          <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#0D0D10]">
                Pipeline Diagnostics
              </span>
              <button
                type="button"
                onClick={runDiagnostics}
                disabled={testingDiagnostics}
                className="inline-flex items-center gap-1.5 rounded-full bg-[#0D0D10] px-3 py-1.5 text-[11px] font-bold text-[#D7FF3F] hover:bg-[#1A1A20] transition-colors"
              >
                {testingDiagnostics ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin text-[#D7FF3F]" />
                    Testing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-3 w-3" />
                    Probe Health
                  </>
                )}
              </button>
            </div>

            <p className="mt-2 text-xs text-[#8A8F98]">
              Verify active backend services, LLM latency, and vector database status.
            </p>

            {diagnosticsResult ? (
              <div className="mt-4 flex flex-col gap-2.5 rounded-[18px] bg-[#F6F7F9] p-4 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#7E8695]">System State:</span>
                  <span className="font-extrabold text-emerald-600 uppercase text-[11px]">
                    ● {diagnosticsResult.status}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#7E8695]">Inference Latency:</span>
                  <span className="font-bold text-[#0D0D10]">{diagnosticsResult.latency_ms} ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#7E8695]">LLM Connection:</span>
                  <span className="font-bold text-[#0D0D10]">{diagnosticsResult.llm_engine.status}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#7E8695]">Anomaly Mode:</span>
                  <span className="font-bold text-[#0D0D10]">{diagnosticsResult.anomaly_engine.mode}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#7E8695]">Indexed RAG Vectors:</span>
                  <span className="font-bold text-[#0D0D10]">
                    {diagnosticsResult.rag_pipeline.mitre_techniques_indexed} MITRE / {diagnosticsResult.rag_pipeline.cve_vectors_indexed} CVEs
                  </span>
                </div>
              </div>
            ) : (
              <div className="mt-4 rounded-[18px] border border-dashed border-black/10 p-4 text-center text-xs text-[#8A8F98]">
                Click <strong className="text-[#0D0D10]">Probe Health</strong> to benchmark the pipeline connection in real-time.
              </div>
            )}
          </div>

          {/* Environment & Version Info */}
          <div className="rounded-[24px] border border-black/[0.04] bg-[#0D0D10] p-6 text-white shadow-[0_4px_20px_rgba(0,0,0,0.06)]">
            <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-[#D7FF3F]">
              <Terminal className="h-4 w-4" />
              <span>Environment Metadata</span>
            </div>

            <div className="mt-4 flex flex-col gap-2 text-xs text-white/80 font-medium">
              <div className="flex justify-between border-b border-white/10 pb-2">
                <span className="text-white/50">App Version</span>
                <span className="font-mono font-bold text-white">v1.0.0 (Phase 22)</span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-2">
                <span className="text-white/50">Framework</span>
                <span className="text-white">FastAPI + Next.js 14</span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-2">
                <span className="text-white/50">Database</span>
                <span className="font-mono text-white">SQLite / threatiq.db</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/50">Vector Store</span>
                <span className="font-mono text-white">ChromaDB In-Memory</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
