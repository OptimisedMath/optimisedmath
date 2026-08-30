'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { DECONSTRUCTION_ORDERING_SEPARATOR } from '@/lib/session';

interface DeconstructionOrderingInputProps {
  items: string[];
  disabled: boolean;
  onSubmit: (answer: string) => Promise<void>;
}

function swapWithNeighbour(order: string[], index: number, offset: number): string[] {
  const target = index + offset;
  if (target < 0 || target >= order.length) return order;
  const next = [...order];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

/**
 * The ordering-input step control (#198): the Student arranges `items` into
 * order with up/down moves rather than typing a value. The caller keys its
 * wrapper by step index (`DeconstructionStep`'s question card), so a fresh
 * step remounts this component and re-seeds `order` from `items` for free.
 */
export default function DeconstructionOrderingInput({
  items,
  disabled,
  onSubmit,
}: DeconstructionOrderingInputProps) {
  const [order, setOrder] = useState(items);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(order.join(DECONSTRUCTION_ORDERING_SEPARATOR));
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <ol data-deconstruction-ordering-list className="flex flex-col gap-2">
        {order.map((label, index) => (
          <li
            key={label}
            data-deconstruction-ordering-item
            className="flex items-center gap-3 rounded-xl border border-white/10 bg-black/40 px-4 py-2 text-white"
          >
            <span className="w-5 text-sm font-bold text-slate-500">{index + 1}</span>
            <span className="flex-1">{label}</span>
            <button
              type="button"
              aria-label="Przesuń w górę"
              disabled={disabled || index === 0}
              onClick={() => setOrder((current) => swapWithNeighbour(current, index, -1))}
              className="text-slate-400 transition hover:text-white disabled:opacity-30"
            >
              ▲
            </button>
            <button
              type="button"
              aria-label="Przesuń w dół"
              disabled={disabled || index === order.length - 1}
              onClick={() => setOrder((current) => swapWithNeighbour(current, index, 1))}
              className="text-slate-400 transition hover:text-white disabled:opacity-30"
            >
              ▼
            </button>
          </li>
        ))}
      </ol>
      <Button type="submit" size="lg" disabled={disabled} className="self-start">
        Sprawdź
      </Button>
    </form>
  );
}
