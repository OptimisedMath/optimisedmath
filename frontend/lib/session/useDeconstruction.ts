'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { useSessionClient } from './SessionClientContext';
import { reportError } from './errors';
import type {
  DeconstructionActions,
  DeconstructionPhase,
  DeconstructionStepResponse,
  DeconstructionView,
  Problem,
  SessionResponse,
} from './types';

const DECONSTRUCTION_PAUSE_MS = 4000;

/** Phases that replace the whole arena; 'idle' and 'pause' leave it on screen. */
export function isTakeoverPhase(phase: DeconstructionPhase): boolean {
  return phase === 'intro' || phase === 'step' || phase === 'handback';
}

/**
 * The Problem the backend is running a Deconstruction over, or null when none is
 * running. Per ADR-0002 the trigger is the backend's own
 * `deconstruction_running` flag — never inferred from the Submission's wire
 * shape, which would tie the takeover to an unrelated spoiler rule in
 * `backend/session.py`'s `public_problem`.
 */
function takeoverArmingProblem(session: SessionResponse | null): Problem | null {
  if (!session?.deconstruction_running) return null;
  return session.current_problem;
}

interface UseDeconstructionOptions {
  sessionState: SessionResponse | null;
  setSessionState: Dispatch<SetStateAction<SessionResponse | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
}

/**
 * Owns the Deconstruction takeover's local phase machine: pause -> intro -> step
 * (looping) -> handback, plus Abandonment via the exit control. Returns the
 * takeover's slice of the render model and its handlers, ready to hang off
 * `SessionView`/`SessionActions`. Internal to lib/session/ — composed by
 * useSession(), which also calls `reset` whenever the Student leaves the
 * triggering Problem behind.
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

  const sessionId = sessionState?.session_id;
  const armingProblem = phase === 'idle' ? takeoverArmingProblem(sessionState) : null;

  useEffect(() => {
    if (!armingProblem) return;
    // Arms the takeover once, in response to a Submission response newly
    // arriving from the backend, not a plain prop-to-state mirror.
    /* eslint-disable react-hooks/set-state-in-effect */
    setTriggerProblem(armingProblem);
    setPhase('pause');
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [armingProblem]);

  // Leaving 'pause' — by tap, by Abandonment, or by unmount — runs this
  // cleanup, so the timer needs no cancelling anywhere else.
  useEffect(() => {
    if (phase !== 'pause') return undefined;
    const timeout = setTimeout(() => setPhase('intro'), DECONSTRUCTION_PAUSE_MS);
    return () => clearTimeout(timeout);
  }, [phase]);

  const endPause = useCallback(() => {
    if (phase !== 'pause') return;
    setPhase('intro');
  }, [phase]);

  const fetchStep = useCallback(async () => {
    if (!sessionId) return;
    setIsLoadingStep(true);
    try {
      const response = await client.getDeconstructionStep(sessionId);
      setStep(response);
    } catch (err) {
      reportError(
        setError,
        err,
        'Failed to load Deconstruction step',
        'Error loading Deconstruction step:'
      );
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
          // The submit response carries no reveal flag — the backend flips the
          // Reveal on the threshold-th wrong answer and says so only in the next
          // step payload, so a wrong answer has to re-read the step too.
          await fetchStep();
        }
      } catch (err) {
        reportError(
          setError,
          err,
          'Failed to submit Deconstruction step',
          'Error submitting Deconstruction step:'
        );
      } finally {
        setIsSubmittingStep(false);
      }
    },
    [client, sessionId, isSubmittingStep, fetchStep, setError]
  );

  const reset = useCallback(() => {
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
    // The backend already ended the Deconstruction when it served the handback
    // question; clearing the flag locally keeps the now-stale SessionResponse
    // from re-arming the takeover the moment `reset()` returns to 'idle'.
    setSessionState((prev) =>
      prev
        ? {
            ...prev,
            deconstruction_running: false,
            can_submit: true,
            can_next_problem: false,
            feedback_type: null,
            feedback_msg: '',
          }
        : prev
    );
    reset();
  }, [setSessionState, reset]);

  const view = useMemo(
    (): DeconstructionView => ({
      phase,
      misconceptionName: step?.misconception_name ?? null,
      headerQuestion: triggerProblem?.question ?? null,
      step: step
        ? {
            question: step.question,
            workingLine: step.working_line,
            stepIndex: step.step_index,
            totalSteps: step.total_steps,
            revealedAnswer: step.revealed_answer,
            inputType: step.input_type,
            items: step.items,
          }
        : null,
      stepFeedback,
      handbackQuestion,
      isLoadingStep,
      isSubmittingStep,
    }),
    [
      phase,
      triggerProblem,
      step,
      stepFeedback,
      handbackQuestion,
      isLoadingStep,
      isSubmittingStep,
    ]
  );

  const actions = useMemo(
    (): DeconstructionActions => ({ endPause, begin, submitStep, exit, returnToProblem }),
    [endPause, begin, submitStep, exit, returnToProblem]
  );

  return { view, actions, reset };
}
