'use client';

import { useEffect } from 'react';
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && value.trim() !== '' && !disabled) {
      onSubmit();
    }
  };

  const handleRadioKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && value.trim() !== '' && !disabled && !showFeedback) {
      e.preventDefault();
      onSubmit();
    }
  };

  const inputMode = problem?.input_mode ?? gameState.current_input_mode;

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
              className={`p-3 sm:p-4 text-base sm:text-xl rounded-lg border-2 transition-all ${
                showFeedback && feedback
                  ? value === option && feedback.correct
                    ? 'border-green-500 bg-green-600/50 text-white ring-2 ring-green-400'
                    : value === option && !feedback.correct
                    ? 'border-red-500 bg-red-600/50 text-white ring-2 ring-red-400'
                    : option === problem?.correct
                    ? 'border-green-500 bg-green-600/50 text-white ring-2 ring-green-400'
                    : 'border-slate-600 bg-slate-700 text-slate-300 opacity-30'
                  : value === option
                    ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                    : 'border-slate-600 bg-slate-700 text-slate-300 hover:border-slate-500'
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
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-4 py-2 sm:px-8 sm:py-3 rounded-lg text-base sm:text-xl font-bold transition-all shadow-lg hover:shadow-blue-500/50"
            >
              Sprawdź odpowiedź
            </Button>
            {onAutoSolve && (
              <Button
                onClick={onAutoSolve}
                disabled={disabled}
                variant="outline"
                className="border-slate-500 text-slate-300 hover:bg-slate-700"
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
        <div className="px-4 py-3 sm:px-6 sm:py-4 text-lg sm:text-2xl text-white rounded-lg w-full max-w-xs sm:w-64 text-center bg-slate-700 border-2 border-slate-600">
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
          onKeyDown={handleKeyDown}
          placeholder="Wpisz wynik..."
          inputMode={keyboardType === 'decimal' ? 'decimal' : 'text'}
          className="px-4 py-3 sm:px-6 sm:py-4 text-lg sm:text-2xl text-white rounded-lg w-full max-w-xs sm:w-64 text-center focus:outline-none focus:ring-4 focus:ring-blue-500"
          autoFocus
          disabled={showFeedback}
        />
      )}

      {!showFeedback ? (
        <>
          <Button
            type="submit"
            disabled={value.trim() === '' || disabled}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-4 py-2 sm:px-8 sm:py-3 rounded-lg text-base sm:text-xl font-bold transition-all shadow-lg hover:shadow-blue-500/50"
          >
            Sprawdź odpowiedź
          </Button>
          {onAutoSolve && (
            <Button
              onClick={onAutoSolve}
              disabled={disabled}
              variant="outline"
              className="border-slate-500 text-slate-300 hover:bg-slate-700"
            >
              🪄 Auto-Solve
            </Button>
          )}
        </>
      ) : null}
    </form>
  );
}
