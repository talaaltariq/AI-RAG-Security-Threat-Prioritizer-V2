"use client";

import { useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, FileJson, Loader2, UploadCloud, X } from "lucide-react";
import { clsx } from "clsx";

import { uploadEventsFile, type UploadResult } from "@/lib/setup";

export interface FileUploadCardProps {
  /** Called with the pipeline summary once the backend accepts the file. */
  onUploaded: (result: UploadResult) => void;
  /** Called whenever the upload state is cleared or replaced (new file, reset). */
  onReset?: () => void;
}

type UploadStatus = "idle" | "uploading" | "done" | "error";

/** Human-readable file size (KB/MB). */
function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

/**
 * Setup Section 1 — drag-and-drop / click-to-browse event file upload.
 *
 * Accepts .json / .csv, auto-uploads on selection, shows live multipart
 * progress, and surfaces backend rejection messages (400/413) verbatim.
 * DESIGN_SYSTEM.md: white 24px card, pill geometry, lime/teal accents.
 */
export function FileUploadCard({ onUploaded, onReset }: FileUploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const startUpload = async (selected: File) => {
    setFile(selected);
    setStatus("uploading");
    setProgress(0);
    setErrorMessage(null);
    setResult(null);
    onReset?.();
    try {
      const uploadResult = await uploadEventsFile(selected, setProgress);
      setResult(uploadResult);
      setStatus("done");
      onUploaded(uploadResult);
    } catch (err) {
      // Surface the backend's message text directly — do not rewrite it.
      setErrorMessage(err instanceof Error ? err.message : "Upload failed.");
      setStatus("error");
    }
  };

  const handleFiles = (files: FileList | null) => {
    const selected = files?.[0];
    if (selected) void startUpload(selected);
  };

  const clearSelection = () => {
    setFile(null);
    setStatus("idle");
    setProgress(0);
    setErrorMessage(null);
    setResult(null);
    if (inputRef.current) inputRef.current.value = "";
    onReset?.();
  };

  return (
    <div className="flex flex-col gap-4">
      <input
        ref={inputRef}
        type="file"
        accept=".json,.csv"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a .json or .csv event file"
        onClick={() => status !== "uploading" && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (status !== "uploading") handleFiles(e.dataTransfer.files);
        }}
        className={clsx(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-[20px] border-2 border-dashed px-6 py-10 text-center transition-all duration-150",
          dragActive
            ? "border-[#0D0D10] bg-[#D7FF3F]/10"
            : "border-black/[0.1] bg-[#F6F7F9] hover:border-black/25 hover:bg-white",
          status === "uploading" && "pointer-events-none opacity-80"
        )}
      >
        <span
          className={clsx(
            "flex h-12 w-12 items-center justify-center rounded-full",
            dragActive ? "bg-[#D7FF3F] text-[#0D0D10]" : "bg-white text-[#0D0D10] shadow-sm"
          )}
        >
          {status === "uploading" ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <UploadCloud className="h-5 w-5" />
          )}
        </span>
        <div>
          <p className="text-sm font-bold text-[#0D0D10]">
            {dragActive ? "Drop your file to upload" : "Drag & drop your events file here"}
          </p>
          <p className="mt-1 text-xs font-medium text-[#8A8F98]">
            or <span className="font-bold text-[#0D0D10] underline underline-offset-2">click to browse</span> — accepts .json and .csv (max 5 MB)
          </p>
        </div>
      </div>

      {/* Selected file chip */}
      {file && (
        <div className="flex items-center justify-between rounded-[16px] border border-black/[0.06] bg-white px-4 py-3 shadow-sm">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#36C6AF]/15 text-[#2EB39E]">
              <FileJson className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-xs font-bold text-[#0D0D10]">{file.name}</p>
              <p className="text-[11px] font-medium text-[#8A8F98]">{formatSize(file.size)}</p>
            </div>
          </div>
          {status !== "uploading" && (
            <button
              type="button"
              onClick={clearSelection}
              aria-label="Remove selected file"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[#8A8F98] transition-colors hover:bg-[#F6F7F9] hover:text-[#0D0D10]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Upload progress bar (pill track per DESIGN_SYSTEM.md §4.7) */}
      {status === "uploading" && (
        <div className="flex flex-col gap-1.5">
          <div className="h-2 w-full overflow-hidden rounded-full bg-[#ECEEF2]">
            <div
              className="h-full rounded-full bg-[#D7FF3F] transition-all duration-200 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-[11px] font-semibold text-[#8A8F98]">
            Uploading &amp; processing… {progress}%
          </p>
        </div>
      )}

      {/* Success state */}
      {status === "done" && result && (
        <div className="flex items-center gap-3 rounded-[18px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-semibold text-emerald-800 animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>
            ✓ {result.events_processed} events uploaded — {result.incidents_created} incident
            {result.incidents_created === 1 ? "" : "s"} correlated by the pipeline.
          </span>
        </div>
      )}

      {/* Backend rejection — message surfaced verbatim */}
      {status === "error" && errorMessage && (
        <div className="flex items-start gap-3 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-semibold text-rose-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
