'use client';

import { Button } from '@/components/ui/button';
import { Check } from 'lucide-react';

interface SubmitRowProps {
  onSubmit?: () => void;
  submitType?: 'button' | 'submit';
  submitDisabled: boolean;
  showAutoSolve: boolean;
  autoSolveDisabled: boolean;
  onAutoSolve: () => void;
}

export default function SubmitRow({
  onSubmit,
  submitType = 'button',
  submitDisabled,
  showAutoSolve,
  autoSolveDisabled,
  onAutoSolve,
}: SubmitRowProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3">
      <Button
        type={submitType}
        onClick={onSubmit}
        disabled={submitDisabled}
        className="bg-sky-600 hover:bg-sky-500 disabled:bg-slate-400 dark:disabled:bg-slate-700 disabled:cursor-not-allowed disabled:hover:translate-y-0 text-white px-5 py-3 sm:px-8 rounded-xl text-base sm:text-xl font-bold transition-all shadow-lg hover:-translate-y-0.5 hover:shadow-sky-500/30 active:translate-y-0 active:scale-[0.98]"
      >
        <Check className="mr-2 h-5 w-5" aria-hidden="true" />
        Sprawdź odpowiedź
      </Button>
      {showAutoSolve && (
        <Button
          type="button"
          onClick={onAutoSolve}
          disabled={autoSolveDisabled}
          variant="outline"
          className="border-slate-300 text-slate-700 hover:bg-slate-100 hover:-translate-y-0.5 active:scale-[0.98] dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          🪄 Auto-Solve
        </Button>
      )}
    </div>
  );
}
