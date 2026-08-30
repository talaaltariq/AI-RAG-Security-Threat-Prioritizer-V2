import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

// DESIGN_SYSTEM.md §2.2 — Inter (sans-serif) + JetBrains Mono (monospace)
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ThreatIQ — AI Security Threat Prioritizer",
  description:
    "AI-powered RAG security threat prioritization dashboard for cybersecurity analysts.",
  icons: {
    icon: "/logo-icon.png",
    shortcut: "/logo-icon.png",
    apple: "/logo-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} h-full bg-[#F6F7F9] text-content-primary font-sans antialiased`}
      >
        <DashboardLayout>{children}</DashboardLayout>
      </body>
    </html>
  );
}
