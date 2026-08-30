"use client";

import { useState } from "react";
import { Check, ChevronsUp, CircleCheck, Loader2 } from "lucide-react";
import { clsx } from "clsx";

import {
  postIncidentAction,
  type AnalystActionType,
} from "@/lib/incident";
import { STATUS_BADGE_CLASSES, STATUS_LABELS } from "@/lib/severity";
import type { IncidentStatus } from "@/lib/types";

export interface ActionPanelProps {
  incidentId: string;
  /** Current incident status — drives the disabled (resolved) state. */
  status: IncidentStatus;
  /** Called with the new status after a successful action submission. */
  onStatusChange: (status: IncidentStatus) => void;
}

interface ActionDef {
  action: AnalystActionType;
  label: string;
  icon: typeof Check;
  classes: string;
  confirm: string;
}

/**
 * Button variants:
 *  - Acknowledge -> Lime filled pill
 *  - Escalate    -> Dark outlined pill
 *  - Resolve     -> Soft red filled pill
 */
const ACTIONS: ActionDef[] = [
  {
    action: "acknowledge",
    label: "Acknowledge",
    icon: Check,
    classes:
      "bg-[#D7FF3F] text-[#0D0D10] hover:bg-[#c7f02b] shadow-sm font-extrabold",
    confirm: "Are you sure you want to acknowledge this incident?",
  },
  {
    action: "escalate",
    label: "Escalate",
    icon: ChevronsUp,
    classes:
      "border border-black/[0.12] bg-white text-[#0D0D10] hover:bg-[#F6F7F9] shadow-sm font-bold",
    confirm: "Are you sure you want to escalate this incident?",
  },
  {
    action: "resolve",
    label: "Resolve",
    icon: CircleCheck,
    classes:
      "bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200/80 shadow-sm font-bold",
    confirm: "Are you sure you want to resolve this incident?",
  },
];

/**
 * ThreatIQ analyst action panel.
 * Acknowledge / Escalate / Resolve with confirmation dialog, POSTing to
 * /api/incidents/{id}/action. Restyled as modern SaaS pill buttons.
 */
export function ActionPanel({
  incidentId,
  status,
  onStatusChange,
}: ActionPanelProps) {
  const [pending, setPending] = useState<ActionDef | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resolved = status === "resolved";

  async function confirmAction() {
    if (!pending) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await postIncidentAction(incidentId, pending.action);
      onStatusChange(response.incident_status);
      setPending(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to submit action"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-extrabold tracking-tight text-[#0D0D10]">
          Analyst Actions
        </h3>
        <span
          className={clsx(
            "inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-bold",
            STATUS_BADGE_CLASSES[status] ?? STATUS_BADGE_CLASSES.active
          )}
        >
          {STATUS_LABELS[status] ?? status}
        </span>
      </div>

      <div className="flex flex-wrap gap-2.5">
        {ACTIONS.map((def) => {
          const Icon = def.icon;
          return (
            <button
              key={def.action}
              type="button"
              disabled={resolved || submitting}
              onClick={() => {
                setError(null);
                setPending(def);
              }}
              className={clsx(
                "inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-xs",
                "transition-all duration-150 ease-out active:scale-[0.97]",
                "disabled:cursor-not-allowed disabled:opacity-40",
                def.classes
              )}
            >
              <Icon className="h-3.5 w-3.5" strokeWidth={2.5} />
              {def.label}
            </button>
          );
        })}
      </div>

      {resolved && (
        <p className="text-xs font-medium text-[#8A8F98]">
          This incident has been resolved — no further actions available.
        </p>
      )}

      {error && (
        <p className="text-xs font-medium text-rose-600">{error}</p>
      )}

      {/* Confirmation dialog — clean SaaS modal */}
      {pending && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label={`${pending.label} confirmation`}
          onClick={() => !submitting && setPending(null)}
        >
          <div
            className="w-full max-w-sm rounded-[24px] border border-black/[0.08] bg-white p-6 shadow-[0_20px_50px_rgba(0,0,0,0.12)]"
            onClick={(e) => e.stopPropagation()}
          >
            <h4 className="text-base font-extrabold tracking-tight text-[#0D0D10]">
              Confirm {pending.label}
            </h4>
            <p className="mt-2 text-xs sm:text-sm font-medium leading-relaxed text-[#7E8695]">
              {pending.confirm}
            </p>
            <div className="mt-6 flex justify-end gap-2.5">
              <button
                type="button"
                disabled={submitting}
                onClick={() => setPending(null)}
                className="rounded-full border border-black/[0.1] bg-white px-4 py-2 text-xs font-bold text-[#0D0D10] transition-all hover:bg-[#F6F7F9] active:scale-[0.97] disabled:opacity-40"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={confirmAction}
                className={clsx(
                  "inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold",
                  "transition-all duration-150 active:scale-[0.97] disabled:opacity-40",
                  pending.classes
                )}
              >
                {submitting && (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" strokeWidth={2.5} />
                )}
                {submitting ? "Submitting…" : `Yes, ${pending.label}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

