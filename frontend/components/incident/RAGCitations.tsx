import { BookOpen, Database } from "lucide-react";

import type { RAGCitation } from "@/lib/incident";

export interface RAGCitationsProps {
  /** Retrieved threat-intelligence documents linked to the incident. */
  ragResults: RAGCitation[];
}

const PREVIEW_LENGTH = 160;

/** Human-readable source labels for the knowledge-base collections. */
const SOURCE_LABELS: Record<string, string> = {
  mitre_attack: "MITRE ATT&CK v14",
  cve_summaries: "NVD / CVE Records",
};

function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

function sourceBadgeId(result: RAGCitation): string {
  return (
    result.technique_id ??
    result.cve_id ??
    result.id.slice(0, 8).toUpperCase()
  );
}

/**
 * ThreatIQ RAG citation list — each retrieved threat-intelligence source
 * rendered as a light card with a mono source-ID tag chip, relevance chip,
 * preview text, and origin collection.
 */
export function RAGCitations({ ragResults }: RAGCitationsProps) {
  if (ragResults.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2.5 py-8 text-center">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-50 text-teal-600">
          <BookOpen className="h-5 w-5" strokeWidth={2} />
        </span>
        <p className="text-xs font-medium text-[#8A8F98]">
          No threat intelligence retrieved for this incident.
        </p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-3.5">
      {ragResults.map((result) => {
        const preview =
          result.content.length > PREVIEW_LENGTH
            ? `${result.content.slice(0, PREVIEW_LENGTH)}…`
            : result.content;
        return (
          <li
            key={result.id}
            className="rounded-[18px] border border-black/[0.05] bg-[#F9FAFB] p-4.5 transition-all duration-150 hover:bg-white hover:border-black/[0.08] hover:shadow-sm"
          >
            <div className="flex items-center justify-between gap-3">
              {/* Source ID tag chip (top-left) */}
              <span className="inline-flex items-center rounded-full bg-white border border-black/[0.08] px-2.5 py-0.5 font-mono text-[11px] font-extrabold text-[#0D0D10] shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
                {sourceBadgeId(result)}
              </span>
              {/* Relevance soft chip (top-right) */}
              <span className="inline-flex items-center rounded-full bg-teal-50 border border-teal-200/80 px-2.5 py-0.5 text-[11px] font-bold text-teal-700 shadow-[0_1px_2px_rgba(13,148,136,0.04)]">
                {(result.relevance_score * 100).toFixed(0)}% relevant
              </span>
            </div>

            <p className="mt-2.5 text-xs font-medium leading-relaxed text-[#374151]">
              {preview}
            </p>

            <p className="mt-3 flex items-center gap-1.5 text-[11px] font-semibold text-[#8A8F98]">
              <Database className="h-3.5 w-3.5 text-teal-600" strokeWidth={2} />
              Source: {sourceLabel(result.source)}
            </p>
          </li>
        );
      })}
    </ul>
  );
}

