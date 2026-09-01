import { useCallback, useRef, useState } from 'react';
import type { Problem, SubmitAnswerHandler } from '@/lib/session';

type AutoSolveInputMode = 'radio' | 'input';

interface UseAutoSolveOptions {
  problem: Problem | null;
  canSubmit: boolean;
  answerLocked: boolean;
  adminMode: boolean;
  onSubmit: SubmitAnswerHandler;
  inputMode: AutoSolveInputMode;
  value: string;
  setValue: (value: string) => void;
}

export function useAutoSolve({
  problem,
  canSubmit,
  answerLocked,
  adminMode,
  onSubmit,
  inputMode,
  value,
  setValue,
}: UseAutoSolveOptions) {
  const [isAutoSolving, setIsAutoSolving] = useState(false);
  const autoSolveRunRef = useRef(0);

  const disabled = !canSubmit;
  const showAutoSolve = adminMode;

  const interactionDisabled = disabled || isAutoSolving;
  const autoSolveDisabled =
    interactionDisabled || !problem?.correct_answer || !canSubmit;

  const handleAutoSolve = useCallback(async () => {
    const correctAnswer = problem?.correct_answer;
    if (
      !showAutoSolve ||
      !correctAnswer ||
      isAutoSolving ||
      answerLocked ||
      !canSubmit ||
      disabled
    ) {
      return;
    }

    const runId = autoSolveRunRef.current + 1;
    autoSolveRunRef.current = runId;
    setIsAutoSolving(true);
    setValue(correctAnswer);

    try {
      await onSubmit(correctAnswer);
    } finally {
      if (autoSolveRunRef.current === runId) {
        setIsAutoSolving(false);
      }
    }
  }, [
    problem?.correct_answer,
    showAutoSolve,
    isAutoSolving,
    answerLocked,
    canSubmit,
    disabled,
    inputMode,
    onSubmit,
    setValue,
  ]);

  return {
    isAutoSolving,
    showAutoSolve,
    handleAutoSolve,
    autoSolveDisabled,
    interactionDisabled,
    answerLocked,
    canSubmit,
    disabled,
  };
}
