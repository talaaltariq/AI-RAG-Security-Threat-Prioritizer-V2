"use client";

import { useState } from "react";
import { CheckCircle2, ChevronDown, Loader2, XCircle } from "lucide-react";
import { clsx } from "clsx";

export type ConnectionTestStatus = "idle" | "loading" | "ok" | "error";

export interface ConnectionStatusProps {
  status: ConnectionTestStatus;
  /** Probe round-trip time in ms (ok state only). */
  latencyMs?: number;
  /** Backend-classified error category (auth/timeout/not_found/...). */
  errorType?: string;
  /** Human-readable explanation, always visible in the error state. */
  message?: string;
  /** Raw provider exception text, revealed behind the details toggle. */
  rawDetail?: string;
}

/**
 * Setup Section 2 — LLM connection probe status panel.
 *
 * ok: green check + latency; error: red X + human-readable message with a
 * collapsed "Show technical details" toggle for the raw provider detail;
 * loading: spinner. Soft-tinted chips per the ThreatIQ light theme.
 */
export function ConnectionStatus({
  status,
  latencyMs,
  errorType,
  message,
  rawDetail,
}: ConnectionStatusProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (status === "idle") return null;

  if (status === "loading") {
    return (
      <div className="flex items-center gap-3 rounded-[18px] border border-black/[0.06] bg-[#F6F7F9] px-4 py-3 text-xs font-semibold text-[#0D0D10]">
        <Loader2 className="h-4 w-4 shrink-0 animate-spin text-[#0D0D10]" />
        <span>Testing connection...</span>
      </div>
    );
  }

  if (status === "ok") {
    return (
      <div className="flex items-center gap-3 rounded-[18px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-semibold text-emerald-800 animate-in fade-in slide-in-from-top-2">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
        <span>
          Connected — responded in {latencyMs ?? 0}ms
        </span>
      </div>
    );
  }

  // error state
  return (
    <div className="flex flex-col gap-2 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3">
      <div className="flex items-start gap-3">
        <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold text-rose-800">
            Connection failed
            {errorType && (
              <span className="ml-2 rounded-full bg-rose-200/70 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-rose-800">
                {errorType.replace("_", " ")}
              </span>
            )}
          </p>
          <p className="mt-1 text-xs font-semibold text-rose-800">{message}</p>
        </div>
      </div>

      {rawDetail && (
        <div className="pl-7">
          <button
            type="button"
            onClick={() => setShowDetails((prev) => !prev)}
            className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 underline-offset-2 transition-colors hover:text-rose-900 hover:underline"
            aria-expanded={showDetails}
          >
            <ChevronDown
              className={clsx(
                "h-3 w-3 transition-transform duration-150",
                showDetails && "rotate-180"
              )}
            />
            {showDetails ? "Hide technical details" : "Show technical details"}
          </button>
          {showDetails && (
            <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-[12px] border border-rose-200 bg-white/70 p-3 font-mono text-[11px] leading-relaxed text-rose-900">
              {rawDetail}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
