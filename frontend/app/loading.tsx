/**
 * Route-level Suspense boundary for the dashboard (Phase 22).
 * Next.js wraps the page in <Suspense> with this skeleton as the
 * fallback during navigation, matching the in-page DashboardSkeleton.
 */
export default function DashboardLoading() {
  return (
    <div className="flex animate-pulse flex-col gap-7">
      <div className="flex items-center justify-between">
        <div className="h-10 w-72 rounded-full bg-white border border-black/[0.04]" />
        <div className="h-10 w-44 rounded-full bg-white border border-black/[0.04]" />
      </div>
      <div className="flex flex-col gap-2">
        <div className="h-8 w-60 rounded-full bg-white border border-black/[0.04]" />
        <div className="h-4 w-80 rounded-full bg-white border border-black/[0.04]" />
      </div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-40 rounded-[22px] border border-black/[0.04] bg-white p-6 shadow-sm"
          />
        ))}
      </div>
      <div className="h-28 rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="h-[360px] rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
        <div className="h-[360px] rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
      </div>
      <div className="h-64 rounded-[22px] border border-black/[0.04] bg-white shadow-sm" />
    </div>
  );
}
