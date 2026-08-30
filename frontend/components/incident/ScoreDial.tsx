"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { clsx } from "clsx";

export interface ScoreDialProps {
  /** Composite risk score (0-100). */
  score: number;
}

interface DialBand {
  label: string;
  strokeColor: string;
  chipClass: string;
}

/**
 * Severity banding mirrors backend/api/ingest.py::_severity_label
 * (critical >= 80, high >= 60, medium >= 40, low < 40)
 */
function dialBand(score: number): DialBand {
  if (score >= 80)
    return {
      label: "CRITICAL",
      strokeColor: "#F43F5E",
      chipClass:
        "bg-rose-50 text-rose-700 border border-rose-200/80 shadow-[0_1px_3px_rgba(225,29,72,0.06)]",
    };
  if (score >= 60)
    return {
      label: "HIGH",
      strokeColor: "#D7FF3F",
      chipClass:
        "bg-orange-50 text-orange-700 border border-orange-200/80 shadow-[0_1px_3px_rgba(234,88,12,0.06)]",
    };
  if (score >= 40)
    return {
      label: "MEDIUM",
      strokeColor: "#14B8A6",
      chipClass:
        "bg-teal-50 text-teal-700 border border-teal-200/80 shadow-[0_1px_3px_rgba(13,148,136,0.06)]",
    };
  if (score >= 10)
    return {
      label: "LOW",
      strokeColor: "#10B981",
      chipClass:
        "bg-emerald-50 text-emerald-700 border border-emerald-200/80 shadow-[0_1px_3px_rgba(16,185,129,0.06)]",
    };
  return {
    label: "INFO",
    strokeColor: "#9CA3AF",
    chipClass: "bg-gray-100 text-gray-700 border border-gray-200",
  };
}

const SIZE = 200;
const CENTER = SIZE / 2;
const RADIUS = 84;
const STROKE_WIDTH = 12;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * ThreatIQ circular risk gauge.
 * Clean SaaS light theme SVG dial with a framer-motion animated fill,
 * large bold centered score, and a soft tinted severity chip below.
 */
function ScoreDialBase({ score }: ScoreDialProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const band = dialBand(clamped);
  const targetOffset = CIRCUMFERENCE * (1 - clamped / 100);

  return (
    <div className="flex flex-col items-center justify-center gap-3.5 py-1">
      <div className="relative" style={{ width: SIZE, height: SIZE }}>
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          width={SIZE}
          height={SIZE}
          role="img"
          aria-label={`Risk score ${clamped} out of 100 — ${band.label}`}
        >
          {/* Track — light gray subtle track */}
          <circle
            cx={CENTER}
            cy={CENTER}
            r={RADIUS}
            fill="none"
            strokeWidth={STROKE_WIDTH}
            stroke="#F0F2F5"
          />
          {/* Animated fill — draws from 0 to score on mount */}
          <motion.circle
            cx={CENTER}
            cy={CENTER}
            r={RADIUS}
            fill="none"
            strokeWidth={STROKE_WIDTH}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            stroke={band.strokeColor}
            transform={`rotate(-90 ${CENTER} ${CENTER})`}
            initial={{ strokeDashoffset: CIRCUMFERENCE }}
            animate={{ strokeDashoffset: targetOffset }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          />
        </svg>

        {/* Center readout — hero number */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-5xl font-extrabold leading-none tracking-tight text-[#0D0D10]">
            {clamped}
          </span>
          <span className="mt-1.5 text-xs font-semibold text-[#8A8F98]">
            / 100
          </span>
        </div>
      </div>

      {/* Severity band pill chip */}
      <span
        className={clsx(
          "inline-flex items-center rounded-full px-3.5 py-1 text-xs font-extrabold uppercase tracking-wide",
          band.chipClass
        )}
      >
        {band.label}
      </span>
    </div>
  );
}

/**
 * Memoized (Phase 22): the dial is the heaviest render on the incident
 * page (SVG + framer-motion animation) and its props are a single
 * primitive score, so it re-renders only when the score changes.
 */
export const ScoreDial = memo(ScoreDialBase);
ScoreDial.displayName = "ScoreDial";

