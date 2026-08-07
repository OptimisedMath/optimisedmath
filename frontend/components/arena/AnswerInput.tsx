'use client';

import { memo, useCallback, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Check } from 'lucide-react';
import { InlineMath } from 'react-katex';
import { useDocumentKeydown } from '@/hooks/useDocumentKeydown';
import type { Problem, SubmitAnswerHandler } from '@/lib/session';
import 'katex/dist/katex.min.css';

interface AnswerInputProps {
  onSubmit: SubmitAnswerHandler;
  disabled: boolean;
  showFeedback: boolean;
  canSubmit: boolean;
  problem: Problem | null;
  currentInputMode: string;
  feedback?: { correct: boolean } | null;
  radioOnly?: boolean;
  onAutoSolve?: () => void;
}

function AnswerInput({
  onSubmit,
  disabled,
  showFeedback,
  canSubmit,
  problem,
  currentInputMode,
  feedback,
  radioOnly = false,
  onAutoSolve,
}: AnswerInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(value);
  };

  const rawInputMode = problem?.input_mode ?? currentInputMode;
  const inputMode =
    radioOnly || rawInputMode === 'radio' ? 'radio' : rawInputMode;
  const inputRef = useRef<HTMLInputElement>(null);

  const handleRadioShortcuts = useCallback(
    (e: KeyboardEvent) => {
      if (
        inputMode !== 'radio' ||
        !problem?.answer_options ||
        showFeedback ||
        !canSubmit ||
        disabled
      ) {
        return;
      }

      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return;
      }

      if (e.key === 'Enter' && value.trim() !== '' && !e.repeat) {
        e.preventDefault();
        onSubmit(value);
        return;
      }

      const num = parseInt(e.key, 10);
      if (num >= 1 && num <= problem.answer_options.length) {
        e.preventDefault();
        setValue(problem.answer_options[num - 1]);
      }
    },
    [inputMode, problem, showFeedback, canSubmit, disabled, value, onSubmit]
  );

  useDocumentKeydown(handleRadioShortcuts, [handleRadioShortcuts]);

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
  const submitDisabled = value.trim() === '' || !canSubmit || disabled;

  const formatInputAsLatex = (s: string): string => {
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
  };

  if (inputMode === 'radio' && problem?.answer_options) {
    return (
      <div className="flex flex-col items-center gap-4">
        <div className="flex flex-col gap-3 w-full">
          {problem.answer_options.map((option, index) => (
            <button
              key={index}
              onClick={() => setValue(option)}
              disabled={showFeedback}
              className={`p-3 sm:p-4 text-base sm:text-xl rounded-xl border-2 transition-all shadow-sm active:scale-[0.98] ${
                showFeedback && feedback
                  ? value === option && feedback.correct
                    ? 'border-emerald-500 bg-emerald-600/85 text-white ring-2 ring-emerald-300'
                    : value === option && !feedback.correct
                    ? 'border-red-500 bg-red-600/85 text-white ring-2 ring-red-300'
                    : !feedback.correct && problem.correct_answer === option
                    ? 'border-emerald-500 bg-emerald-600/85 text-white ring-2 ring-emerald-300'
                    : 'border-slate-200 bg-slate-100 text-slate-500 opacity-40 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300'
                  : value === option
                    ? 'border-sky-500 bg-sky-50 text-sky-700 ring-4 ring-sky-100 hover:-translate-y-0.5 dark:bg-sky-500/20 dark:text-sky-200 dark:ring-sky-500/20'
                    : 'border-slate-200 bg-white text-slate-700 hover:-translate-y-0.5 hover:border-sky-300 hover:bg-sky-50 hover:shadow-md dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:bg-slate-800'
              } ${showFeedback ? '' : 'cursor-pointer'}`}
            >
              <span className="inline-flex items-center gap-2">
                <kbd className="hidden sm:inline-block text-xs px-1.5 py-0.5 rounded bg-slate-600/50 text-slate-400 font-mono border border-slate-500/50">
                  {index + 1}
                </kbd>
                {option.includes('\\') ? <InlineMath math={option} /> : option}
              </span>
            </button>
          ))}
        </div>

        {!showFeedback && (
            <div className="flex flex-wrap items-center justify-center gap-3">
            <Button
              onClick={() => onSubmit(value)}
              disabled={submitDisabled}
              className="bg-sky-600 hover:bg-sky-500 disabled:bg-slate-400 dark:disabled:bg-slate-700 disabled:cursor-not-allowed disabled:hover:translate-y-0 text-white px-5 py-3 sm:px-8 rounded-xl text-base sm:text-xl font-bold transition-all shadow-lg hover:-translate-y-0.5 hover:shadow-sky-500/30 active:translate-y-0 active:scale-[0.98]"
            >
              <Check className="mr-2 h-5 w-5" aria-hidden="true" />
              Sprawdź odpowiedź
            </Button>
            {onAutoSolve && (
              <Button
                onClick={onAutoSolve}
                disabled={disabled}
                variant="outline"
                className="border-slate-300 text-slate-700 hover:bg-slate-100 hover:-translate-y-0.5 active:scale-[0.98] dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                🪄 Auto-Solve
              </Button>
            )}
            </div>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
      {showFeedback ? (
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

      {!showFeedback && keyboardType !== 'decimal' && (
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

      {!showFeedback ? (
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button
            type="submit"
            disabled={submitDisabled}
            className="bg-sky-600 hover:bg-sky-500 disabled:bg-slate-400 dark:disabled:bg-slate-700 disabled:cursor-not-allowed disabled:hover:translate-y-0 text-white px-5 py-3 sm:px-8 rounded-xl text-base sm:text-xl font-bold transition-all shadow-lg hover:-translate-y-0.5 hover:shadow-sky-500/30 active:translate-y-0 active:scale-[0.98]"
          >
            <Check className="mr-2 h-5 w-5" aria-hidden="true" />
            Sprawdź odpowiedź
          </Button>
          {onAutoSolve && (
            <Button
              type="button"
              onClick={onAutoSolve}
              disabled={disabled}
              variant="outline"
              className="border-slate-300 text-slate-700 hover:bg-slate-100 hover:-translate-y-0.5 active:scale-[0.98] dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              🪄 Auto-Solve
            </Button>
          )}
        </div>
      ) : null}
    </form>
  );
}

export default memo(AnswerInput);
