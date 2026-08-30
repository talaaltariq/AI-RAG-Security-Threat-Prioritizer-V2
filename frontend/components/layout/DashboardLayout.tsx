"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#F6F7F9]">
      {/* Fixed obsidian sidebar with collapse/expand state */}
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

      {/* Main content area — smooth margin transition matching sidebar state */}
      <main
        className={`flex-1 overflow-y-auto bg-[#F6F7F9] transition-all duration-300 ease-in-out ${
          collapsed ? "ml-[112px]" : "ml-[272px]"
        }`}
      >
        <div className="mx-auto flex min-h-full w-full max-w-[1440px] flex-col gap-7 px-8 pt-4 pb-8">
          {children}
        </div>
      </main>
    </div>
  );
}
