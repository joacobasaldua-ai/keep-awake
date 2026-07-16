"use client";

import type { Product } from "@/lib/types";
import SwipeToConfirm from "./SwipeToConfirm";

export default function WithdrawScreen({
  items,
  venue,
  time,
  onConfirm,
}: {
  items: Product[];
  venue: string;
  time: string;
  onConfirm: () => void;
}) {
  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-[#fa8f88] to-[#f66a63] px-5 pt-8">
      <h1 className="text-3xl font-bold text-neutral-900">Retiro</h1>

      <div className="mt-5 rounded-2xl border border-white/40 bg-[#fb7e77] px-4 py-3 text-center font-semibold text-white">
        &iexcl;NO hagas swipe antes de retirar!
      </div>

      <div className="mt-5 flex-1 overflow-y-auto rounded-3xl bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-neutral-200 text-sm font-bold text-neutral-700">
              {venue.charAt(0)}
            </span>
            <div>
              <p className="font-bold leading-tight text-neutral-900">{venue}</p>
              <p className="text-sm text-neutral-500">Ingreso&nbsp;-&nbsp;.</p>
            </div>
          </div>
          <p className="whitespace-nowrap text-sm font-semibold text-neutral-500">
            Hora {time}
          </p>
        </div>

        <div className="my-4 h-px w-full bg-neutral-100" />

        <div className="flex items-center justify-between">
          <p className="font-bold text-neutral-900">Est&aacute;s retirando</p>
          <p className="font-bold text-neutral-900">
            Total:{items.length}
          </p>
        </div>

        <ul className="mt-3 space-y-2">
          {items.map((item) => (
            <li key={item.id} className="flex gap-2 text-neutral-800">
              <span className="font-semibold">1</span>
              <span>{item.name}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="shrink-0 py-5">
        <SwipeToConfirm label="Retirado" onConfirm={onConfirm} />
        <p className="mt-3 text-center text-sm font-medium text-white/90">
          Desliz&aacute; para confirmar que retiraste tus productos
        </p>
      </div>
    </div>
  );
}
