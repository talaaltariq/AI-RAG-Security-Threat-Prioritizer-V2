/**
 * Route-level Suspense boundary for the threat queue (Phase 22).
 * Matches the in-page loading skeleton of app/threats/page.tsx.
 */
export default function ThreatQueueLoading() {
  return (
    <div className="flex animate-pulse flex-col gap-7">
      <div className="flex items-center justify-between">
        <div className="h-10 w-full max-w-md rounded-full bg-white border border-black/[0.04]" />
      </div>
      <div className="flex flex-col gap-2">
        <div className="h-8 w-52 rounded-full bg-white border border-black/[0.04]" />
        <div className="h-4 w-72 rounded-full bg-white border border-black/[0.04]" />
      </div>
      <div className="h-14 rounded-[20px] border border-black/[0.04] bg-white shadow-sm" />
      <div className="h-[480px] rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
    </div>
  );
}
