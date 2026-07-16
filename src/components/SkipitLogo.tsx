export default function SkipitLogo({ className }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className ?? ""}`}>
      <svg viewBox="0 0 100 60" className="h-7 w-auto" aria-hidden="true">
        <path
          d="M6 42 C6 20 28 8 50 8 C66 8 76 17 76 27 C76 35 67 39 58 35 C51 32 52 24 60 22"
          fill="none"
          stroke="#3ecf8e"
          strokeWidth="8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="83" cy="15" r="10" fill="#3ecf8e" />
        <circle cx="87" cy="12" r="2.2" fill="white" />
      </svg>
      <span className="text-2xl font-extrabold tracking-tight text-[#0c2622]">
        skipit
      </span>
    </span>
  );
}
