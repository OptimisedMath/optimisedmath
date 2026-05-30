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

  if (inputMode === 'radio' && problem?.options) {
    return (
      <div className="flex flex-col items-center gap-4" onKeyDown={handleRadioKeyDown} tabIndex={0}>
        <div className="flex flex-col gap-2.5 w-full">
          {problem.options.map((option, index) => {
            const isSelected = value === option;
            const isCorrectAnswer = option === problem?.correct;

            let optionClasses = 'p-3.5 sm:p-4 text-base sm:text-lg rounded-2xl border-2 transition-all duration-200 ';

            if (showFeedback && feedback) {
              if (isSelected && feedback.correct) {
                optionClasses += 'border-emerald-500 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 ring-2 ring-emerald-500/30 shadow-[0_0_12px_oklch(0.6_0.2_155/0.15)]';
              } else if (isSelected && !feedback.correct) {
                optionClasses += 'border-red-500 bg-red-500/15 text-red-600 dark:text-red-400 ring-2 ring-red-500/30';
              } else if (isCorrectAnswer) {
                optionClasses += 'border-emerald-500 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 ring-2 ring-emerald-500/30';
              } else {
                optionClasses += 'border-border/30 bg-secondary/30 text-muted-foreground opacity-40';
              }
            } else if (isSelected) {
              optionClasses += 'border-primary bg-primary/10 text-primary ring-2 ring-primary/20 shadow-md';
            } else {
              optionClasses += 'border-border/50 bg-secondary/30 dark:bg-white/3 text-foreground hover:border-primary/40 hover:bg-primary/5';
            }

            if (showFeedback) {
              optionClasses += ' cursor-default';
            } else {
              optionClasses += ' cursor-pointer active:scale-[0.98]';
            }

            return (
              <button
                key={index}
                onClick={() => !showFeedback && onChange(option)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !showFeedback) {
                    e.preventDefault();
                    onChange(option);
                    setTimeout(() => onSubmit(), 100);
                  }
                }}
                disabled={showFeedback}
                className={optionClasses}
              >
                <span className="inline-flex items-center gap-2.5">
                  <kbd className="hidden sm:inline-flex items-center justify-center w-6 h-6 text-[10px] rounded-lg bg-secondary/80 dark:bg-white/10 text-muted-foreground font-mono border border-border/50">
                    {index + 1}
                  </kbd>
                  <span className="font-medium">
                    {option.includes('\\') ? <InlineMath math={option} /> : option}
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        {!showFeedback && (
          <div className="flex flex-col items-center gap-2 w-full mt-1">
            <Button
              onClick={onSubmit}
              disabled={value.trim() === '' || disabled}
              className="w-full max-w-xs h-12 gradient-primary hover:opacity-90 disabled:opacity-40 text-white rounded-xl text-base font-semibold transition-all shadow-lg hover:shadow-xl hover:translate-y-[-1px] active:translate-y-0"
            >
              Sprawdź odpowiedź
            </Button>
            {onAutoSolve && (
              <Button
                onClick={onAutoSolve}
                disabled={disabled}
                variant="ghost"
                className="text-xs text-muted-foreground hover:text-foreground"
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
        <div className="px-5 py-3.5 text-lg sm:text-2xl rounded-2xl w-full max-w-xs sm:w-64 text-center bg-secondary/50 dark:bg-white/5 border-2 border-border/30 text-foreground font-medium">
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
          className="h-14 px-5 text-lg sm:text-2xl rounded-2xl w-full max-w-xs sm:w-64 text-center bg-white/50 dark:bg-white/5 border-2 border-border/50 focus-visible:border-primary focus-visible:ring-primary/20 font-medium transition-all"
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
            className="rounded-xl border-border/50 text-foreground hover:bg-secondary px-5 py-3 text-xl font-mono"
          >
            /
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => appendChar(' ')}
            className="rounded-xl border-border/50 text-foreground hover:bg-secondary px-5 py-3 text-base"
          >
            spacja
          </Button>
        </div>
      )}

      {!showFeedback ? (
        <div className="flex flex-col items-center gap-2 w-full mt-1">
          <Button
            type="submit"
            disabled={value.trim() === '' || disabled}
            className="w-full max-w-xs h-12 gradient-primary hover:opacity-90 disabled:opacity-40 text-white rounded-xl text-base font-semibold transition-all shadow-lg hover:shadow-xl hover:translate-y-[-1px] active:translate-y-0"
          >
            Sprawdź odpowiedź
          </Button>
          {onAutoSolve && (
            <Button
              onClick={onAutoSolve}
              disabled={disabled}
              variant="ghost"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              🪄 Auto-Solve
            </Button>
          )}
        </div>
      ) : null}
    </form>
  );
}
