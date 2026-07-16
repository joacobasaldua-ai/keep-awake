import { appName } from "@/lib/data";

export default function LoadingScreen() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 bg-[#f5f6f4]">
      <div className="flex h-60 w-60 flex-col items-center justify-center gap-8 rounded-[2.25rem] bg-white p-6 shadow-md">
        <span className="flex items-center gap-2">
          <svg viewBox="0 0 24 24" className="h-6 w-6 text-[#2ecc8f]">
            <path
              d="M4 15c2-5 6-8 10-8 3 0 6 1.5 6 4s-3 3-5 2c-3-1.5-2-5 1-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="text-xl font-bold tracking-tight text-neutral-900">
            {appName}
          </span>
        </span>
        <span className="h-16 w-16 animate-spin rounded-full border-[6px] border-[#2ecc8f] border-t-transparent" />
      </div>
    </div>
  );
}
