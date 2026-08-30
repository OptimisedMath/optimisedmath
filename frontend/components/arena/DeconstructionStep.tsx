'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import { BlockMath, InlineMath } from 'react-katex';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { DeconstructionStepView } from '@/lib/session';
import DeconstructionExitControl from './DeconstructionExitControl';
import DeconstructionOrderingInput from './DeconstructionOrderingInput';
import 'katex/dist/katex.min.css';

interface DeconstructionStepProps {
  headerQuestion: string | null;
  step: DeconstructionStepView;
  feedback: string | null;
  isSubmitting: boolean;
  onSubmit: (answer: string) => Promise<void>;
  onExit: () => void;
}

/** Done / current / still to come, in the dot row that paces the walkthrough. */
function progressDotClass(dotIndex: number, stepIndex: number): string {
  if (dotIndex < stepIndex) return 'w-2 bg-emerald-400';
  if (dotIndex === stepIndex) return 'w-8 bg-sky-400';
  return 'w-2 bg-white/20';
}

/**
 * One Deconstruction step, alone — no scrolling thread of past steps. The
 * working line above it is the sole pacing device: each state replaces the
 * last, and is entirely absent (not padded) for a step that authors none.
 */
export default function DeconstructionStep({
  headerQuestion,
  step,
  feedback,
  isSubmitting,
  onSubmit,
  onExit,
}: DeconstructionStepProps) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed === '') return;
    onSubmit(trimmed);
    setValue('');
  };

  return (
    <div className="flex w-full flex-col">
      <header className="mb-3 flex items-center justify-between gap-3 border-b border-white/10 pb-3">
        <span className="text-xs font-bold uppercase tracking-[0.2em] text-sky-300">
          Rozkładamy zadanie
        </span>
        {headerQuestion && (
          <span data-deconstruction-question className="truncate text-sm text-slate-500">
            <InlineMath math={headerQuestion} />
          </span>
        )}
      </header>

      {/* Keyed by its text so a changed working line remounts and replays the flash. */}
      {step.workingLine !== null && (
        <div
          key={step.workingLine}
          data-deconstruction-working-line
          className="animate-working-line-flash rounded-2xl border p-5 text-center text-2xl text-emerald-100 sm:text-3xl"
        >
          <BlockMath math={step.workingLine} />
        </div>
      )}

      <div className="mt-4 flex justify-center gap-2">
        {Array.from({ length: step.totalSteps }).map((_, dotIndex) => (
          <span
            key={dotIndex}
            data-deconstruction-dot
            className={`h-2 rounded-full transition-all ${progressDotClass(dotIndex, step.stepIndex)}`}
          />
        ))}
      </div>

      {/* Keyed by step so each question card remounts and replays its entrance. */}
      <div
        key={step.stepIndex}
        className="animate-fade-slide-up mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8"
      >
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
          krok {step.stepIndex + 1} z {step.totalSteps}
        </p>
        <h2 className="mb-4 text-lg font-bold text-white sm:text-xl">{step.question}</h2>

        {step.revealedAnswer !== null && (
          <div className="mb-4 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-emerald-200">
            Odpowiedź: <span className="font-bold">{step.revealedAnswer}</span> — wpisz ją, aby
            przejść dalej.
          </div>
        )}

        {step.inputType === 'ordering' && step.items ? (
          <DeconstructionOrderingInput
            items={step.items}
            disabled={isSubmitting}
            onSubmit={onSubmit}
          />
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-wrap items-center gap-3">
            <Input
              autoFocus
              value={value}
              onChange={(e) => setValue(e.target.value)}
              disabled={isSubmitting}
              className="w-40 border-white/15 bg-black/40 text-lg font-bold text-white placeholder:text-slate-500 focus-visible:ring-sky-500/40"
              placeholder="?"
            />
            <Button type="submit" size="lg" disabled={isSubmitting || value.trim() === ''}>
              Sprawdź
            </Button>
          </form>
        )}

        {feedback && <p className="mt-4 text-sm font-semibold text-amber-300">{feedback}</p>}
      </div>

      <div className="mt-6 flex justify-center">
        <DeconstructionExitControl onExit={onExit} disabled={isSubmitting} />
      </div>
    </div>
  );
}
