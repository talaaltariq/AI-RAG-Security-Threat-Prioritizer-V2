"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListChecks,
  ShieldAlert,
  Settings,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { label: "Setup", href: "/setup", icon: ListChecks },
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Threat Queue", href: "/threats", icon: ShieldAlert },
  { label: "Settings", href: "/settings", icon: Settings },
];

export interface SidebarProps {
  collapsed?: boolean;
  setCollapsed?: (value: boolean | ((prev: boolean) => boolean)) => void;
}

/**
 * ThreatIQ sidebar — DESIGN_SYSTEM.md §4.2
 * Fixed left, full height, expandable/collapsible (240px <-> 80px), solid obsidian (#0D0D10).
 * Active nav item is an Electric Lime pill (#D7FF3F) with obsidian text/icon.
 */
export function Sidebar({
  collapsed: externalCollapsed,
  setCollapsed: externalSetCollapsed,
}: SidebarProps) {
  const pathname = usePathname();
  const [internalCollapsed, setInternalCollapsed] = useState(false);

  const isCollapsed = externalCollapsed ?? internalCollapsed;
  const toggleCollapse = () => {
    if (externalSetCollapsed) {
      externalSetCollapsed((prev) => !prev);
    } else {
      setInternalCollapsed((prev) => !prev);
    }
  };

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside
      className={clsx(
        "fixed top-4 bottom-4 left-4 z-40 flex flex-col justify-between bg-[#0D0D10] py-7 text-white transition-all duration-300 ease-in-out rounded-[24px] shadow-xl border border-white/5",
        isCollapsed ? "w-20 px-2" : "w-60 px-4"
      )}
    >
      {/* Expand / Contract Toggle Button */}
      <button
        type="button"
        onClick={toggleCollapse}
        className="absolute -right-3.5 top-8 z-50 flex h-7 w-7 items-center justify-center rounded-full bg-[#0D0D10] text-[#D7FF3F] border border-white/10 shadow-md transition-transform duration-200 hover:scale-110 hover:bg-[#1A1A20]"
        title={isCollapsed ? "Expand sidebar" : "Contract sidebar"}
        aria-label={isCollapsed ? "Expand sidebar" : "Contract sidebar"}
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4" strokeWidth={2.5} />
        ) : (
          <ChevronLeft className="h-4 w-4" strokeWidth={2.5} />
        )}
      </button>

      <div>
        {/* Brand: Full custom ThreatIQ logo (horizontally centered) */}
        <Link
          href="/"
          className="mb-8 flex items-center justify-center px-1 py-1"
        >
          <img
            src={isCollapsed ? "/logo-icon.png" : "/logo-horizontal.png"}
            alt="ThreatIQ"
            className={clsx(
              "object-contain transition-all duration-300 hover:scale-[1.03]",
              isCollapsed ? "h-9 w-9" : "h-12 w-auto max-w-full"
            )}
          />
        </Link>

        {/* Navigation */}
        <nav className="flex flex-col gap-2">
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={label}
                href={href}
                title={isCollapsed ? label : undefined}
                className={clsx(
                  "flex items-center gap-3 rounded-full py-3 text-sm font-semibold transition-all duration-150 ease-out",
                  isCollapsed ? "justify-center px-0 w-12 h-12 mx-auto" : "px-4",
                  active
                    ? "bg-[#D7FF3F] font-bold text-[#0D0D10] shadow-sm"
                    : "text-[#8E95A5] hover:bg-white/[0.06] hover:text-white"
                )}
              >
                <Icon
                  className="h-[18px] w-[18px] shrink-0"
                  strokeWidth={active ? 2.5 : 1.75}
                />
                {!isCollapsed && <span>{label}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Open Source GitHub Community Widget */}
      {isCollapsed ? (
        <div className="relative mt-auto flex justify-center">
          <a
            href="https://github.com/talaaltariq/AI-RAG-Security-Threat-Prioritizer-V2"
            target="_blank"
            rel="noreferrer"
            title="AI-RAG-Security-Threat-Prioritizer-V2 on GitHub"
            className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#D8FF3F] text-black shadow-sm transition-transform hover:scale-105"
          >
            <svg
              className="h-5 w-5 fill-current"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
          </a>
        </div>
      ) : (
        <div className="relative mt-auto overflow-hidden rounded-2xl bg-[#D8FF3F] p-4 text-black shadow-sm">
          {/* Subtle background decorative wave */}
          <svg
            className="pointer-events-none absolute -right-4 -top-4 h-28 w-28 text-black/[0.05]"
            viewBox="0 0 100 100"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
          >
            <path d="M10,80 Q30,20 60,60 T100,20" />
          </svg>

          <div className="relative z-10">
            {/* Header / Badge */}
            <div className="flex items-center justify-between">
              <span className="bg-black/10 text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full uppercase">
                OPEN SOURCE
              </span>
              <ArrowUpRight className="h-3.5 w-3.5 text-black/50" />
            </div>

            {/* Content & Iconography */}
            <div className="my-2.5 flex items-center gap-2.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-black text-white p-1.5">
                <svg
                  className="h-full w-full fill-current"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <a
                  href="https://github.com/talaaltariq/AI-RAG-Security-Threat-Prioritizer-V2"
                  target="_blank"
                  rel="noreferrer"
                  title="AI-RAG-Security-Threat-Prioritizer-V2"
                  className="block text-xs font-bold leading-tight text-black truncate hover:underline"
                >
                  AI-RAG-Security-Threat-Prioritizer-V2
                </a>
                <p className="text-[10px] font-medium text-black/60">
                  MIT / Apache 2.0
                </p>
              </div>
            </div>

            {/* Tagline */}
            <p className="mb-3 text-[11px] font-medium leading-snug text-black/80">
              Community rules, detection schemas &amp; MITRE vectors.
            </p>

            {/* Action Button / CTA */}
            <a
              href="https://github.com/talaaltariq/AI-RAG-Security-Threat-Prioritizer-V2"
              target="_blank"
              rel="noreferrer"
              className="bg-black text-white text-xs font-semibold py-2 rounded-xl w-full flex items-center justify-center gap-1.5 hover:bg-black/90 transition-colors"
            >
              View on GitHub ↗
            </a>
          </div>
        </div>
      )}
    </aside>
  );
}
