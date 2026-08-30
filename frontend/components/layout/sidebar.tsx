"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShieldAlert,
  Settings,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { clsx } from "clsx";

const NAV_ITEMS = [
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

      {/* Promo / Go Pro card (matches GoodBoard reference lime card) */}
      {isCollapsed ? (
        <div className="relative mt-auto flex justify-center">
          <button
            type="button"
            title="ThreatIQ Pro+"
            className="flex h-11 w-11 items-center justify-center rounded-full bg-[#D7FF3F] text-[#0D0D10] font-extrabold text-[11px] shadow-sm transition-transform hover:scale-105"
          >
            PRO+
          </button>
        </div>
      ) : (
        <div className="relative mt-auto overflow-hidden rounded-[22px] bg-[#D7FF3F] p-5 text-[#0D0D10] shadow-sm">
          {/* Subtle background decorative wave */}
          <svg
            className="pointer-events-none absolute -right-4 -top-4 h-28 w-28 text-black/[0.06]"
            viewBox="0 0 100 100"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
          >
            <path d="M10,80 Q30,20 60,60 T100,20" />
          </svg>

          <div className="relative z-10">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-0.5 rounded-full bg-black/10 px-2.5 py-0.5 text-[11px] font-extrabold tracking-wider text-[#0D0D10]">
                PRO+
              </span>
            </div>

            <div className="my-3 flex items-center justify-center py-1">
              {/* Wavy brand glyph like reference */}
              <svg
                className="h-12 w-12 text-[#0D0D10]"
                viewBox="0 0 48 48"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14 18 C14 10, 26 10, 26 22 C26 34, 38 34, 38 26" />
              </svg>
            </div>

            <p className="mb-3 text-center text-xs font-bold leading-tight text-[#0D0D10]">
              Get all features on ThreatIQ Pro
            </p>

            <button
              type="button"
              className="flex w-full items-center justify-center gap-1.5 rounded-full bg-[#0D0D10] px-4 py-2.5 text-xs font-bold text-white transition-transform duration-150 ease-out hover:scale-[1.02] active:scale-[0.98]"
            >
              Go Pro now
              <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
