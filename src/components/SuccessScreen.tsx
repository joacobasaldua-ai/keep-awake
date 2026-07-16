import { CheckIcon } from "./icons";

export default function SuccessScreen({ onDone }: { onDone: () => void }) {
  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-[#fa8f88] to-[#f66a63] px-5 pt-8">
      <h1 className="text-3xl font-bold text-neutral-900">Retiro</h1>

      <div className="flex flex-1 flex-col items-center justify-center gap-6">
        <span className="flex h-24 w-24 items-center justify-center rounded-full bg-[#f5f6f4]">
          <CheckIcon className="h-10 w-10 text-[#2ecc8f]" />
        </span>
        <p className="text-xl font-bold text-neutral-900">
          &iexcl;Retiraste tus productos!
        </p>
      </div>

      <div className="shrink-0 pb-8">
        <button
          type="button"
          onClick={onDone}
          className="w-full rounded-full bg-white/90 py-3.5 text-center font-semibold text-[#0c2622] shadow-sm"
        >
          Volver a mis productos
        </button>
      </div>
    </div>
  );
}
