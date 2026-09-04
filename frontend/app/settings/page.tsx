"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Cpu,
  Database,
  Layers,
  Loader2,
  MinusCircle,
  RefreshCw,
  Shield,
  ShieldAlert,
  Sliders,
  Stethoscope,
  Terminal,
  XCircle,
  Zap,
} from "lucide-react";
import { clsx } from "clsx";

import { probeHealth, updateSettings } from "@/lib/api";
import { useActiveLLMConfig, useKnowledgeBaseStats, useSettings } from "@/lib/hooks";
import type {
  PipelineSettings,
  PipelineSettingsUpdate,
  ProbeHealth,
} from "@/lib/types";

type SettingsTab = "detection" | "rag" | "diagnostics";

const TABS: { id: SettingsTab; label: string; icon: typeof Cpu }[] = [
  { id: "detection", label: "Detection & Scoring", icon: Sliders },
  { id: "rag", label: "RAG & Threat Intel", icon: Database },
  { id: "diagnostics", label: "Diagnostics", icon: Stethoscope },
];

type SeverityField =
  | "severity_critical_min"
  | "severity_high_min"
  | "severity_medium_min"
  | "severity_low_min";

const SEVERITY_FIELDS: SeverityField[] = [
  "severity_critical_min",
  "severity_high_min",
  "severity_medium_min",
  "severity_low_min",
];

/**
 * Settings page — live controls for the persisted PipelineSettings row.
 *
 * Every slider/toggle commits directly to PUT /api/settings: sliders update
 * a local draft while dragging and fire the PUT on release (pointer/keyboard),
 * toggles PUT immediately. The backend enforces strictly-decreasing severity
 * thresholds; a 400 reverts the draft and shows an inline error.
 */
export default function SettingsPage() {
  const { data: settings, mutate } = useSettings();
  const { data: kbStats } = useKnowledgeBaseStats();
  const { data: llmConfig } = useActiveLLMConfig();

  const [activeTab, setActiveTab] = useState<SettingsTab>("detection");
  // Local slider drafts, synced from the server row whenever it changes.
  const [draft, setDraft] = useState<PipelineSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [severityError, setSeverityError] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Diagnostics probe state
  const [probing, setProbing] = useState(false);
  const [probeResult, setProbeResult] = useState<ProbeHealth | null>(null);
  const [probeFailed, setProbeFailed] = useState(false);

  useEffect(() => {
    if (settings) setDraft(settings);
  }, [settings]);

  const commit = async (patch: PipelineSettingsUpdate, isSeverity = false) => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const updated = await updateSettings(patch);
      mutate(updated, false);
      setDraft(updated);
      if (isSeverity) setSeverityError(null);
      setGeneralError(null);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      if (isSeverity && axios.isAxiosError(err) && err.response?.status === 400) {
        const detail = err.response.data?.detail;
        setSeverityError(
          typeof detail === "string" ? detail : "Severity thresholds must be strictly decreasing."
        );
        // Do not apply the change visually — revert drafts to the server row.
        if (settings) {
          setDraft((prev) => {
            if (!prev) return prev;
            const reverted = { ...prev };
            for (const f of SEVERITY_FIELDS) reverted[f] = settings[f];
            return reverted;
          });
        }
      } else {
        setGeneralError(
          axios.isAxiosError(err)
            ? err.response?.data?.detail ?? err.message
            : "Failed to save setting"
        );
      }
    } finally {
      setSaving(false);
    }
  };

  const runProbe = async () => {
    setProbing(true);
    setProbeFailed(false);
    try {
      setProbeResult(await probeHealth());
    } catch {
      setProbeResult(null);
      setProbeFailed(true);
    } finally {
      setProbing(false);
    }
  };

  const llmLabel = llmConfig?.configured
    ? `${llmConfig.provider} · ${llmConfig.model}`
    : "Not configured";

  return (
    <div className="flex flex-col gap-7 pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#0D0D10] lg:text-[28px]">
            Pipeline Settings
          </h1>
          <p className="mt-0.5 text-xs font-medium text-[#8A8F98] sm:text-sm">
            Tune detection sensitivity, severity bands, and RAG retrieval — every change is persisted immediately
          </p>
        </div>
        {saving && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#ECEEF2] px-3.5 py-1.5 text-[11px] font-bold text-[#7E8695]">
            <Loader2 className="h-3 w-3 animate-spin" />
            Saving...
          </span>
        )}
        {saveSuccess && !saving && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3.5 py-1.5 text-[11px] font-bold text-emerald-800 animate-in fade-in">
            <CheckCircle2 className="h-3 w-3" />
            Saved
          </span>
        )}
      </div>

      {generalError && (
        <div className="flex items-center gap-3 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-semibold text-rose-800 shadow-sm">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>Error saving configuration: {generalError}</span>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Active LLM (read-only, configured in /setup) */}
        <div className="flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-white p-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8A8F98]">
              Active LLM
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#D7FF3F]/20 text-[#0D0D10]">
              <Cpu className="h-3.5 w-3.5" />
            </span>
          </div>
          <div className="mt-3">
            <div className="truncate text-base font-extrabold text-[#0D0D10]" title={llmLabel}>
              {llmLabel}
            </div>
            <Link
              href="/setup"
              className="mt-1 inline-flex items-center gap-1 text-[11px] font-bold text-teal-700 hover:underline"
            >
              Change in Setup
            </Link>
          </div>
        </div>

        {/* Anomaly Threshold */}
        <div className="flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-white p-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8A8F98]">
              Anomaly Threshold
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#36C6AF]/20 text-teal-700">
              <Zap className="h-3.5 w-3.5" />
            </span>
          </div>
          <div className="mt-3">
            <div className="text-base font-extrabold text-[#0D0D10]">
              {draft ? `${(draft.anomaly_threshold * 100).toFixed(0)}%` : "—"}
            </div>
            <div className="mt-1 text-[11px] font-medium text-[#8A8F98]">
              Isolation Forest cutoff score
            </div>
          </div>
        </div>

        {/* RAG Index */}
        <div className="flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-white p-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8A8F98]">
              RAG Index
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-100 text-violet-700">
              <Database className="h-3.5 w-3.5" />
            </span>
          </div>
          <div className="mt-3">
            <div className="text-base font-extrabold text-[#0D0D10]">
              {kbStats ? `${kbStats.mitre_count} MITRE · ${kbStats.cve_count} CVEs` : "—"}
            </div>
            <div className="mt-1 text-[11px] font-medium text-[#8A8F98]">
              Live ChromaDB collection counts
            </div>
          </div>
        </div>

        {/* Critical Threshold */}
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
              <span>Score ≥ {draft?.severity_critical_min ?? "—"}</span>
              <span className="text-xs font-normal text-white/50">/ 100</span>
            </div>
            <div className="mt-1 text-[11px] font-medium text-[#D7FF3F]">
              Minimum composite score for Critical severity
            </div>
          </div>
        </div>
      </div>

      {/* Segmented pill tabs */}
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
            </button>
          );
        })}
      </div>

      {/* TAB: Detection & Scoring */}
      {activeTab === "detection" && draft && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          {/* Anomaly detection */}
          <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
              <div>
                <h2 className="text-base font-extrabold text-[#0D0D10]">
                  Telemetry Anomaly Detection
                </h2>
                <p className="mt-0.5 text-xs text-[#8A8F98]">
                  Isolation Forest cutoff — events scoring at or above the threshold enter the correlation pipeline
                </p>
              </div>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#36C6AF]/20 text-teal-800">
                <Zap className="h-4 w-4" />
              </span>
            </div>

            <div className="mt-6 flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-[#0D0D10]">
                  Anomaly Cutoff Sensitivity Threshold
                </label>
                <span className="rounded-full bg-[#0D0D10] px-2.5 py-0.5 text-xs font-extrabold text-[#D7FF3F]">
                  {(draft.anomaly_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <CommitSlider
                min={0.05}
                max={0.95}
                step={0.01}
                value={draft.anomaly_threshold}
                onDraft={(v) => setDraft((p) => (p ? { ...p, anomaly_threshold: v } : p))}
                onCommit={(v) => commit({ anomaly_threshold: v })}
              />
              <div className="flex justify-between text-[10px] font-semibold text-[#8A8F98]">
                <span>5% (High Recall / More Alerts)</span>
                <span>50% (Balanced)</span>
                <span>95% (High Precision / Strict)</span>
              </div>
              <p className="text-[11px] text-[#8A8F98]">
                Security events with an Isolation Forest anomaly score ≥ {(draft.anomaly_threshold * 100).toFixed(0)}% are routed into the correlation and RAG analysis pipeline.
              </p>
            </div>

            {/* Pre-generation toggle */}
            <div className="mt-6 flex items-center justify-between rounded-[18px] bg-[#F6F7F9] p-4">
              <div className="pr-4">
                <div className="text-xs font-bold text-[#0D0D10]">
                  Enable Explanation Pre-Generation & Caching
                </div>
                <div className="text-[11px] text-[#8A8F98]">
                  Eagerly generate LLM explanations for High/Critical incidents at ingest and serve them from cache during analyst reviews.
                </div>
              </div>
              <Toggle
                checked={draft.enable_precaching}
                onChange={() => commit({ enable_precaching: !draft.enable_precaching })}
              />
            </div>
          </div>

          {/* Severity thresholds */}
          <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
              <div>
                <h2 className="text-base font-extrabold text-[#0D0D10]">
                  Composite Risk Scoring Thresholds
                </h2>
                <p className="mt-0.5 text-xs text-[#8A8F98]">
                  0-100 score boundaries per severity tier — must stay strictly decreasing (Critical &gt; High &gt; Medium &gt; Low)
                </p>
              </div>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-100 text-rose-800">
                <ShieldAlert className="h-4 w-4" />
              </span>
            </div>

            {severityError && (
              <div className="mt-5 flex items-center gap-3 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-semibold text-rose-800 animate-in fade-in">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{severityError}</span>
              </div>
            )}

            <div className="mt-6 flex flex-col gap-5">
              <SeverityBand
                label="Critical Severity Threshold"
                description="Immediate P1 SOC incident requiring real-time analyst containment."
                value={draft.severity_critical_min}
                min={1}
                max={100}
                tone="rose"
                onDraft={(v) => setDraft((p) => (p ? { ...p, severity_critical_min: v } : p))}
                onCommit={(v) => commit({ severity_critical_min: v }, true)}
              />
              <SeverityBand
                label="High Severity Threshold"
                description="Significant threats with active exploitation indicators or targeted assets."
                value={draft.severity_high_min}
                min={1}
                max={100}
                tone="amber"
                onDraft={(v) => setDraft((p) => (p ? { ...p, severity_high_min: v } : p))}
                onCommit={(v) => commit({ severity_high_min: v }, true)}
              />
              <SeverityBand
                label="Medium Severity Threshold"
                description="Suspicious anomalies monitored by standard automated rules."
                value={draft.severity_medium_min}
                min={1}
                max={100}
                tone="teal"
                onDraft={(v) => setDraft((p) => (p ? { ...p, severity_medium_min: v } : p))}
                onCommit={(v) => commit({ severity_medium_min: v }, true)}
              />
              <SeverityBand
                label="Low Severity Threshold"
                description="Background noise floor — scores below this are not surfaced as incidents."
                value={draft.severity_low_min}
                min={1}
                max={100}
                tone="slate"
                onDraft={(v) => setDraft((p) => (p ? { ...p, severity_low_min: v } : p))}
                onCommit={(v) => commit({ severity_low_min: v }, true)}
              />
            </div>
          </div>
        </div>
      )}

      {/* TAB: RAG & Threat Intel */}
      {activeTab === "rag" && draft && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
              <div>
                <h2 className="text-base font-extrabold text-[#0D0D10]">
                  RAG Knowledge Base & Embeddings
                </h2>
                <p className="mt-0.5 text-xs text-[#8A8F98]">
                  Semantic retrieval depth and threat intelligence vector collections
                </p>
              </div>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100 text-violet-800">
                <Database className="h-4 w-4" />
              </span>
            </div>

            {/* Knowledge collections — always active, no toggles */}
            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-[20px] border border-black/[0.06] bg-[#F6F7F9] p-4">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-[#0D0D10]" />
                  <span className="text-xs font-bold text-[#0D0D10]">MITRE ATT&CK Matrix</span>
                </div>
                <p className="mt-1 text-[11px] text-[#8A8F98]">
                  Enterprise adversary techniques mapped for real-time technique classification.
                </p>
                <span className="mt-2 inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                  {kbStats ? `${kbStats.mitre_count} documents indexed` : "Indexed & Active"}
                </span>
              </div>

              <div className="rounded-[20px] border border-black/[0.06] bg-[#F6F7F9] p-4">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-[#0D0D10]" />
                  <span className="text-xs font-bold text-[#0D0D10]">NVD CVE Vulnerability DB</span>
                </div>
                <p className="mt-1 text-[11px] text-[#8A8F98]">
                  CVE vectors for matching exploits, CVSS scores, and known vulnerability patterns.
                </p>
                <span className="mt-2 inline-block rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-bold text-teal-800">
                  {kbStats ? `${kbStats.cve_count} documents indexed` : "Indexed & Active"}
                </span>
              </div>
            </div>

            {/* Retrieval hyperparameters */}
            <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-[#0D0D10]">
                    Top-K Retrieved Documents
                  </label>
                  <span className="rounded-full bg-[#0D0D10] px-2.5 py-0.5 text-xs font-extrabold text-[#D7FF3F]">
                    {draft.rag_top_k} Docs
                  </span>
                </div>
                <CommitSlider
                  min={1}
                  max={10}
                  step={1}
                  value={draft.rag_top_k}
                  onDraft={(v) => setDraft((p) => (p ? { ...p, rag_top_k: Math.round(v) } : p))}
                  onCommit={(v) => commit({ rag_top_k: Math.round(v) })}
                />
                <span className="text-[10px] text-[#8A8F98]">
                  Maximum number of threat intel citations attached to each incident reasoning payload.
                </span>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-[#0D0D10]">
                    Similarity Confidence Cutoff
                  </label>
                  <span className="rounded-full bg-[#0D0D10] px-2.5 py-0.5 text-xs font-extrabold text-[#D7FF3F]">
                    {draft.rag_similarity_cutoff.toFixed(2)}
                  </span>
                </div>
                <CommitSlider
                  min={0}
                  max={0.95}
                  step={0.05}
                  value={draft.rag_similarity_cutoff}
                  onDraft={(v) => setDraft((p) => (p ? { ...p, rag_similarity_cutoff: v } : p))}
                  onCommit={(v) => commit({ rag_similarity_cutoff: v })}
                />
                <span className="text-[10px] text-[#8A8F98]">
                  Minimum cosine similarity before a technique or CVE citation is included (0 disables filtering).
                </span>
              </div>
            </div>

            {/* Embedding model (read-only) */}
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

      {/* TAB: Diagnostics */}
      {activeTab === "diagnostics" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 animate-in fade-in duration-200">
          {/* Probe health */}
          <div className="rounded-[24px] border border-black/[0.04] bg-white p-6 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#0D0D10]">
                Pipeline Diagnostics
              </span>
              <button
                type="button"
                onClick={runProbe}
                disabled={probing}
                className="inline-flex items-center gap-1.5 rounded-full bg-[#0D0D10] px-3 py-1.5 text-[11px] font-bold text-[#D7FF3F] hover:bg-[#1A1A20] transition-colors disabled:opacity-60"
              >
                {probing ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin text-[#D7FF3F]" />
                    Probing...
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
              Verify backend reachability, database connectivity, vector store contents, and LLM latency.
            </p>

            {probeFailed && (
              <div className="mt-4 flex items-center gap-3 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-semibold text-rose-800">
                <XCircle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>Health probe failed — is the backend API server running?</span>
              </div>
            )}

            {probeResult ? (
              <div className="mt-4 flex flex-col gap-2.5 rounded-[18px] bg-[#F6F7F9] p-4 text-xs">
                <ProbeRow
                  label="Backend API"
                  status={probeResult.backend.status}
                  latencyMs={probeResult.backend.latency_ms}
                />
                <ProbeRow
                  label="Database"
                  status={probeResult.database.status}
                  latencyMs={probeResult.database.latency_ms}
                />
                <ProbeRow
                  label="Vector Store"
                  status={probeResult.vector_store.status}
                  extra={
                    probeResult.vector_store.status === "ok"
                      ? `${probeResult.vector_store.mitre_count} MITRE · ${probeResult.vector_store.cve_count} CVEs`
                      : "ChromaDB unavailable — check backend logs"
                  }
                />
                <ProbeRow
                  label="LLM Reasoner"
                  status={probeResult.llm.status}
                  latencyMs={probeResult.llm.latency_ms}
                  extra={
                    probeResult.llm.status === "ok"
                      ? `${probeResult.llm.provider ?? "llm"} · ${probeResult.llm.model ?? "unknown"} (${probeResult.llm.source ?? "env"})`
                      : probeResult.llm.message
                  }
                />
              </div>
            ) : (
              !probeFailed && (
                <div className="mt-4 rounded-[18px] border border-dashed border-black/10 p-4 text-center text-xs text-[#8A8F98]">
                  Click <strong className="text-[#0D0D10]">Probe Health</strong> to benchmark each pipeline component in real-time.
                </div>
              )
            )}
          </div>

          {/* Environment metadata */}
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
                <span className="font-mono text-white">ChromaDB Persistent (backend/data/chroma_db)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Slider that reports intermediate values via onDraft while dragging and
 * fires onCommit exactly once when the drag/keyboard interaction ends.
 */
function CommitSlider({
  min,
  max,
  step,
  value,
  onDraft,
  onCommit,
}: {
  min: number;
  max: number;
  step: number;
  value: number;
  onDraft: (v: number) => void;
  onCommit: (v: number) => void;
}) {
  return (
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onDraft(parseFloat(e.target.value))}
      onMouseUp={(e) => onCommit(parseFloat((e.target as HTMLInputElement).value))}
      onTouchEnd={(e) => onCommit(parseFloat((e.target as HTMLInputElement).value))}
      onKeyUp={(e) => {
        if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(e.key)) {
          onCommit(parseFloat((e.target as HTMLInputElement).value));
        }
      }}
      className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-[#ECEEF2] accent-[#0D0D10]"
    />
  );
}

/** Toggle switch that commits to the backend on click. */
function Toggle({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      type="button"
      onClick={onChange}
      aria-pressed={checked}
      className={clsx(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
        checked ? "bg-[#0D0D10]" : "bg-black/20"
      )}
    >
      <span
        className={clsx(
          "pointer-events-none inline-block h-5 w-5 transform rounded-full shadow ring-0 transition duration-200 ease-in-out",
          checked ? "translate-x-5 bg-[#D7FF3F]" : "translate-x-0 bg-white"
        )}
      />
    </button>
  );
}

const SEVERITY_TONES = {
  rose: {
    wrap: "border-rose-200/60 bg-rose-50/40",
    dot: "bg-rose-500",
    label: "text-rose-900",
    badge: "bg-rose-600",
    track: "bg-rose-200 accent-rose-600",
    desc: "text-rose-700/80",
  },
  amber: {
    wrap: "border-amber-200/60 bg-amber-50/40",
    dot: "bg-amber-500",
    label: "text-amber-900",
    badge: "bg-amber-600",
    track: "bg-amber-200 accent-amber-600",
    desc: "text-amber-700/80",
  },
  teal: {
    wrap: "border-teal-200/60 bg-teal-50/40",
    dot: "bg-teal-500",
    label: "text-teal-900",
    badge: "bg-teal-700",
    track: "bg-teal-200 accent-teal-700",
    desc: "text-teal-800/80",
  },
  slate: {
    wrap: "border-slate-200/80 bg-slate-50/60",
    dot: "bg-slate-400",
    label: "text-slate-800",
    badge: "bg-slate-600",
    track: "bg-slate-200 accent-slate-600",
    desc: "text-slate-600",
  },
} as const;

function SeverityBand({
  label,
  description,
  value,
  min,
  max,
  tone,
  onDraft,
  onCommit,
}: {
  label: string;
  description: string;
  value: number;
  min: number;
  max: number;
  tone: keyof typeof SEVERITY_TONES;
  onDraft: (v: number) => void;
  onCommit: (v: number) => void;
}) {
  const t = SEVERITY_TONES[tone];
  return (
    <div className={clsx("flex flex-col gap-2 rounded-[18px] border p-4", t.wrap)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={clsx("h-2.5 w-2.5 rounded-full", t.dot)} />
          <span className={clsx("text-xs font-extrabold", t.label)}>{label}</span>
        </div>
        <span className={clsx("rounded-full px-3 py-0.5 text-xs font-black text-white", t.badge)}>
          ≥ {value} pts
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={1}
        value={value}
        onChange={(e) => onDraft(parseInt(e.target.value, 10))}
        onMouseUp={(e) => onCommit(parseInt((e.target as HTMLInputElement).value, 10))}
        onTouchEnd={(e) => onCommit(parseInt((e.target as HTMLInputElement).value, 10))}
        onKeyUp={(e) => {
          if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(e.key)) {
            onCommit(parseInt((e.target as HTMLInputElement).value, 10));
          }
        }}
        className={clsx("h-2 w-full cursor-pointer appearance-none rounded-lg", t.track)}
      />
      <span className={clsx("text-[11px]", t.desc)}>{description}</span>
    </div>
  );
}

/** One row of the probe-health result with a status icon. */
function ProbeRow({
  label,
  status,
  latencyMs,
  extra,
}: {
  label: string;
  status: string;
  latencyMs?: number | null;
  extra?: string;
}) {
  const ok = status === "ok";
  const notConfigured = status === "not_configured";
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="flex items-center gap-2 font-semibold text-[#7E8695]">
        {ok ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
        ) : notConfigured ? (
          <MinusCircle className="h-4 w-4 text-[#8A8F98]" />
        ) : (
          <XCircle className="h-4 w-4 text-rose-600" />
        )}
        {label}
      </span>
      <span className="flex min-w-0 items-center gap-2 text-right">
        {extra && (
          <span className="max-w-[240px] truncate text-[11px] font-medium text-[#8A8F98]" title={extra}>
            {extra}
          </span>
        )}
        {latencyMs != null && (
          <span className="font-bold text-[#0D0D10]">{latencyMs} ms</span>
        )}
        <span
          className={clsx(
            "font-extrabold uppercase text-[11px]",
            ok ? "text-emerald-600" : notConfigured ? "text-[#8A8F98]" : "text-rose-600"
          )}
        >
          {notConfigured ? "not configured" : status}
        </span>
      </span>
    </div>
  );
}
