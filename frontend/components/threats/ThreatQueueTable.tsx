"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowDown, ArrowUp, ShieldCheck } from "lucide-react";
import { clsx } from "clsx";

import { ScoreBadge } from "@/components/threats/ScoreBadge";
import {
  STATUS_BADGE_CLASSES,
  STATUS_LABELS,
} from "@/lib/severity";
import { formatRelativeTime } from "@/lib/utils";
import type { IncidentSummary } from "@/lib/types";

export interface ThreatQueueTableProps {
  incidents: IncidentSummary[];
}

/**
 * ThreatIQ threat queue table.
 * Borderless rows on subtle dividers (DESIGN_SYSTEM.md §4.7), sortable by
 * Risk Score (default descending), row hover uses the dark-surface hover
 * wash (§4.2 nav hover / §2.1 surface tokens). Row click navigates to the
 * incident detail view at /threats/{id}.
 */
export function ThreatQueueTable({ incidents }: ThreatQueueTableProps) {
  const router = useRouter();
  const [sortDesc, setSortDesc] = useState(true);

  const sorted = useMemo(
    () =>
      [...incidents].sort((a, b) =>
        sortDesc
          ? b.total_score - a.total_score
          : a.total_score - b.total_score
      ),
    [incidents, sortDesc]
  );

  return (
    <div className="overflow-hidden rounded-[24px] border border-black/[0.04] bg-white shadow-[0_4px_20px_rgba(0,0,0,0.04)]">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left">
          <thead>
            <tr className="bg-[#0D0D10] text-[11px] font-bold uppercase tracking-wider text-white/70 border-b-2 border-[#D7FF3F]">
              <th className="px-6 py-4">
                <button
                  type="button"
                  onClick={() => setSortDesc((d) => !d)}
                  className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-[#D7FF3F] transition-colors hover:text-white focus:outline-none"
                  aria-label="Sort by risk score"
                >
                  Risk Score
                  {sortDesc ? (
                    <ArrowDown className="h-3.5 w-3.5 text-[#D7FF3F]" strokeWidth={2.5} />
                  ) : (
                    <ArrowUp className="h-3.5 w-3.5 text-[#D7FF3F]" strokeWidth={2.5} />
                  )}
                </button>
              </th>
              <th className="px-6 py-4">Incident ID</th>
              <th className="px-6 py-4">Target Asset</th>
              <th className="px-6 py-4">MITRE Technique</th>
              <th className="px-6 py-4">Events</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Last Event</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/[0.04]">
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-16">
                  <div className="flex flex-col items-center justify-center gap-3 text-center">
                    <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#36C6AF]/15 text-[#0D9488]">
                      <ShieldCheck className="h-6 w-6" strokeWidth={2} />
                    </span>
                    <p className="text-sm font-bold text-[#0D0D10]">
                      No active incidents
                    </p>
                    <p className="text-xs font-medium text-[#8A8F98]">
                      The queue is clear — new correlated incidents will appear here.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              sorted.map((incident) => (
                <tr
                  key={incident.id}
                  onClick={() => router.push(`/threats/${incident.id}`)}
                  className="group cursor-pointer text-sm transition-colors duration-150 ease-out hover:bg-[#F8FAFD]"
                >
                  <td className="px-6 py-4.5">
                    <ScoreBadge score={incident.total_score} />
                  </td>
                  <td className="px-6 py-4.5 font-mono text-xs font-semibold text-[#8A8F98] group-hover:text-[#0D0D10] transition-colors">
                    {incident.id.slice(0, 8)}
                  </td>
                  <td className="px-6 py-4.5 font-bold text-[#0D0D10]">
                    {incident.asset}
                  </td>
                  <td className="px-6 py-4.5">
                    {incident.mitre_technique ? (
                      <span className="inline-flex items-center rounded-md bg-black/[0.03] px-2.5 py-1 font-mono text-xs font-medium text-[#5A606C] border border-black/[0.03]">
                        {incident.mitre_technique}
                      </span>
                    ) : (
                      <span className="font-mono text-xs text-[#8A8F98]">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4.5 font-semibold text-[#0D0D10]">
                    {incident.events_count}
                  </td>
                  <td className="px-6 py-4.5">
                    <span
                      className={clsx(
                        "inline-flex items-center rounded-full px-3 py-1 text-[11px] font-bold tracking-tight",
                        STATUS_BADGE_CLASSES[incident.status] ??
                          STATUS_BADGE_CLASSES.active
                      )}
                    >
                      {STATUS_LABELS[incident.status] ?? incident.status}
                    </span>
                  </td>
                  <td className="px-6 py-4.5 text-xs font-medium text-[#8A8F98]">
                    {formatRelativeTime(incident.latest_event_time)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
