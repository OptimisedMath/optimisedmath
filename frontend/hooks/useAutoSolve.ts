import { useCallback, useRef, useState } from 'react';
import type { SessionActions, SessionView } from '@/lib/session';

const AUTO_SOLVE_RADIO_DELAY_MS = 450;
const AUTO_SOLVE_INPUT_CHAR_DELAY_MS = 45;
const AUTO_SOLVE_INPUT_SUBMIT_DELAY_MS = 300;

const sleep = (ms: number) => new Promise<void>((resolve) => {
  setTimeout(resolve, ms);
});

type AutoSolveInputMode = 'radio' | 'input';

interface UseAutoSolveOptions {
  view: SessionView;
  actions: SessionActions;
  inputMode: AutoSolveInputMode;
  value: string;
  setValue: (value: string) => void;
}

export function useAutoSolve({
  view,
  actions,
  inputMode,
  value,
  setValue,
}: UseAutoSolveOptions) {
  const [isAutoSolving, setIsAutoSolving] = useState(false);
  const autoSolveRunRef = useRef(0);

  const problem = view.problem;
  const canSubmit = view.canSubmit;
  const answerLocked = view.feedbackPhase === 'answer_locked';
  const disabled = !canSubmit;
  const showAutoSolve = view.adminMode;

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
    setValue('');

    try {
      if (inputMode === 'radio') {
        setValue(correctAnswer);
        await sleep(AUTO_SOLVE_RADIO_DELAY_MS);
      } else {
        for (let index = 0; index < correctAnswer.length; index += 1) {
          if (autoSolveRunRef.current !== runId) {
            return;
          }
          setValue(correctAnswer.slice(0, index + 1));
          await sleep(AUTO_SOLVE_INPUT_CHAR_DELAY_MS);
        }
        await sleep(AUTO_SOLVE_INPUT_SUBMIT_DELAY_MS);
      }

      if (autoSolveRunRef.current !== runId) {
        return;
      }

      await actions.submit(correctAnswer);
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
    actions,
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
