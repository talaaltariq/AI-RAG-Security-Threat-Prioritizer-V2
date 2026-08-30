"use client";

import { useEffect } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";
import {
  Minus,
  TrendingDown,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { clsx } from "clsx";

export interface StatCardProps {
  title: string;
  value: number;
  subtitle?: string;
  icon?: LucideIcon;
  imageSrc?: string;
  trend?: "up" | "down" | "neutral";
  /** Extra classes for the icon bubble (design-system token classes only). */
  colorClass?: string;
  /** Optional unit suffix rendered after the value (e.g. "%"). */
  suffix?: string;
  /** Decimal places for the animated counter (default 0). */
  decimals?: number;
}

const TREND_CONFIG = {
  up: {
    icon: TrendingUp,
    pill: "bg-[#36C6AF] text-[#0D0D10]",
    label: "Active",
  },
  down: {
    icon: TrendingDown,
    pill: "bg-[#36C6AF] text-[#0D0D10]",
    label: "Optimized",
  },
  neutral: {
    icon: Minus,
    pill: "bg-[#36C6AF] text-[#0D0D10]",
    label: "Normal",
  },
} as const;

/**
 * ThreatIQ Stat Card — Dual-Tone Executive SaaS Card.
 * Top section: Solid black with white circular icon, large bold value, and title.
 * Bottom section: Electric lime banner with teal status/subtitle pill.
 */
export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  imageSrc,
  trend = "neutral",
  colorClass,
  suffix = "",
  decimals = 0,
}: StatCardProps) {
  const count = useMotionValue(0);
  const display = useTransform(count, (v) =>
    `${v.toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}${suffix}`
  );

  useEffect(() => {
    const controls = animate(count, value, {
      duration: 1.1,
      ease: [0.16, 1, 0.3, 1],
    });
    return () => controls.stop();
  }, [count, value]);

  const trendCfg = TREND_CONFIG[trend];
  const TrendIcon = trendCfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={clsx(
        "group flex flex-col overflow-hidden rounded-[22px] border border-black/[0.04] shadow-[0_4px_20px_rgba(0,0,0,0.05)]",
        "transition-all duration-300 ease-out hover:scale-[1.025] hover:-translate-y-1.5 hover:shadow-[0_16px_36px_rgba(0,0,0,0.12)] hover:border-black/10 cursor-pointer"
      )}
    >
      {/* Top Black Section */}
      <div className="relative flex flex-col justify-between bg-[#0D0D10] p-5 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Circle Icon Container */}
            <div
              className={clsx(
                "flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-transform duration-300 ease-out group-hover:scale-110 overflow-hidden",
                imageSrc ? "bg-transparent p-0 drop-shadow-md" : "bg-white text-[#0D0D10] shadow-sm p-1.5",
                colorClass
              )}
            >
              {imageSrc ? (
                <img
                  src={imageSrc}
                  alt={title}
                  className="h-full w-full object-cover"
                />
              ) : Icon ? (
                <Icon className="h-5 w-5" strokeWidth={2.5} />
              ) : null}
            </div>

            {/* Big Bold Number */}
            <motion.div className="text-3xl font-extrabold tracking-tight text-white leading-none transition-transform duration-300 group-hover:translate-x-0.5">
              {display}
            </motion.div>
          </div>
        </div>

        {/* Title */}
        <div className="mt-4 text-xs font-semibold text-white/80 transition-colors duration-300 group-hover:text-white">
          {title}
        </div>
      </div>

      {/* Bottom Electric Lime Section */}
      <div className="flex items-center bg-[#D7FF3F] px-4 py-3 transition-colors duration-300 group-hover:brightness-[1.03]">
        <span
          className={clsx(
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold shadow-xs transition-transform duration-300 group-hover:scale-[1.02]",
            trendCfg.pill
          )}
        >
          <TrendIcon className="h-3.5 w-3.5" strokeWidth={2.5} />
          {subtitle || trendCfg.label}
        </span>
      </div>
    </motion.div>
  );
}

