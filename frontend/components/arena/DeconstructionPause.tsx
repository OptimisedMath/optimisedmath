'use client';

interface DeconstructionPauseProps {
  onTap: () => void;
}

/**
 * The 4-second pause between the triggering Feedback and the takeover. Renders
 * as a transparent, full-screen tap target over the arena — the Trap prose
 * underneath stays exactly as it is, so it is readable, but every tap advances
 * straight to the takeover rather than making anyone wait out the timer.
 */
export default function DeconstructionPause({ onTap }: DeconstructionPauseProps) {
  return (
    <button
      type="button"
      onClick={onTap}
      aria-label="Przejdź dalej"
      className="fixed inset-0 z-40 flex cursor-pointer items-end justify-center bg-transparent pb-6"
    >
      <span className="animate-pulse rounded-full bg-slate-900/80 px-4 py-2 text-xs font-semibold text-white shadow-lg">
        Stuknij, aby przejść dalej →
      </span>
    </button>
  );
}
