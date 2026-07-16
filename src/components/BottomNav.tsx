import { BagIcon, CartIcon, StoreIcon, UserIcon } from "./icons";

const items = [
  { icon: StoreIcon, label: "Tienda" },
  { icon: CartIcon, label: "Carrito" },
  { icon: BagIcon, label: "Mis productos" },
  { icon: UserIcon, label: "Perfil" },
] as const;

export default function BottomNav({ active = 2 }: { active?: number }) {
  return (
    <nav className="flex shrink-0 items-center justify-around border-t border-black/5 bg-[#f5f6f4] px-4 py-4">
      {items.map(({ icon: Icon, label }, i) => (
        <button
          key={label}
          type="button"
          aria-label={label}
          aria-current={i === active}
          className={`flex h-11 w-11 items-center justify-center rounded-full transition-colors ${
            i === active ? "text-[#2ecc8f]" : "text-neutral-900"
          }`}
        >
          <Icon className="h-6 w-6" />
        </button>
      ))}
    </nav>
  );
}
