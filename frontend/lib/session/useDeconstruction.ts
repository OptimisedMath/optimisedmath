'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { useSessionClient } from './SessionClientContext';
import { reportError } from './errors';
import type { DeconstructionPhase, DeconstructionStepResponse, Problem, SessionResponse } from './types';

const DECONSTRUCTION_PAUSE_MS = 4000;

interface UseDeconstructionOptions {
  sessionState: SessionResponse | null;
  setSessionState: Dispatch<SetStateAction<SessionResponse | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
}

/**
 * Owns the Deconstruction takeover's local phase machine: pause -> intro -> step
 * (looping) -> handback, plus Abandonment via the exit control. `SessionResponse`
 * has no field naming a running Deconstruction (see `docs/session.md`) — the
 * trigger is derived purely from the triggering Submission's own wire shape: a
 * wrong, locked answer whose Problem is missing `correct_answer` (withheld by
 * the backend only while a Deconstruction is running). Internal to lib/session/
 * — composed by useSession().
 */
export function useDeconstruction({
  sessionState,
  setSessionState,
  setError,
}: UseDeconstructionOptions) {
  const client = useSessionClient();
  const [phase, setPhase] = useState<DeconstructionPhase>('idle');
  const [triggerProblem, setTriggerProblem] = useState<Problem | null>(null);
  const [step, setStep] = useState<DeconstructionStepResponse | null>(null);
  const [stepFeedback, setStepFeedback] = useState<string | null>(null);
  const [handbackQuestion, setHandbackQuestion] = useState<string | null>(null);
  const [isLoadingStep, setIsLoadingStep] = useState(false);
  const [isSubmittingStep, setIsSubmittingStep] = useState(false);
  const pauseTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const sessionId = sessionState?.session_id;
  const problem = sessionState?.current_problem ?? null;

  const isTriggeringSubmission =
    phase === 'idle' &&
    !!sessionState &&
    sessionState.can_next_problem &&
    sessionState.feedback_type !== null &&
    sessionState.feedback_type !== 'success' &&
    !!problem &&
    problem.correct_answer === undefined;

  useEffect(() => {
    if (!isTriggeringSubmission || !problem) return;
    // Arms the takeover once, in response to a Submission response newly
    // arriving from the backend, not a plain prop-to-state mirror.
    /* eslint-disable react-hooks/set-state-in-effect */
    setTriggerProblem(problem);
    setPhase('pause');
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [isTriggeringSubmission, problem]);

  useEffect(() => {
    if (phase !== 'pause') return undefined;
    pauseTimeoutRef.current = setTimeout(() => setPhase('intro'), DECONSTRUCTION_PAUSE_MS);
    return () => {
      if (pauseTimeoutRef.current) clearTimeout(pauseTimeoutRef.current);
    };
  }, [phase]);

  const endPause = useCallback(() => {
    if (phase !== 'pause') return;
    if (pauseTimeoutRef.current) clearTimeout(pauseTimeoutRef.current);
    setPhase('intro');
  }, [phase]);

  const fetchStep = useCallback(async () => {
    if (!sessionId) return;
    setIsLoadingStep(true);
    try {
      const response = await client.getDeconstructionStep(sessionId);
      setStep(response);
    } catch (err) {
      reportError(setError, err, 'Failed to load Deconstruction step', 'Error loading Deconstruction step:');
    } finally {
      setIsLoadingStep(false);
    }
  }, [client, sessionId, setError]);

  useEffect(() => {
    if (phase !== 'intro') return;
    if (step !== null || isLoadingStep) return;
    // Fetching the step on entering 'intro' is the canonical fetch-in-effect
    // pattern; setIsLoadingStep(true) inside fetchStep runs before its await.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchStep();
  }, [phase, step, isLoadingStep, fetchStep]);

  const begin = useCallback(() => {
    if (phase !== 'intro' || !step) return;
    setPhase('step');
  }, [phase, step]);

  const submitStep = useCallback(
    async (answer: string) => {
      if (!sessionId || isSubmittingStep) return;
      const trimmed = answer.trim();
      if (trimmed === '') return;

      setIsSubmittingStep(true);
      try {
        const response = await client.submitDeconstructionStep({
          session_id: sessionId,
          user_input: trimmed,
        });

        if (response.handback_question) {
          setStep(null);
          setStepFeedback(null);
          setHandbackQuestion(response.handback_question);
          setPhase('handback');
        } else if (response.is_correct) {
          setStepFeedback(null);
          await fetchStep();
        } else {
          setStepFeedback(response.feedback_msg);
        }
      } catch (err) {
        reportError(setError, err, 'Failed to submit Deconstruction step', 'Error submitting Deconstruction step:');
      } finally {
        setIsSubmittingStep(false);
      }
    },
    [client, sessionId, isSubmittingStep, fetchStep, setError]
  );

  const reset = useCallback(() => {
    if (pauseTimeoutRef.current) clearTimeout(pauseTimeoutRef.current);
    setPhase('idle');
    setTriggerProblem(null);
    setStep(null);
    setStepFeedback(null);
    setHandbackQuestion(null);
  }, []);

  const exit = useCallback(async () => {
    if (!sessionId) return;
    try {
      const response = await client.abandonDeconstruction({ session_id: sessionId });
      setSessionState(response);
      reset();
    } catch (err) {
      reportError(setError, err, 'Failed to end the Deconstruction', 'Error ending Deconstruction:');
    }
  }, [client, sessionId, setSessionState, reset, setError]);

  const returnToProblem = useCallback(() => {
    setSessionState((prev) =>
      prev
        ? {
            ...prev,
            can_submit: true,
            can_next_problem: false,
            feedback_type: null,
            feedback_msg: '',
          }
        : prev
    );
    reset();
  }, [setSessionState, reset]);

  return {
    phase,
    triggerProblem,
    step,
    stepFeedback,
    handbackQuestion,
    isLoadingStep,
    isSubmittingStep,
    endPause,
    begin,
    submitStep,
    exit,
    returnToProblem,
    reset,
  };
}
