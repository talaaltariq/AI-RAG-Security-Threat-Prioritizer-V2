"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ChevronRight,
  Search,
} from "lucide-react";
import { clsx } from "clsx";

import { ActionPanel } from "@/components/incident/ActionPanel";
import { AIExplanation } from "@/components/incident/AIExplanation";
import { EventTimeline } from "@/components/incident/EventTimeline";
import { RAGCitations } from "@/components/incident/RAGCitations";
import { ScoreBreakdown } from "@/components/incident/ScoreBreakdown";
import { ScoreDial } from "@/components/incident/ScoreDial";
import { ScoreBadge } from "@/components/threats/ScoreBadge";
import { useIncident } from "@/lib/hooks";
import { STATUS_BADGE_CLASSES, STATUS_LABELS } from "@/lib/severity";

/** Card shell shared by the detail panels (clean SaaS white card). */
function Panel({
  title,
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[22px] lg:rounded-[24px] border border-black/[0.04] bg-white p-6 sm:p-7 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
      {title && (
        <h2 className="mb-4 text-base font-extrabold tracking-tight text-[#0D0D10]">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}

/**
 * ThreatIQ incident detail page.
 * Clean SaaS light theme analyst workbench:
 * Scoring + timeline on the left, AI reasoning, threat intel citations,
 * and analyst actions on the right.
 */
export default function IncidentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  // Phase 22: SWR-backed detail — the incident is served from cache on
  // revisit and revalidated in the background; the explanation itself is
  // always the pre-generated row read from the DB by the API (no live
  // LLM call on page load).
  const { data: incident, error: queryError, isLoading, mutate } =
    useIncident(id);
  const loading = isLoading && !incident;
  const error = queryError
    ? queryError instanceof Error
      ? queryError.message
      : "Failed to load incident"
    : null;

  return (
    <div className="flex flex-col gap-7">
      {/* Top Application Bar matching Dashboard & Threat Queue */}
      <div className="flex items-center justify-between">
        {/* Search Bar */}
        <div className="relative w-full max-w-md">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8A8F98]" />
          <input
            type="text"
            placeholder="Search threats, assets, IOCs, CVEs..."
            className="w-full rounded-full border border-black/[0.06] bg-white py-2.5 pl-11 pr-4 text-xs font-medium text-[#0D0D10] placeholder-[#8A8F98] shadow-[0_2px_12px_rgba(0,0,0,0.02)] transition-all focus:border-[#0D0D10] focus:outline-none focus:ring-2 focus:ring-[#0D0D10]/10"
          />
        </div>
      </div>

      {/* Breadcrumb Navigation */}
      <nav
        aria-label="Breadcrumb"
        className="flex items-center gap-2 text-xs font-semibold text-[#8A8F98]"
      >
        <Link
          href="/threats"
          className="transition-colors duration-150 hover:text-[#0D0D10]"
        >
          Threats
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-[#8A8F98]" />
        <span className="font-mono text-[#0D0D10]">
          Incident {id.slice(0, 8)}
        </span>
      </nav>

      {loading ? (
        /* Loading state — skeleton panels */
        <div className="grid animate-pulse gap-6 lg:grid-cols-2">
          <div className="flex flex-col gap-6">
            <div className="h-72 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
            <div className="h-80 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
            <div className="h-64 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
          </div>
          <div className="flex flex-col gap-6">
            <div className="h-96 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
            <div className="h-56 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
            <div className="h-28 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
          </div>
        </div>
      ) : error || !incident ? (
        /* Error state */
        <div className="rounded-[24px] border border-black/[0.06] bg-white px-10 py-12 text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)]">
          <h2 className="text-base font-extrabold tracking-tight text-[#0D0D10]">
            Unable to load this incident
          </h2>
          <p className="mt-1 text-xs font-medium text-[#8A8F98]">
            {error ?? "Incident not found"} — verify the backend is running at{" "}
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
          </p>
        </div>
      ) : (
        <>
          {/* Incident header */}
          <header className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight text-[#0D0D10] lg:text-[28px]">
                {incident.asset}
              </h1>
              <p className="mt-0.5 text-xs font-medium text-[#8A8F98] sm:text-sm">
                {incident.mitre_technique ?? "No MITRE technique"} ·{" "}
                {incident.events_count} correlated event
                {incident.events_count === 1 ? "" : "s"}
              </p>
            </div>
            <div className="flex items-center gap-2.5">
              <ScoreBadge score={incident.total_score} />
              <span
                className={clsx(
                  "inline-flex items-center rounded-full px-3 py-1 text-xs font-bold",
                  STATUS_BADGE_CLASSES[incident.status] ??
                    STATUS_BADGE_CLASSES.active
                )}
              >
                {STATUS_LABELS[incident.status] ?? incident.status}
              </span>
            </div>
          </header>

          {/* Two-column analyst workbench */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Left: scoring + evidence */}
            <div className="flex min-w-0 flex-col gap-6">
              <Panel title="Composite Risk Score">
                <ScoreDial score={incident.total_score} />
              </Panel>

              {incident.score_factors && (
                <Panel title="Score Breakdown">
                  <ScoreBreakdown scoreFactors={incident.score_factors} />
                </Panel>
              )}

              <Panel title="Event Timeline">
                <EventTimeline events={incident.events} />
              </Panel>
            </div>

            {/* Right: AI reasoning + intel + actions */}
            <div className="flex min-w-0 flex-col gap-6">
              {incident.llm_explanation && (
                <Panel>
                  <AIExplanation explanation={incident.llm_explanation} />
                </Panel>
              )}

              <Panel title="Threat Intelligence">
                <RAGCitations ragResults={incident.rag_results} />
              </Panel>

              <Panel>
                <ActionPanel
                  incidentId={incident.id}
                  status={incident.status}
                  onStatusChange={(status) =>
                    // Optimistic local cache update — no refetch needed.
                    mutate(
                      (prev) => (prev ? { ...prev, status } : prev),
                      { revalidate: false }
                    )
                  }
                />
              </Panel>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

