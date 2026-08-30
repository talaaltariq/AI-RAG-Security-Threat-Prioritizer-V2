import { ArrowRight, ShieldAlert } from "lucide-react";
import { clsx } from "clsx";

import type { IncidentEvent } from "@/lib/incident";

export interface EventTimelineProps {
  /** Correlated events belonging to the incident. */
  events: IncidentEvent[];
}

/** Format an ISO timestamp as "MMM D, HH:MM:SS" (mono readout). */
function formatTimestamp(iso: string | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

/**
 * ThreatIQ event timeline.
 * Clean vertical timeline inside a white card — subtle connecting line,
 * colored status dots (rose/coral for anomalous events, teal/slate for normal),
 * with monospace IP flows, timestamps, and anomaly scores.
 */
export function EventTimeline({ events }: EventTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="py-6 text-center text-xs font-medium text-[#8A8F98]">
        No correlated events recorded for this incident.
      </p>
    );
  }

  const sorted = [...events].sort((a, b) => {
    const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
    const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
    return ta - tb;
  });

  return (
    <ol className="relative flex flex-col">
      {sorted.map((event, index) => {
        const anomalous = Boolean(event.is_anomaly);
        const last = index === sorted.length - 1;
        return (
          <li key={event.id} className="relative flex gap-4">
            {/* Rail: node dot + connecting line */}
            <div className="flex flex-col items-center">
              <span
                className={clsx(
                  "mt-1 h-3 w-3 shrink-0 rounded-full ring-4 transition-all",
                  anomalous
                    ? "bg-rose-500 ring-rose-100"
                    : "bg-[#14B8A6] ring-teal-50"
                )}
              />
              {!last && (
                <span className="my-1.5 w-[2px] flex-1 bg-black/[0.06]" aria-hidden />
              )}
            </div>

            {/* Event body */}
            <div
              className={clsx(
                "flex min-w-0 flex-1 flex-col gap-1.5",
                !last && "pb-6"
              )}
            >
              <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
                <span className="font-mono text-[11px] font-semibold text-[#8A8F98]">
                  {formatTimestamp(event.timestamp)}
                </span>
                {anomalous && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 border border-rose-200/80 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-rose-700 shadow-[0_1px_2px_rgba(225,29,72,0.04)]">
                    <ShieldAlert className="h-3 w-3" strokeWidth={2.5} />
                    Anomalous
                  </span>
                )}
              </div>

              {/* IP Flow */}
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
                <span className="font-mono text-xs font-bold text-[#0D0D10]">
                  {event.source_ip ?? "unknown"}
                </span>
                <ArrowRight
                  className="h-3.5 w-3.5 text-[#8A8F98]"
                  strokeWidth={2}
                />
                <span className="font-mono text-xs font-bold text-[#0D0D10]">
                  {event.dest_ip ?? "—"}
                </span>
              </div>

              {/* Event type & metadata */}
              <span className="text-xs font-medium text-[#7E8695]">
                {event.event_type ?? "unknown"}
                {event.username && (
                  <span className="text-[#0D0D10]"> · user: {event.username}</span>
                )}
                {typeof event.anomaly_score === "number" && (
                  <span className="text-[#8A8F98]">
                    {" "}
                    · anomaly {event.anomaly_score.toFixed(2)}
                  </span>
                )}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

