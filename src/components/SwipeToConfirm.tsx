"use client";

import { useRef, useState } from "react";
import { ChevronRightIcon } from "./icons";

const THUMB = 56;
const THRESHOLD = 0.72;

export default function SwipeToConfirm({
  label,
  onConfirm,
}: {
  label: string;
  onConfirm: () => void;
}) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [dragX, setDragX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [settled, setSettled] = useState(false);
  const startX = useRef(0);
  const maxX = useRef(0);

  function getMax() {
    const track = trackRef.current;
    if (!track) return 0;
    return Math.max(track.clientWidth - THUMB - 8, 0);
  }

  function onPointerDown(e: React.PointerEvent) {
    if (settled) return;
    (e.target as Element).setPointerCapture(e.pointerId);
    startX.current = e.clientX - dragX;
    maxX.current = getMax();
    setDragging(true);
  }

  function onPointerMove(e: React.PointerEvent) {
    if (!dragging || settled) return;
    const next = Math.min(Math.max(e.clientX - startX.current, 0), maxX.current);
    setDragX(next);
  }

  function finish(success: boolean) {
    setDragging(false);
    if (success) {
      setDragX(maxX.current);
      setSettled(true);
      onConfirm();
    } else {
      setDragX(0);
    }
  }

  function onPointerUp() {
    if (!dragging || settled) return;
    const ratio = maxX.current === 0 ? 0 : dragX / maxX.current;
    finish(ratio >= THRESHOLD);
  }

  return (
    <div
      ref={trackRef}
      className="relative h-16 w-full select-none overflow-hidden rounded-full bg-white/40"
    >
      <div
        className="pointer-events-none absolute inset-y-0 left-0 rounded-full bg-white/30"
        style={{ width: dragX + THUMB }}
      />
      <span className="pointer-events-none absolute inset-0 flex items-center justify-center font-medium text-[#0c2622]/70">
        {label}
      </span>
      <div
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        className={`absolute left-1 top-1 flex h-14 w-14 items-center justify-center rounded-full bg-[#c9f7e2] text-[#0c2622] shadow ${
          dragging ? "cursor-grabbing" : "cursor-grab"
        }`}
        style={{
          transform: `translateX(${dragX}px)`,
          transition: dragging ? "none" : "transform 200ms ease",
        }}
      >
        <ChevronRightIcon className="h-6 w-6" />
      </div>
    </div>
  );
}
