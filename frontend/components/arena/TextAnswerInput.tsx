'use client';

import { memo, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { InlineMath } from 'react-katex';
import { useAutoSolve } from '@/hooks/useAutoSolve';
import type { SessionActions, SessionView } from '@/lib/session';
import SubmitRow from './SubmitRow';
import 'katex/dist/katex.min.css';

interface TextAnswerInputProps {
  view: SessionView;
  actions: SessionActions;
}

function formatInputAsLatex(s: string): string {
  if (!s.trim()) return s;
  const trimmed = s.trim();
  const mixedMatch = trimmed.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixedMatch) {
    const [, whole, num, den] = mixedMatch;
    return `${whole}\\frac{${num}}{${den}}`;
  }
  const fracMatch = trimmed.match(/^(\d+)\/(\d+)$/);
  if (fracMatch) {
    const [, num, den] = fracMatch;
    return `\\frac{${num}}{${den}}`;
  }
  return trimmed;
}

function TextAnswerInput({
  view,
  actions,
}: TextAnswerInputProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const problem = view.problem;
  const answerLocked = view.answerLocked;

  const {
    isAutoSolving,
    showAutoSolve,
    handleAutoSolve,
    autoSolveDisabled,
    interactionDisabled,
    canSubmit,
  } = useAutoSolve({
    view,
    actions,
    inputMode: 'input',
    value,
    setValue,
  });

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    actions.submit(value);
  };

  const appendChar = (char: string) => {
    const input = inputRef.current;
    const start = input?.selectionStart ?? value.length;
    const end = input?.selectionEnd ?? value.length;
    const newValue = value.slice(0, start) + char + value.slice(end);
    const newCursorPos = start + char.length;

    setValue(newValue);

    setTimeout(() => {
      if (!input) return;
      input.focus();
      input.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  const keyboardType = problem?.keyboard_type || 'default';
  const submitDisabled = value.trim() === '' || !canSubmit || interactionDisabled;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
      {answerLocked ? (
        <div className="px-4 py-3 sm:px-6 sm:py-4 text-lg sm:text-2xl text-slate-950 dark:text-white rounded-xl w-full max-w-xs sm:w-64 text-center bg-slate-50 dark:bg-slate-950/70 border-2 border-slate-200 dark:border-slate-700 shadow-inner">
          {value.includes('/') || value.includes(' ') ? (
            <InlineMath math={formatInputAsLatex(value)} />
          ) : (
            value
          )}
        </div>
      ) : (
        <Input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Wpisz wynik..."
          inputMode={keyboardType === 'decimal' ? 'decimal' : 'numeric'}
          className="px-4 py-3 sm:px-6 sm:py-4 text-lg sm:text-2xl text-slate-950 dark:text-white rounded-xl w-full max-w-xs sm:w-64 text-center bg-white dark:bg-slate-950/70 border-slate-200 dark:border-slate-700 shadow-sm focus:outline-none focus:ring-4 focus:ring-sky-200 dark:focus:ring-sky-500/30"
          autoFocus
          ref={inputRef}
        />
      )}

      {!answerLocked && keyboardType !== 'decimal' && (
        <div className="sm:hidden flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => appendChar('/')}
            className="border-slate-300 text-slate-700 hover:bg-slate-100 active:scale-[0.98] px-5 py-3 text-xl font-mono dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            /
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => appendChar(' ')}
            className="border-slate-300 text-slate-700 hover:bg-slate-100 active:scale-[0.98] px-5 py-3 text-xl dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            spacja
          </Button>
        </div>
      )}

      {!answerLocked ? (
        <SubmitRow
          submitType="submit"
          submitDisabled={submitDisabled}
          showAutoSolve={showAutoSolve}
          autoSolveDisabled={autoSolveDisabled}
          onAutoSolve={handleAutoSolve}
        />
      ) : null}
    </form>
  );
}

export default memo(TextAnswerInput);
