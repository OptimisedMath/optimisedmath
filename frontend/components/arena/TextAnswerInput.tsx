'use client';

import { memo, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { InlineMath } from 'react-katex';
import { useAutoSolve } from '@/hooks/useAutoSolve';
import type { Problem, SubmitAnswerHandler } from '@/lib/session';
import SubmitRow from './SubmitRow';
import 'katex/dist/katex.min.css';

interface TextAnswerInputProps {
  problem: Problem;
  answerLocked: boolean;
  canSubmit: boolean;
  adminMode: boolean;
  onSubmit: SubmitAnswerHandler;
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

// `text` is Geometria's: `numeric` puts `c` and `m` out of reach on a phone,
// and there the Unit is part of the answer.
const INPUT_MODES: Record<string, 'decimal' | 'numeric' | 'text'> = {
  decimal: 'decimal',
  text: 'text',
};

type TapKey = { char: string; label?: string };

const TAP_KEYS: Record<string, TapKey[]> = {
  default: [
    { char: '/' },
    { char: ' ', label: 'spacja' },
  ],
};

// `x²` reads as an exponent at phone size; the bare `²` glyph alone reads as a `2`
// (#292). Whether it appears at all is a Level decision, not a keyboard-type one —
// see `problem.exponent_key`.
const EXPONENT_KEY: TapKey = { char: '²', label: 'x²' };

function TextAnswerInput({
  problem,
  answerLocked,
  canSubmit,
  adminMode,
  onSubmit,
}: TextAnswerInputProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    isAutoSolving,
    showAutoSolve,
    handleAutoSolve,
    autoSolveDisabled,
    interactionDisabled,
  } = useAutoSolve({
    problem,
    canSubmit,
    answerLocked,
    adminMode,
    onSubmit,
    inputMode: 'typing',
    value,
    setValue,
  });

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(value);
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
  // A `text` keyboard answer carries a Unit (`126 mm²`), never a fraction, so its
  // space must not route the echo through KaTeX, which would eat the space and
  // italicise the Unit.
  const echoAsMath =
    keyboardType !== 'text' && (value.includes('/') || value.includes(' '));
  const keyboardTapKeys = TAP_KEYS[keyboardType] ?? [];
  const tapKeys = problem?.exponent_key
    ? [...keyboardTapKeys, EXPONENT_KEY]
    : keyboardTapKeys;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
      {answerLocked ? (
        <div className="px-4 py-3 sm:px-6 sm:py-4 text-lg sm:text-2xl text-slate-950 dark:text-white rounded-xl w-full max-w-xs sm:w-64 text-center bg-slate-50 dark:bg-slate-950/70 border-2 border-slate-200 dark:border-slate-700 shadow-inner">
          {echoAsMath ? (
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
          inputMode={INPUT_MODES[keyboardType] ?? 'numeric'}
          className="px-4 py-3 sm:px-6 sm:py-4 text-lg sm:text-2xl text-slate-950 dark:text-white rounded-xl w-full max-w-xs sm:w-64 text-center bg-white dark:bg-slate-950/70 border-slate-200 dark:border-slate-700 shadow-sm focus:outline-none focus:ring-4 focus:ring-sky-200 dark:focus:ring-sky-500/30"
          autoFocus
          ref={inputRef}
        />
      )}

      {!answerLocked && tapKeys.length > 0 && (
        <div className="sm:hidden flex gap-3">
          {tapKeys.map(({ char, label }) => (
            <Button
              key={char}
              type="button"
              variant="outline"
              onClick={() => appendChar(char)}
              className="border-slate-300 text-slate-700 hover:bg-slate-100 active:scale-[0.98] min-h-12 min-w-12 px-5 py-3 text-xl font-mono dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {label ?? char}
            </Button>
          ))}
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
