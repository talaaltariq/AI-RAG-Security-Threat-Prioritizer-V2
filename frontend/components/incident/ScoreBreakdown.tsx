"use client";

import { memo, useMemo, type CSSProperties } from "react";
import { clsx } from "clsx";

import {
  SCORE_TOTAL_MAX,
  toScoreFactorItems,
  totalFactorPoints,
  type ScoreFactorsRecord,
} from "@/lib/incident";

export interface ScoreBreakdownProps {
  /** Flat per-factor point record from GET /api/incidents/{id}. */
  scoreFactors: ScoreFactorsRecord;
}

/**
 * ThreatIQ score factor breakdown.
 * Vertical list of the 7 weighted factors — capsule progress bars on a
 * light gray track with alternating Electric Lime and Cyber Teal fills,
 * and clean light point chips.
 */
function ScoreBreakdownBase({ scoreFactors }: ScoreBreakdownProps) {
  // Memoized (Phase 22): factor expansion and total are derived data —
  // recompute only when the score_factors record actually changes.
  const factors = useMemo(() => toScoreFactorItems(scoreFactors), [scoreFactors]);
  const total = useMemo(() => totalFactorPoints(scoreFactors), [scoreFactors]);

  return (
    <div className="flex flex-col">
      {factors.map((factor, index) => {
        const pct =
          factor.pts_max > 0
            ? Math.min(100, Math.round((factor.pts_earned / factor.pts_max) * 100))
            : 0;
        return (
          <div
            key={factor.key}
            className="flex flex-col gap-2 border-t border-black/[0.05] py-3.5 first:border-t-0 first:pt-0"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs sm:text-sm font-bold text-[#0D0D10]">
                {factor.name}
              </span>
              {/* Points pill — clean light capsule chip */}
              <span className="inline-flex items-center rounded-full bg-black/[0.04] border border-black/[0.04] px-2.5 py-0.5 text-[11px] font-bold text-[#0D0D10]">
                {factor.pts_earned} / {factor.pts_max} pts
              </span>
            </div>

            {/* Capsule progress bar on light gray track */}
            <div className="h-2 w-full overflow-hidden rounded-full bg-black/[0.05]">
              <div
                className={clsx(
                  "h-full rounded-full transition-all duration-500",
                  index % 2 === 0 ? "bg-[#D7FF3F]" : "bg-[#14B8A6]"
                )}
                style={
                  {
                    width: `${pct}%`,
                    "--target-width": `${pct}%`,
                  } as CSSProperties
                }
              />
            </div>

            <p className="text-xs font-medium text-[#7E8695]">
              {factor.reason}
            </p>
          </div>
        );
      })}

      {/* Total row — bold header with lime badge */}
      <div className="mt-2 flex items-center justify-between gap-3 border-t border-black/[0.06] pt-4">
        <span className="text-sm sm:text-base font-extrabold tracking-tight text-[#0D0D10]">
          Total Composite Score
        </span>
        <span className="inline-flex items-center rounded-full bg-[#D7FF3F] px-3.5 py-1.5 text-xs sm:text-sm font-extrabold text-[#0D0D10] shadow-sm">
          {total} / {SCORE_TOTAL_MAX} pts
        </span>
      </div>
    </div>
  );
}

/**
 * Memoized (Phase 22): the breakdown re-renders only when the
 * score_factors record reference changes.
 */
export const ScoreBreakdown = memo(ScoreBreakdownBase);
ScoreBreakdown.displayName = "ScoreBreakdown";

