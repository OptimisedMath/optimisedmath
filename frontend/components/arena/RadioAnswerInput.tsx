'use client';

import { memo, useCallback, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Check } from 'lucide-react';
import { InlineMath } from 'react-katex';
import { useDocumentKeydown } from '@/hooks/useDocumentKeydown';
import { useAutoSolve } from '@/hooks/useAutoSolve';
import { getRevealedCorrectAnswer } from '@/lib/session';
import type { SessionActions, SessionView } from '@/lib/session';
import 'katex/dist/katex.min.css';

interface RadioAnswerInputProps {
  view: SessionView;
  actions: SessionActions;
  answerLocked: boolean;
}

function RadioAnswerInput({
  view,
  actions,
  answerLocked,
}: RadioAnswerInputProps) {
  const [value, setValue] = useState('');

  const problem = view.problem!;
  const feedback = view.feedback;

  const {
    isAutoSolving,
    showAutoSolve,
    handleAutoSolve,
    autoSolveDisabled,
    interactionDisabled,
    canSubmit,
    disabled,
  } = useAutoSolve({
    view,
    actions,
    inputMode: 'radio',
    value,
    setValue,
  });

  const submitDisabled = value.trim() === '' || !canSubmit || interactionDisabled;
  const revealedCorrectAnswer = getRevealedCorrectAnswer(problem, feedback);

  const handleRadioShortcuts = useCallback(
    (e: KeyboardEvent) => {
      if (
        !problem.answer_options ||
        answerLocked ||
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
        actions.submit(value);
        return;
      }

      const num = parseInt(e.key, 10);
      if (num >= 1 && num <= problem.answer_options.length) {
        e.preventDefault();
        setValue(problem.answer_options[num - 1]);
      }
    },
    [problem, answerLocked, canSubmit, disabled, value, actions]
  );

  useDocumentKeydown(handleRadioShortcuts, [handleRadioShortcuts]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="flex flex-col gap-3 w-full">
        {problem.answer_options!.map((option, index) => (
          <button
            key={index}
            onClick={() => setValue(option)}
            disabled={answerLocked || isAutoSolving}
            className={`p-3 sm:p-4 text-base sm:text-xl rounded-xl border-2 transition-all shadow-sm active:scale-[0.98] ${
              answerLocked && feedback
                ? value === option && feedback.correct
                  ? 'border-emerald-500 bg-emerald-600/85 text-white ring-2 ring-emerald-300'
                  : value === option && !feedback.correct
                  ? 'border-red-500 bg-red-600/85 text-white ring-2 ring-red-300'
                  : revealedCorrectAnswer === option
                  ? 'border-emerald-500 bg-emerald-600/85 text-white ring-2 ring-emerald-300'
                  : 'border-slate-200 bg-slate-100 text-slate-500 opacity-40 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300'
                : value === option
                  ? 'border-sky-500 bg-sky-50 text-sky-700 ring-4 ring-sky-100 hover:-translate-y-0.5 dark:bg-sky-500/20 dark:text-sky-200 dark:ring-sky-500/20'
                  : 'border-slate-200 bg-white text-slate-700 hover:-translate-y-0.5 hover:border-sky-300 hover:bg-sky-50 hover:shadow-md dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:bg-slate-800'
            } ${answerLocked ? '' : 'cursor-pointer'}`}
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

      {!answerLocked && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button
            onClick={() => actions.submit(value)}
            disabled={submitDisabled}
            className="bg-sky-600 hover:bg-sky-500 disabled:bg-slate-400 dark:disabled:bg-slate-700 disabled:cursor-not-allowed disabled:hover:translate-y-0 text-white px-5 py-3 sm:px-8 rounded-xl text-base sm:text-xl font-bold transition-all shadow-lg hover:-translate-y-0.5 hover:shadow-sky-500/30 active:translate-y-0 active:scale-[0.98]"
          >
            <Check className="mr-2 h-5 w-5" aria-hidden="true" />
            Sprawdź odpowiedź
          </Button>
          {showAutoSolve && (
            <Button
              onClick={handleAutoSolve}
              disabled={autoSolveDisabled}
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

export default memo(RadioAnswerInput);
