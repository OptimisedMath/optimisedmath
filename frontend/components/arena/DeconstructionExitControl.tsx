'use client';

interface DeconstructionExitControlProps {
  onExit: () => void;
  disabled?: boolean;
}

/** Visually recessive by design — leaving is possible, never the obvious action. */
export default function DeconstructionExitControl({
  onExit,
  disabled,
}: DeconstructionExitControlProps) {
  return (
    <button
      type="button"
      onClick={onExit}
      disabled={disabled}
      className="text-xs font-medium text-slate-500 opacity-60 transition hover:text-slate-300 hover:opacity-100 hover:underline disabled:opacity-30"
    >
      Zrezygnuj i wróć do zadania
    </button>
  );
}
