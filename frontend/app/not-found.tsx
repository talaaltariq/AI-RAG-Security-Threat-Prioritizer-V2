import Link from "next/link";
import { ShieldAlert } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#0D0D10] text-[#D7FF3F] shadow-lg mb-6">
        <ShieldAlert className="h-8 w-8" />
      </div>
      <h1 className="text-4xl font-extrabold tracking-tight text-[#0D0D10]">
        404 — Page Not Found
      </h1>
      <p className="mt-2 text-sm text-[#52525B] max-w-md">
        The security asset or page you are requesting could not be located in the ThreatIQ system index.
      </p>
      <Link
        href="/"
        className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#0D0D10] px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-[#202024] transition-colors"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
