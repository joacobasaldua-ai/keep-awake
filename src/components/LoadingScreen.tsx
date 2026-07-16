import { appName } from "@/lib/data";

export default function LoadingScreen() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 bg-[#f5f6f4]">
      <div className="flex h-44 w-44 flex-col items-center justify-center gap-6 rounded-3xl bg-white p-6 shadow-md">
        <span className="text-lg font-bold tracking-tight text-neutral-900">
          {appName}
        </span>
        <span className="h-14 w-14 animate-spin rounded-full border-4 border-[#2ecc8f] border-t-transparent" />
      </div>
    </div>
  );
}
