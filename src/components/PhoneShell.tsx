export default function PhoneShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-full w-full flex items-center justify-center bg-neutral-200 p-0 sm:p-6">
      <div className="relative flex h-dvh w-full max-w-[440px] flex-col overflow-hidden bg-[#f5f6f4] sm:h-[880px] sm:rounded-[2.5rem] sm:shadow-2xl sm:ring-8 sm:ring-neutral-900/90">
        {children}
      </div>
    </div>
  );
}
