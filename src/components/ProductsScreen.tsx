"use client";

import type { Product } from "@/lib/types";
import { DrinkIcon } from "./icons";
import BottomNav from "./BottomNav";

export default function ProductsScreen({
  products,
  selected,
  onToggle,
  onToggleAll,
  onConfirm,
}: {
  products: Product[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: () => void;
  onConfirm: () => void;
}) {
  const allSelected = products.length > 0 && selected.size === products.length;
  const count = selected.size;

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-5 pt-8">
        <h1 className="text-3xl font-bold text-neutral-900">Mis productos</h1>

        <div className="mt-6 flex items-center justify-between gap-4 rounded-3xl bg-white p-5 shadow-sm">
          <div>
            <p className="text-lg font-semibold leading-snug text-neutral-900">
              Seleccion&aacute; tus
              <br />
              productos.
            </p>
            <p className="mt-1 text-sm text-neutral-500">
              Retiralos por el mostrador.
            </p>
          </div>
          <button
            type="button"
            onClick={onToggleAll}
            disabled={products.length === 0}
            className={`shrink-0 rounded-full border px-6 py-3 text-sm font-medium transition-colors ${
              allSelected
                ? "border-[#0c2622] bg-[#0c2622] text-white"
                : "border-neutral-300 bg-white text-neutral-900"
            }`}
          >
            Todos
          </button>
        </div>

        <div className="mt-5 space-y-3">
          {products.length === 0 && (
            <p className="mt-16 text-center text-neutral-400">
              No ten&eacute;s productos pendientes de retiro.
            </p>
          )}
          {products.map((p) => {
            const checked = selected.has(p.id);
            return (
              <label
                key={p.id}
                htmlFor={p.id}
                className={`flex cursor-pointer items-center gap-4 rounded-2xl border bg-white p-4 transition-colors ${
                  checked ? "border-neutral-900" : "border-neutral-200"
                }`}
              >
                <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-amber-50 text-amber-600">
                  <DrinkIcon className="h-7 w-7" />
                </span>
                <span className="flex-1 font-semibold text-neutral-900">
                  {p.name}
                </span>
                <input
                  id={p.id}
                  type="checkbox"
                  className="peer sr-only"
                  checked={checked}
                  onChange={() => onToggle(p.id)}
                />
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md border-2 transition-colors ${
                    checked
                      ? "border-[#0c2622] bg-[#0c2622]"
                      : "border-neutral-300 bg-white"
                  }`}
                >
                  {checked && (
                    <svg viewBox="0 0 24 24" className="h-4 w-4 text-white">
                      <path
                        d="M5 12.5 9.5 17 19 7"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </span>
              </label>
            );
          })}
        </div>
      </div>

      <div className="shrink-0 border-t border-black/5 bg-[#f5f6f4] px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="whitespace-nowrap text-sm font-medium text-neutral-700">
            {count} {count === 1 ? "Producto" : "Productos"}
          </span>
          <button
            type="button"
            onClick={onConfirm}
            disabled={count === 0}
            className={`flex-1 rounded-full py-3.5 text-center font-semibold transition-colors ${
              count === 0
                ? "cursor-not-allowed bg-neutral-200 text-neutral-400"
                : "bg-gradient-to-r from-[#5eeab0] to-[#33d38f] text-[#0c2622] shadow-sm"
            }`}
          >
            Confirmar Retiro
          </button>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
