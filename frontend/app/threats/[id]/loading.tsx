/**
 * Route-level Suspense boundary for the incident detail page (Phase 22).
 * Matches the in-page skeleton of app/threats/[id]/page.tsx.
 */
export default function IncidentDetailLoading() {
  return (
    <div className="flex animate-pulse flex-col gap-7">
      <div className="flex items-center justify-between">
        <div className="h-10 w-full max-w-md rounded-full bg-white border border-black/[0.04]" />
      </div>
      <div className="h-4 w-48 rounded-full bg-white border border-black/[0.04]" />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <div className="h-72 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
          <div className="h-80 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
          <div className="h-64 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
        </div>
        <div className="flex flex-col gap-6">
          <div className="h-96 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
          <div className="h-56 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
          <div className="h-28 rounded-[24px] border border-black/[0.04] bg-white shadow-sm" />
        </div>
      </div>
    </div>
  );
}
