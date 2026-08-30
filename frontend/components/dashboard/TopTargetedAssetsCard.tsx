"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ArrowUpRight, Server } from "lucide-react";
import type { IncidentSummary } from "@/lib/types";

interface TopTargetedAssetsCardProps {
  incidents: IncidentSummary[];
}

export function TopTargetedAssetsCard({ incidents }: TopTargetedAssetsCardProps) {
  // Aggregate incidents by asset
  const topAssets = useMemo(() => {
    if (!incidents || incidents.length === 0) {
      return [
        {
          asset: "prod-db-primary.internal",
          technique: "T1059: Command & Scripting",
          criticality: "Tier 1",
          score: 92,
          incidentCount: 4,
          maxScore: 100,
        },
        {
          asset: "auth-gateway-node-02",
          technique: "T1078: Valid Accounts",
          criticality: "Tier 1",
          score: 84,
          incidentCount: 3,
          maxScore: 100,
        },
        {
          asset: "vpn-concentrator-us-east",
          technique: "T1133: External Remote",
          criticality: "Tier 2",
          score: 72,
          incidentCount: 2,
          maxScore: 100,
        },
        {
          asset: "k8s-ingress-controller",
          technique: "T1190: Exploit Public App",
          criticality: "Tier 2",
          score: 65,
          incidentCount: 2,
          maxScore: 100,
        },
      ];
    }

    // Group incidents by asset
    const map = new Map<
      string,
      {
        asset: string;
        technique: string;
        criticality: string;
        maxScore: number;
        incidentCount: number;
      }
    >();

    for (const inc of incidents) {
      const existing = map.get(inc.asset);
      if (!existing) {
        map.set(inc.asset, {
          asset: inc.asset,
          technique: inc.mitre_technique ?? "T1059 (Att&ck)",
          criticality: inc.asset_criticality || "Tier 2",
          maxScore: inc.total_score,
          incidentCount: 1,
        });
      } else {
        existing.incidentCount += 1;
        if (inc.total_score > existing.maxScore) {
          existing.maxScore = inc.total_score;
        }
      }
    }

    return Array.from(map.values())
      .sort((a, b) => b.maxScore - a.maxScore)
      .slice(0, 4);
  }, [incidents]);

  return (
    <div className="group flex flex-col justify-between rounded-[22px] border border-black/[0.04] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:scale-[1.015] hover:-translate-y-1 hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)] hover:border-black/10">
      {/* Header */}
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-[#0D0D10]">
            Top Targeted Assets
          </h2>
          <p className="text-xs font-medium text-[#8A8F98]">
            Systems with highest cumulative threat severity and activity
          </p>
        </div>
        <Link
          href="/threats"
          className="inline-flex items-center gap-1 text-xs font-bold text-[#0D0D10] hover:text-black transition-colors"
        >
          View queue
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Asset Table / List matching GoodBoard Top Products layout */}
      <div className="overflow-hidden rounded-xl border border-black/[0.06]">
        <table className="w-full text-left text-xs bg-white">
          <thead>
            <tr className="bg-[#0D0D10] text-white/80 border-b-2 border-[#D7FF3F] text-[11px] font-semibold">
              <th className="py-3 pl-3 font-medium">#</th>
              <th className="py-3 font-medium">Target Asset</th>
              <th className="py-3 font-medium hidden sm:table-cell">Technique</th>
              <th className="py-3 pr-3 text-right font-medium">Risk Density</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/[0.04]">
            {topAssets.map((item, index) => {
              const rank = String(index + 1).padStart(2, "0");

              return (
                <tr key={item.asset} className="group transition-colors hover:bg-[#F6F7F9]/60">
                  {/* Rank */}
                  <td className="py-3.5 pl-3 font-bold text-[#8A8F98] group-hover:text-[#0D0D10]">
                    {rank}
                  </td>

                  {/* Asset Name */}
                  <td className="py-3.5 pr-3">
                    <div className="flex items-center gap-2">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#F6F7F9] text-[#0D0D10]">
                        <Server className="h-3.5 w-3.5" />
                      </div>
                      <div className="flex flex-col">
                        <span className="font-bold text-[#0D0D10]">{item.asset}</span>
                        <span className="text-[10px] font-medium text-[#8A8F98] sm:hidden">
                          {item.technique}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* MITRE Technique */}
                  <td className="py-3.5 pr-3 hidden sm:table-cell">
                    <span className="inline-flex items-center rounded-md bg-[#F6F7F9] px-2 py-0.5 text-[10px] font-semibold text-[#0D0D10] border border-black/[0.04]">
                      {item.technique}
                    </span>
                  </td>

                  {/* Progress / Risk Score */}
                  <td className="py-3.5 pr-3 text-right">
                    <div className="flex items-center justify-end gap-3">
                      {/* Dual-color capsule progress bar like reference */}
                      <div className="hidden w-28 sm:flex h-2 overflow-hidden rounded-full bg-[#F6F7F9]">
                        <div
                          className="h-full bg-[#D7FF3F] rounded-l-full"
                          style={{ width: `${Math.min(item.maxScore * 0.7, 70)}%` }}
                        />
                        <div
                          className="h-full bg-[#36C6AF] rounded-r-full"
                          style={{ width: `${Math.max(item.maxScore * 0.3, 10)}%` }}
                        />
                      </div>
                      <span className="font-extrabold text-[#0D0D10] min-w-[32px]">
                        {item.maxScore}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
