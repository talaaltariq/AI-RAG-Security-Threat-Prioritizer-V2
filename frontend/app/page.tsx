"use client";

import dynamic from "next/dynamic";
import { Search, Download } from "lucide-react";

import { StatCard } from "@/components/dashboard/StatCard";
import { AlertReductionBanner } from "@/components/dashboard/AlertReductionBanner";
import { SeverityDistributionCard } from "@/components/dashboard/SeverityDistributionCard";
import { TopTargetedAssetsCard } from "@/components/dashboard/TopTargetedAssetsCard";
import { useIncidents, useStats } from "@/lib/hooks";

const AlertVolumeChart = dynamic(
  () =>
    import("@/components/dashboard/AlertVolumeChart").then(
      (mod) => ({ default: mod.AlertVolumeChart })
    ),
  {
    ssr: false,
    loading: () => (
      <div className="h-[360px] rounded-[22px] border border-black/[0.04] bg-white p-6 shadow-sm animate-pulse" />
    ),
  }
);

/**
 * ThreatIQ Security Overview Dashboard.
 * Light, minimal executive SaaS dashboard with solid black sidebar,
 * electric lime accents, soft rounded white cards, and real data visualizations.
 */
export default function DashboardPage() {
  // Phase 22: SWR-backed data — automatic caching, deduplication, and
  // background revalidation. Revisiting the dashboard renders instantly
  // from cache instead of refetching.
  const statsQuery = useStats();
  const incidentsQuery = useIncidents();

  const stats = statsQuery.data ?? null;
  const incidents = incidentsQuery.data ?? [];
  const queryError = statsQuery.error ?? incidentsQuery.error;
  const error = queryError
    ? queryError instanceof Error
      ? queryError.message
      : "Failed to load dashboard data"
    : null;
  // Initial load only: cached data keeps rendering while SWR revalidates.
  const loading = !stats && !error;

  if (loading) return <DashboardSkeleton />;

  if (error || !stats) {
    return (
      <div className="flex flex-1 items-center justify-center py-20">
        <div className="rounded-[22px] border border-black/[0.06] bg-white px-10 py-8 text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)]">
          <h1 className="text-xl font-extrabold tracking-tight text-[#0D0D10]">
            Unable to reach the ThreatIQ API
          </h1>
          <p className="mt-2 text-sm font-medium text-[#8A8F98]">
            {error ?? "Unknown error"} — verify the backend is running at{" "}
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
          </p>
        </div>
      </div>
    );
  }

  // Raw alerts derived from reduction ratio or today's events
  const rawAlerts =
    stats.alert_reduction_pct > 0 && stats.alert_reduction_pct < 100
      ? Math.round(stats.total_incidents / (1 - stats.alert_reduction_pct / 100))
      : Math.max(stats.total_events_today, stats.total_incidents);

  return (
    <div className="flex flex-col gap-7">
      {/* Top Application Bar matching GoodBoard layout */}
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

      {/* Page Title & Actions */}
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#0D0D10] lg:text-[28px]">
            Security Overview
          </h1>
          <p className="mt-0.5 text-xs font-medium text-[#8A8F98] sm:text-sm">
            Real-time threat posture and correlated telemetry intelligence
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-full border border-black/[0.06] bg-white px-4 py-2 text-xs font-bold text-[#0D0D10] shadow-[0_2px_8px_rgba(0,0,0,0.03)] transition-all hover:bg-[#F6F7F9] active:scale-[0.98]"
          >
            <Download className="h-3.5 w-3.5" />
            Export Report
          </button>
        </div>
      </header>

      {/* Top 4 KPI Stat Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Events"
          value={stats.total_events_today}
          subtitle="Ingested telemetry events"
          imageSrc="/icons/total-events.png"
          trend="neutral"
        />
        <StatCard
          title="Active Incidents"
          value={stats.total_incidents}
          subtitle="Correlated by ThreatIQ"
          imageSrc="/icons/active-incidents.png"
          trend="up"
        />
        <StatCard
          title="Critical"
          value={stats.critical_count}
          subtitle="Require immediate action"
          imageSrc="/icons/critical.png"
          trend={stats.critical_count > 0 ? "up" : "neutral"}
        />
        <StatCard
          title="Alert Reduction"
          value={stats.alert_reduction_pct}
          suffix="%"
          decimals={1}
          subtitle="Noise eliminated by AI"
          imageSrc="/icons/alert-reduction.png"
          trend="down"
        />
      </div>

      {/* Alert Reduction Funnel Banner */}
      <AlertReductionBanner
        rawAlerts={rawAlerts}
        incidents={stats.total_incidents}
        critical={stats.critical_count}
        reductionPct={stats.alert_reduction_pct}
      />

      {/* Visual Data Analytics Grid — Airy 2-column layout (max 2 charts per row) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Chart 1: Alert & Ingestion Velocity Trend */}
        <AlertVolumeChart stats={stats} incidents={incidents} />

        {/* Chart 2: Threat Posture & Severity Breakdown */}
        <SeverityDistributionCard stats={stats} />
      </div>

      {/* Row 2: Top Targeted Assets & MITRE Techniques */}
      <div className="grid grid-cols-1 gap-6">
        <TopTargetedAssetsCard incidents={incidents} />
      </div>
    </div>
  );
}

/** Loading skeleton in clean light theme. */
function DashboardSkeleton() {
  return (
    <div className="flex animate-pulse flex-col gap-7">
      <div className="flex items-center justify-between">
        <div className="h-10 w-72 rounded-full bg-white border border-black/[0.04]" />
        <div className="h-10 w-44 rounded-full bg-white border border-black/[0.04]" />
      </div>
      <div className="flex flex-col gap-2">
        <div className="h-8 w-60 rounded-full bg-white border border-black/[0.04]" />
        <div className="h-4 w-80 rounded-full bg-white border border-black/[0.04]" />
      </div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-40 rounded-[22px] border border-black/[0.04] bg-white p-6 shadow-sm"
          />
        ))}
      </div>
      <div className="h-28 rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="h-[360px] rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
        <div className="h-[360px] rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
      </div>
      <div className="h-64 rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
    </div>
  );
}
