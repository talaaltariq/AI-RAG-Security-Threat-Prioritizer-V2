"use client";

import { useEffect, useMemo, useState } from "react";
import { Search, ShieldAlert } from "lucide-react";
import { clsx } from "clsx";

import { ThreatQueueTable } from "@/components/threats/ThreatQueueTable";
import { useIncidents } from "@/lib/hooks";
import { SEVERITY_LABELS, SEVERITY_ORDER } from "@/lib/severity";
import type { IncidentSummary, SeverityLabel } from "@/lib/types";

type SeverityFilter = SeverityLabel | "all";

/** Stable empty fallback so useMemo deps stay referentially equal. */
const NO_INCIDENTS: IncidentSummary[] = [];

const FILTERS: SeverityFilter[] = ["all", ...SEVERITY_ORDER];

/**
 * ThreatIQ Threat Queue Page.
 * Light, minimal SaaS queue interface matching the GoodBoard design system:
 * - White cards, 24px radius, soft shadow
 * - Pill segmented control on light track with Electric Lime active pill
 * - Severity summary counter strip
 * - Soft tinted badges and borderless rows on subtle dividers
 */
export default function ThreatQueuePage() {
  const [filter, setFilter] = useState<SeverityFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Debounce the search term (200ms) so the client-side filter only runs
  // once typing pauses, not on every keystroke.
  useEffect(() => {
    const timer = setTimeout(
      () => setSearchQuery(searchInput.trim().toLowerCase()),
      200
    );
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Phase 22: SWR-backed queue — cached across page navigations with
  // background revalidation, so the queue renders instantly on revisit.
  const { data, error: queryError, isLoading } = useIncidents();
  const incidents = data ?? NO_INCIDENTS;
  const loading = isLoading && !data;
  const error = queryError
    ? queryError instanceof Error
      ? queryError.message
      : "Failed to load incidents"
    : null;

  // Severity filter and search query combine with AND logic: an incident
  // must match the selected severity band AND the debounced search term.
  const filtered = useMemo(() => {
    let result =
      filter === "all"
        ? incidents
        : incidents.filter((i) => i.severity_label === filter);
    if (searchQuery) {
      result = result.filter(
        (i) =>
          i.id.toLowerCase().includes(searchQuery) ||
          i.asset.toLowerCase().includes(searchQuery) ||
          (i.mitre_technique ?? "").toLowerCase().includes(searchQuery) ||
          (i.source_ips ?? []).some((ip) =>
            ip.toLowerCase().includes(searchQuery)
          )
      );
    }
    return result;
  }, [incidents, filter, searchQuery]);

  // Quick summary counts per severity band
  const counts = useMemo(() => {
    const critical = incidents.filter((i) => i.severity_label === "critical").length;
    const high = incidents.filter((i) => i.severity_label === "high").length;
    const medium = incidents.filter((i) => i.severity_label === "medium").length;
    const low = incidents.filter((i) => i.severity_label === "low").length;
    return { critical, high, medium, low, total: incidents.length };
  }, [incidents]);

  return (
    <div className="flex flex-col gap-7">
      {/* Top Application Bar matching Dashboard */}
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

      {/* Page Title & Filter Bar */}
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#0D0D10] lg:text-[28px]">
            Threat Queue
          </h1>
          <p className="mt-0.5 text-xs font-medium text-[#8A8F98] sm:text-sm">
            Correlated incidents ranked by composite risk score
          </p>
        </div>

        {/* Search + Severity Filter Tabs — client-side filters, AND logic */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-64 sm:w-72">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8A8F98]" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by asset, IP, technique, or incident ID..."
              aria-label="Search incidents"
              className="w-full rounded-full border border-black/[0.06] bg-white py-2.5 pl-11 pr-4 text-xs font-medium text-[#0D0D10] placeholder-[#8A8F98] shadow-[0_2px_12px_rgba(0,0,0,0.02)] transition-all focus:border-[#0D0D10] focus:outline-none focus:ring-2 focus:ring-[#0D0D10]/10"
            />
          </div>

          {/* Pill segmented control on a light gray track */}
          <div className="inline-flex items-center gap-1 rounded-full bg-black/[0.04] p-1 border border-black/[0.04]">
          {FILTERS.map((f) => {
            const active = filter === f;
            return (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={clsx(
                  "rounded-full px-4 py-1.5 text-xs transition-all duration-150 ease-out",
                  active
                    ? "bg-[#D7FF3F] font-bold text-[#0D0D10] shadow-sm"
                    : "font-semibold text-[#7E8695] hover:text-[#0D0D10]"
                )}
              >
                {f === "all" ? "All" : SEVERITY_LABELS[f]}
              </button>
            );
          })}
          </div>
        </div>
      </header>

      {/* Severity Summary Counter Strip */}
      {!loading && !error && incidents.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-[20px] border border-black/[0.04] bg-white px-5 py-3.5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
          <div className="flex items-center gap-2.5">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#0D0D10] text-[#D7FF3F]">
              <ShieldAlert className="h-3.5 w-3.5" />
            </span>
            <span className="text-xs font-bold text-[#0D0D10]">
              {counts.total} Correlated Incidents
            </span>
            <span className="hidden text-xs text-[#8A8F98] sm:inline">·</span>
            <span className="hidden text-xs font-medium text-[#8A8F98] sm:inline">
              Live queue status
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-bold text-rose-700 border border-rose-200/80 shadow-[0_1px_3px_rgba(225,29,72,0.06)]">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
              {counts.critical} Critical
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-orange-50 px-2.5 py-1 text-xs font-bold text-orange-700 border border-orange-200/80 shadow-[0_1px_3px_rgba(234,88,12,0.06)]">
              <span className="h-1.5 w-1.5 rounded-full bg-orange-500" />
              {counts.high} High
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-2.5 py-1 text-xs font-bold text-teal-700 border border-teal-200/80 shadow-[0_1px_3px_rgba(13,148,136,0.06)]">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
              {counts.medium} Medium
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700 border border-emerald-200/80 shadow-[0_1px_3px_rgba(16,185,129,0.06)]">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              {counts.low} Low
            </span>
          </div>
        </div>
      )}

      {/* Main Content: Loading Skeleton, Error State, or Table */}
      {loading ? (
        <div className="flex animate-pulse flex-col gap-6">
          <div className="h-14 rounded-[20px] border border-black/[0.04] bg-white shadow-sm" />
          <div className="h-[480px] rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
        </div>
      ) : error ? (
        <div className="rounded-[24px] border border-black/[0.06] bg-white px-10 py-12 text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)]">
          <h2 className="text-base font-extrabold tracking-tight text-[#0D0D10]">
            Unable to load the threat queue
          </h2>
          <p className="mt-1 text-xs font-medium text-[#8A8F98]">
            {error} — verify the backend is running at{" "}
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
          </p>
        </div>
      ) : filtered.length === 0 && searchQuery ? (
        <div className="rounded-[24px] border border-black/[0.04] bg-white px-10 py-16 text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)]">
          <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-black/[0.04] text-[#8A8F98]">
            <Search className="h-5 w-5" strokeWidth={2} />
          </span>
          <p className="text-sm font-bold text-[#0D0D10]">
            No incidents match your search
          </p>
          <p className="mt-1 text-xs font-medium text-[#8A8F98]">
            Try a different asset, IP, technique, or incident ID.
          </p>
        </div>
      ) : (
        <ThreatQueueTable incidents={filtered} />
      )}
    </div>
  );
}
