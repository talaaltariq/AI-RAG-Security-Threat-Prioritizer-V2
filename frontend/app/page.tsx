"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { Search, Download, Loader2, XCircle, ChevronDown } from "lucide-react";
import { clsx } from "clsx";
import axios from "axios";

import { StatCard } from "@/components/dashboard/StatCard";
import { AlertReductionBanner } from "@/components/dashboard/AlertReductionBanner";
import { SeverityDistributionCard } from "@/components/dashboard/SeverityDistributionCard";
import { TopTargetedAssetsCard } from "@/components/dashboard/TopTargetedAssetsCard";
import { useIncidents, useStats } from "@/lib/hooks";
import { exportReport } from "@/lib/api";
import { SETUP_COMPLETE_KEY } from "@/lib/setup";

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
  const router = useRouter();
  // First-run gate: the /setup flow is the landing experience — until it
  // has been completed (localStorage flag set by "Run Analysis"), the
  // dashboard redirects there.
  const [setupChecked, setSetupChecked] = useState(false);
  useEffect(() => {
    if (localStorage.getItem(SETUP_COMPLETE_KEY) === "1") {
      setSetupChecked(true);
    } else {
      router.replace("/setup");
    }
  }, [router]);

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

  // Export Report button state: spinner while the backend renders the PDF,
  // and an inline error card (message + collapsible technical detail) on
  // failure, matching the ConnectionStatus error pattern from /setup.
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportErrorDetail, setExportErrorDetail] = useState<string | null>(null);
  const [showExportDetail, setShowExportDetail] = useState(false);

  async function handleExportReport() {
    setExporting(true);
    setExportError(null);
    setExportErrorDetail(null);
    setShowExportDetail(false);
    try {
      const blob = await exportReport();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `threatiq_report_${new Date()
        .toISOString()
        .slice(0, 10)}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(
        "Failed to generate the report. Check that the backend is running and try again."
      );
      if (axios.isAxiosError(err)) {
        // responseType: "blob" turns error bodies into blobs too — surface
        // status + generic message as the technical detail.
        const status = err.response?.status
          ? `HTTP ${err.response.status}`
          : "No response";
        setExportErrorDetail(`${err.message} (${status})`);
      } else if (err instanceof Error) {
        setExportErrorDetail(err.message);
      } else {
        setExportErrorDetail(String(err));
      }
    } finally {
      setExporting(false);
    }
  }

  if (!setupChecked) return <DashboardSkeleton />;

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

  // Raw alerts derived from reduction ratio or total ingested events
  const rawAlerts =
    stats.alert_reduction_pct > 0 && stats.alert_reduction_pct < 100
      ? Math.round(stats.total_incidents / (1 - stats.alert_reduction_pct / 100))
      : Math.max(stats.total_events, stats.total_incidents);

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
            onClick={handleExportReport}
            disabled={exporting}
            className="inline-flex items-center gap-2 rounded-full border border-black/[0.06] bg-white px-4 py-2 text-xs font-bold text-[#0D0D10] shadow-[0_2px_8px_rgba(0,0,0,0.03)] transition-all hover:bg-[#F6F7F9] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {exporting ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Download className="h-3.5 w-3.5" />
                Export Report
              </>
            )}
          </button>
        </div>
      </header>

      {/* Export failure: plain message + collapsible technical detail,
          same pattern as ConnectionStatus on /setup. */}
      {exportError && (
        <div className="flex flex-col gap-2 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3">
          <div className="flex items-start gap-3">
            <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-rose-800">
                Report export failed
              </p>
              <p className="mt-1 text-xs font-semibold text-rose-800">
                {exportError}
              </p>
            </div>
          </div>

          {exportErrorDetail && (
            <div className="pl-7">
              <button
                type="button"
                onClick={() => setShowExportDetail((prev) => !prev)}
                className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 underline-offset-2 transition-colors hover:text-rose-900 hover:underline"
                aria-expanded={showExportDetail}
              >
                <ChevronDown
                  className={clsx(
                    "h-3 w-3 transition-transform duration-150",
                    showExportDetail && "rotate-180"
                  )}
                />
                {showExportDetail
                  ? "Hide technical details"
                  : "Show technical details"}
              </button>
              {showExportDetail && (
                <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-[12px] border border-rose-200 bg-white/70 p-3 font-mono text-[11px] leading-relaxed text-rose-900">
                  {exportErrorDetail}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* Top 4 KPI Stat Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Events"
          value={stats.total_events}
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
