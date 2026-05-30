'use client';

import { useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { InlineMath } from 'react-katex';
import type { Problem, GameState } from '@/lib/types';
import 'katex/dist/katex.min.css';

interface AnswerInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  showFeedback: boolean;
  problem: Problem | null;
  gameState: GameState;
  onAutoSolve?: () => void;
  feedback?: { correct: boolean } | null;
}

export default function AnswerInput({
  value,
  onChange,
  onSubmit,
  disabled,
  showFeedback,
  problem,
  gameState,
  onAutoSolve,
  feedback,
}: AnswerInputProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const handleRadioKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && value.trim() !== '' && !disabled && !showFeedback) {
      e.preventDefault();
      onSubmit();
    }
  };

  const inputMode = problem?.input_mode ?? gameState.current_input_mode;
  const inputRef = useRef<HTMLInputElement>(null);

  const appendChar = (char: string) => {
    onChange(value + char);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  useEffect(() => {
    const handleGlobalNumberKey = (e: KeyboardEvent) => {
      if (inputMode !== 'radio' || !problem?.options || showFeedback) return;
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;
      const num = parseInt(e.key, 10);
      if (num >= 1 && num <= problem.options.length) {
        e.preventDefault();
        onChange(problem.options[num - 1]);
      }
    };
    window.addEventListener('keydown', handleGlobalNumberKey);
    return () => window.removeEventListener('keydown', handleGlobalNumberKey);
  }, [inputMode, problem, showFeedback, onChange]);
  const keyboardType = problem?.keyboard_type || 'default';

  // Convert plain text input to LaTeX for display
  const formatInputAsLatex = (s: string): string => {
    if (!s.trim()) return s;
    const trimmed = s.trim();
    // Handle mixed numbers like "1 3/4" → "1\\frac{3}{4}"
    const mixedMatch = trimmed.match(/^(\d+)\s+(\d+)\/(\d+)$/);
    if (mixedMatch) {
      const [, whole, num, den] = mixedMatch;
      return `${whole}\\frac{${num}}{${den}}`;
    }
    // Handle fractions like "3/4" → "\\frac{3}{4}"
    const fracMatch = trimmed.match(/^(\d+)\/(\d+)$/);
    if (fracMatch) {
      const [, num, den] = fracMatch;
      return `\\frac{${num}}{${den}}`;
    }
    // Return as-is for decimals or whole numbers
    return trimmed;
  };

  // Render radio mode
  if (inputMode === 'radio' && problem?.options) {
    return (
      <div className="flex flex-col items-center gap-4" onKeyDown={handleRadioKeyDown} tabIndex={0}>
        <div className="flex flex-col gap-3 w-full">
          {problem.options.map((option, index) => (
            <button
              key={index}
              onClick={() => !showFeedback && onChange(option)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !showFeedback) {
                  e.preventDefault();
                  onChange(option);
                  // Auto-submit after selection
                  setTimeout(() => onSubmit(), 100);
                }
              }}
              disabled={showFeedback}
              className={`p-3 sm:p-4 text-base sm:text-xl rounded-xl border-2 transition-all shadow-sm ${
                showFeedback && feedback
                  ? value === option && feedback.correct
                    ? 'border-emerald-500 bg-emerald-600/85 text-white ring-2 ring-emerald-300'
                    : value === option && !feedback.correct
                    ? 'border-red-500 bg-red-600/85 text-white ring-2 ring-red-300'
                    : option === problem?.correct
                    ? 'border-emerald-500 bg-emerald-600/85 text-white ring-2 ring-emerald-300'
                    : 'border-slate-200 bg-slate-100 text-slate-500 opacity-40 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300'
                  : value === option
                    ? 'border-sky-500 bg-sky-50 text-sky-700 ring-4 ring-sky-100 dark:bg-sky-500/20 dark:text-sky-200 dark:ring-sky-500/20'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-sky-300 hover:bg-sky-50 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:bg-slate-800'
              } ${showFeedback ? 'cursor-not-allowed' : 'cursor-pointer'}`}
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
          <>
            <Button
              onClick={onSubmit}
              disabled={value.trim() === '' || disabled}
              className="bg-sky-600 hover:bg-sky-500 disabled:bg-slate-400 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white px-5 py-3 sm:px-8 rounded-xl text-base sm:text-xl font-bold transition-all shadow-lg hover:shadow-sky-500/30"
            >
              Sprawdź odpowiedź
            </Button>
            {onAutoSolve && (
              <Button
                onClick={onAutoSolve}
                disabled={disabled}
                variant="outline"
                className="border-slate-300 text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                🪄 Auto-Solve
              </Button>
            )}
          </>
        )}
      </div>
    );
  }

  // Render text mode
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
          onChange={(e) => onChange(e.target.value)}
          placeholder="Wpisz wynik..."
          inputMode={keyboardType === 'decimal' ? 'decimal' : 'numeric'}
          className="px-4 py-3 sm:px-6 sm:py-4 text-lg sm:text-2xl text-slate-950 dark:text-white rounded-xl w-full max-w-xs sm:w-64 text-center bg-white dark:bg-slate-950/70 border-slate-200 dark:border-slate-700 shadow-sm focus:outline-none focus:ring-4 focus:ring-sky-200 dark:focus:ring-sky-500/30"
          autoFocus
          disabled={showFeedback}
          ref={inputRef}
        />
      )}

      {!showFeedback && keyboardType !== 'decimal' && (
        <div className="sm:hidden flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => appendChar('/')}
            className="border-slate-300 text-slate-700 hover:bg-slate-100 px-5 py-3 text-xl font-mono dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            /
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => appendChar(' ')}
            className="border-slate-300 text-slate-700 hover:bg-slate-100 px-5 py-3 text-xl dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            spacja
          </Button>
        </div>
      )}

      {!showFeedback ? (
        <>
          <Button
            type="submit"
            disabled={value.trim() === '' || disabled}
            className="bg-sky-600 hover:bg-sky-500 disabled:bg-slate-400 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white px-5 py-3 sm:px-8 rounded-xl text-base sm:text-xl font-bold transition-all shadow-lg hover:shadow-sky-500/30"
          >
            Sprawdź odpowiedź
          </Button>
          {onAutoSolve && (
            <Button
              onClick={onAutoSolve}
              disabled={disabled}
              variant="outline"
              className="border-slate-300 text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              🪄 Auto-Solve
            </Button>
          )}
        </>
      ) : null}
    </form>
  );
}
