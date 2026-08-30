import { clsx } from "clsx";

import {
  SEVERITY_BADGE_CLASSES,
  SEVERITY_LABELS,
  severityFromScore,
} from "@/lib/severity";

export interface ScoreBadgeProps {
  /** Composite risk score (0-100). */
  score: number;
}

/**
 * ThreatIQ risk score badge — full-pill capsule (DESIGN_SYSTEM.md §2.3
 * radius-full). Color boundaries strictly follow the severity banding
 * (critical >= 80, high >= 60, medium >= 40, low < 40) mapped onto the
 * DESIGN_SYSTEM.md risk severity palette (see lib/severity.ts).
 */
export function ScoreBadge({ score }: ScoreBadgeProps) {
  const severity = severityFromScore(score);
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold transition-transform duration-150",
        SEVERITY_BADGE_CLASSES[severity]
      )}
      title={`${SEVERITY_LABELS[severity]} risk (${score}/100)`}
    >
      <span className="font-extrabold">{score}</span>
      <span className="text-[11px] font-semibold opacity-85">
        {SEVERITY_LABELS[severity]}
      </span>
    </span>
  );
}
