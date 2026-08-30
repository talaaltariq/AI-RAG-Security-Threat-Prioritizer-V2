import { clsx } from "clsx";
import { AlertTriangle, Sparkles } from "lucide-react";

import type { LLMExplanation } from "@/lib/incident";

export interface AIExplanationProps {
  /** Structured LLM explanation (ExplanationResult) for the incident. */
  explanation: LLMExplanation;
}

interface SectionDef {
  key: keyof Pick<
    LLMExplanation,
    | "observed_evidence"
    | "retrieved_context"
    | "ai_interpretation"
    | "recommended_action"
  >;
  label: string;
  cardClasses: string;
  labelColor: string;
}

/**
 * Section accent mapping:
 *  - Observed Evidence   -> Teal left-accent border + soft light background
 *  - Retrieved Context   -> Blue/Sky left-accent border + soft light background
 *  - AI Interpretation   -> Purple left-accent border + soft light background
 *  - Recommended Action  -> Lime left-accent border + soft light background
 */
const SECTIONS: SectionDef[] = [
  {
    key: "observed_evidence",
    label: "Observed Evidence",
    cardClasses:
      "border border-black/[0.04] border-l-4 border-l-teal-500 bg-teal-50/25",
    labelColor: "text-teal-700",
  },
  {
    key: "retrieved_context",
    label: "Retrieved Context",
    cardClasses:
      "border border-black/[0.04] border-l-4 border-l-sky-500 bg-sky-50/25",
    labelColor: "text-sky-700",
  },
  {
    key: "ai_interpretation",
    label: "AI Interpretation",
    cardClasses:
      "border border-black/[0.04] border-l-4 border-l-purple-500 bg-purple-50/25",
    labelColor: "text-purple-700",
  },
  {
    key: "recommended_action",
    label: "Recommended Action",
    cardClasses:
      "border border-black/[0.04] border-l-4 border-l-[#A3E635] bg-[#F7FEE7]/50",
    labelColor: "text-[#3F6212]",
  },
];

/** Confidence badge mapped onto soft SaaS chips. */
const CONFIDENCE_CLASSES: Record<LLMExplanation["confidence"], string> = {
  high: "bg-[#D7FF3F] text-[#0D0D10] shadow-sm",
  medium: "bg-teal-50 text-teal-700 border border-teal-200/80 shadow-sm",
  low: "bg-rose-50 text-rose-700 border border-rose-200/80 shadow-sm",
};

/**
 * ThreatIQ AI reasoning panel — the four grounded sections of the LLM
 * explanation with soft white cards, colored left-accent borders,
 * confidence badge, and the verification note.
 */
export function AIExplanation({ explanation }: AIExplanationProps) {
  return (
    <div className="relative flex flex-col gap-3.5">
      {/* Header & Confidence badge */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#D7FF3F]/30 text-[#0D0D10]">
            <Sparkles className="h-4 w-4" strokeWidth={2.2} />
          </span>
          <div>
            <h3 className="text-base font-extrabold tracking-tight text-[#0D0D10]">
              AI Analysis
            </h3>
            <p className="text-xs font-medium text-[#7E8695]">
              {explanation.confidence_reason}
            </p>
          </div>
        </div>
        <span
          className={clsx(
            "inline-flex shrink-0 items-center rounded-full px-3 py-1 text-[11px] font-extrabold uppercase tracking-wide",
            CONFIDENCE_CLASSES[explanation.confidence] ??
              CONFIDENCE_CLASSES.low
          )}
        >
          {explanation.confidence} confidence
        </span>
      </div>

      {explanation.error && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-xs font-medium text-rose-700">
          <AlertTriangle className="h-4 w-4 shrink-0" strokeWidth={2} />
          LLM pipeline reported an error — showing degraded output.
        </div>
      )}

      {/* 4 Grounded Sections with colored left-accent borders */}
      {SECTIONS.map((section) => (
        <section
          key={section.key}
          className={clsx("rounded-xl p-4 transition-all", section.cardClasses)}
        >
          <h4
            className={clsx(
              "text-[11px] font-extrabold uppercase tracking-wider",
              section.labelColor
            )}
          >
            {section.label}
          </h4>
          <p className="mt-1.5 text-xs sm:text-sm font-medium leading-relaxed text-[#1F2937]">
            {explanation[section.key]}
          </p>
        </section>
      ))}

      <p className="mt-1 text-center text-xs italic text-[#8A8F98]">
        AI-generated analysis. Verify before acting.
      </p>
    </div>
  );
}

