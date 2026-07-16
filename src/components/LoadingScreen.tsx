import SkipitLogo from "./SkipitLogo";

export default function LoadingScreen() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 bg-[#f5f6f4]">
      <div className="flex h-60 w-60 flex-col items-center justify-center gap-8 rounded-[2.25rem] bg-white p-6 shadow-md">
        <SkipitLogo />
        <span className="h-16 w-16 animate-spin rounded-full border-[6px] border-[#2ecc8f] border-t-transparent" />
      </div>
    </div>
  );
}
