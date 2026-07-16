"use client";

import { useMemo, useState } from "react";
import PhoneShell from "@/components/PhoneShell";
import ProductsScreen from "@/components/ProductsScreen";
import WithdrawScreen from "@/components/WithdrawScreen";
import LoadingScreen from "@/components/LoadingScreen";
import SuccessScreen from "@/components/SuccessScreen";
import { initialProducts } from "@/lib/data";
import type { Product, Screen } from "@/lib/types";

const LOADING_DELAY_MS = 1000;

export default function Home() {
  const [products, setProducts] = useState<Product[]>(initialProducts);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [screen, setScreen] = useState<Screen>("products");
  const [withdrawTime, setWithdrawTime] = useState("");

  const withdrawItems = useMemo(
    () => products.filter((p) => selected.has(p.id)),
    [products, selected]
  );

  function toggleProduct(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) =>
      prev.size === products.length ? new Set() : new Set(products.map((p) => p.id))
    );
  }

  function goToWithdraw() {
    setWithdrawTime(
      new Date().toLocaleTimeString("es-AR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    );
    setScreen("withdraw");
  }

  function confirmWithdraw() {
    setScreen("loading");
    window.setTimeout(() => {
      setProducts((prev) => prev.filter((p) => !selected.has(p.id)));
      setScreen("success");
    }, LOADING_DELAY_MS);
  }

  function backToProducts() {
    setSelected(new Set());
    setScreen("products");
  }

  return (
    <PhoneShell>
      {screen === "products" && (
        <ProductsScreen
          products={products}
          selected={selected}
          onToggle={toggleProduct}
          onToggleAll={toggleAll}
          onConfirm={goToWithdraw}
        />
      )}
      {screen === "withdraw" && (
        <WithdrawScreen
          items={withdrawItems}
          venue={withdrawItems[0]?.venue ?? ""}
          time={withdrawTime}
          onConfirm={confirmWithdraw}
        />
      )}
      {screen === "loading" && <LoadingScreen />}
      {screen === "success" && <SuccessScreen onDone={backToProducts} />}
    </PhoneShell>
  );
}
