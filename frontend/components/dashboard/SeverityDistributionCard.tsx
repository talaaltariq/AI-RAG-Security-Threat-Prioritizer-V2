"use client";

import { ShieldCheck } from "lucide-react";
import type { DashboardStats } from "@/lib/types";

interface SeverityDistributionCardProps {
  stats: DashboardStats;
}

export function SeverityDistributionCard({ stats }: SeverityDistributionCardProps) {
  const total = stats.total_incidents || 1;
  const criticalPct = Math.round((stats.critical_count / total) * 100);
  const highPct = Math.round((stats.high_count / total) * 100);
  const mediumPct = Math.round((stats.medium_count / total) * 100);
  const lowPct = Math.max(0, 100 - criticalPct - highPct - mediumPct);

  // Posture score: higher is healthier (fewer critical/high)
  const healthScore = Math.max(
    10,
    Math.round(100 - (stats.critical_count * 25 + stats.high_count * 10))
  );

  const severities = [
    {
      label: "Critical",
      count: stats.critical_count,
      pct: criticalPct,
      chipClass: "bg-rose-50 text-rose-700 border border-rose-200/70",
      barColor: "bg-rose-500",
      trackColor: "bg-rose-50",
    },
    {
      label: "High",
      count: stats.high_count,
      pct: highPct,
      chipClass: "bg-orange-50 text-orange-700 border border-orange-200/70",
      barColor: "bg-orange-500",
      trackColor: "bg-orange-50",
    },
    {
      label: "Medium",
      count: stats.medium_count,
      pct: mediumPct,
      chipClass: "bg-teal-50 text-teal-700 border border-teal-200/70",
      barColor: "bg-teal-500",
      trackColor: "bg-teal-50",
    },
    {
      label: "Low",
      count: stats.low_count,
      pct: lowPct,
      chipClass: "bg-emerald-50 text-emerald-700 border border-emerald-200/70",
      barColor: "bg-emerald-500",
      trackColor: "bg-emerald-50",
    },
  ];

  return (
    <div className="group flex flex-col h-full rounded-[22px] border border-black/[0.04] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:scale-[1.015] hover:-translate-y-1 hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)] hover:border-black/10">
      {/* Header */}
      <div className="mb-4 flex shrink-0 items-center justify-between">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-[#0D0D10]">
            Posture & Severity Breakdown
          </h2>
          <p className="text-xs font-medium text-[#8A8F98]">
            Distribution of correlated threats across risk tiers
          </p>
        </div>
        <span className="rounded-full border border-black/[0.04] bg-[#F6F7F9] px-3 py-1 text-xs font-bold text-[#0D0D10]">
          {stats.total_incidents} Total
        </span>
      </div>

      {/* Main Content: Split Grid */}
      <div className="grid flex-1 grid-cols-1 items-stretch gap-5 md:grid-cols-12">
        {/* Left Column: Electric Lime Posture Card */}
        <div className="relative flex h-full flex-col justify-between overflow-hidden rounded-2xl bg-[#D7FF3F] p-5 text-[#0D0D10] shadow-sm md:col-span-5">
          {/* Subtle concentric decorative rings */}
          <div
            aria-hidden
            className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full border-4 border-black/[0.06]"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full border-4 border-black/[0.04]"
          />

          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#0D0D10]/80">
                Health Index
              </span>
              <ShieldCheck className="h-4 w-4 text-[#0D0D10]" strokeWidth={2.5} />
            </div>
            <div className="mt-2 text-3xl font-extrabold tracking-tight text-[#0D0D10]">
              {healthScore}%
            </div>
            <p className="mt-0.5 text-xs font-medium text-[#0D0D10]/80">
              {stats.critical_count === 0
                ? "Optimal Posture — No Criticals"
                : `${stats.critical_count} Criticals Require Action`}
            </p>
          </div>

          {/* Mini dual-tone vertical bars indicator */}
          <div className="mt-4 flex items-end gap-2 border-t border-black/10 pt-2">
            <div className="flex h-12 items-end gap-1.5">
              <div className="h-8 w-2.5 rounded-full bg-[#0D0D10]" title="Critical & High" />
              <div className="h-12 w-2.5 rounded-full bg-[#36C6AF]" title="Medium & Low" />
              <div className="h-6 w-2.5 rounded-full bg-[#0D0D10]" />
              <div className="h-10 w-2.5 rounded-full bg-[#36C6AF]" />
              <div className="h-4 w-2.5 rounded-full bg-[#0D0D10]" />
              <div className="h-9 w-2.5 rounded-full bg-[#36C6AF]" />
            </div>
            <div className="ml-auto text-[11px] font-bold text-[#0D0D10]">
              <span className="mr-1 inline-block h-2 w-2 rounded-full bg-[#0D0D10]" />
              Triage Load
            </div>
          </div>
        </div>

        {/* Right Column: Severity Tier Bars */}
        <div className="flex h-full flex-col justify-between gap-3 py-1 md:col-span-7">
          {severities.map((item) => (
            <div key={item.label} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold ${item.chipClass}`}>
                  {item.label}
                </span>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#0D0D10]">
                    {item.count} <span className="font-normal text-[#8A8F98]">({item.pct}%)</span>
                  </span>
                </div>
              </div>
              <div className={`h-2 w-full overflow-hidden rounded-full ${item.trackColor}`}>
                <div
                  className={`h-full rounded-full transition-all duration-500 ${item.barColor}`}
                  style={{ width: `${Math.max(item.pct, item.count > 0 ? 8 : 0)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
