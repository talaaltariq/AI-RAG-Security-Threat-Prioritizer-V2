"use client";

import { motion } from "framer-motion";
import { ArrowRight, TrendingDown } from "lucide-react";

export interface AlertReductionBannerProps {
  /** Raw alerts ingested before correlation. */
  rawAlerts: number;
  /** Incidents identified after correlation. */
  incidents: number;
  /** Critical-severity incidents. */
  critical: number;
  /** Alert-noise reduction percentage (0-100). */
  reductionPct: number;
}

/**
 * ThreatIQ alert reduction funnel banner.
 * Light minimal SaaS horizontal flow card with clean dividers,
 * bold numbers, an electric lime reduction pill, and a seamless animated gradient glow.
 */
export function AlertReductionBanner({
  rawAlerts,
  incidents,
  critical,
  reductionPct,
}: AlertReductionBannerProps) {
  return (
    <section className="group relative overflow-hidden rounded-[22px] border border-black/[0.04] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:scale-[1.015] hover:-translate-y-1 hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)] hover:border-black/10">
      {/* Full-width seamless animated electric lime gradient glow moving left to right and reverse */}
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -top-12 h-64 w-80 rounded-full bg-[#D7FF3F]/35 blur-3xl"
        animate={{
          left: ["-25%", "105%", "-25%"],
        }}
        transition={{
          duration: 7,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -bottom-12 h-64 w-80 rounded-full bg-[#36C6AF]/25 blur-3xl"
        animate={{
          left: ["105%", "-25%", "105%"],
        }}
        transition={{
          duration: 7,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 w-1/3 bg-[linear-gradient(90deg,transparent_0%,rgba(215,255,63,0.25)_50%,transparent_100%)] blur-2xl"
        animate={{
          left: ["-35%", "110%", "-35%"],
        }}
        transition={{
          duration: 7,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        {/* Correlation funnel */}
        <div className="flex flex-wrap items-center gap-4 sm:gap-6">
          <FunnelStep
            value={rawAlerts}
            label="Raw alerts processed"
            step="01"
          />

          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#F6F7F9] text-[#8A8F98]">
            <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
          </div>

          <FunnelStep
            value={incidents}
            label="Incidents identified"
            step="02"
          />

          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#F6F7F9] text-[#8A8F98]">
            <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
          </div>

          <FunnelStep
            value={critical}
            label="Critical prioritized"
            step="03"
            isCritical={critical > 0}
          />
        </div>

        {/* Noise reduction pill — Electric Lime */}
        <div className="inline-flex items-center gap-2 self-start rounded-full bg-[#D7FF3F] px-4 py-2.5 text-xs font-extrabold text-[#0D0D10] shadow-sm transition-transform duration-150 hover:scale-[1.02] lg:self-center">
          <TrendingDown className="h-4 w-4" strokeWidth={2.5} />
          <span>
            {reductionPct.toLocaleString("en-US", {
              maximumFractionDigits: 1,
            })}
            % Alert Noise Reduced
          </span>
        </div>
      </div>
    </section>
  );
}

function FunnelStep({
  value,
  label,
  step,
  isCritical = false,
}: {
  value: number;
  label: string;
  step: string;
  isCritical?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-[11px] font-bold text-[#8A8F98]">{step}</span>
      <div className="flex flex-col">
        <span
          className={
            isCritical
              ? "text-2xl font-extrabold tracking-tight text-rose-600 leading-tight lg:text-[26px]"
              : "text-2xl font-extrabold tracking-tight text-[#0D0D10] leading-tight lg:text-[26px]"
          }
        >
          {value.toLocaleString("en-US")}
        </span>
        <span className="text-xs font-medium text-[#8A8F98]">{label}</span>
      </div>
    </div>
  );
}
