'use client';

import { useCallback, useRef, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import {
  getNextProblem,
  navigateSession,
  resetSession,
  submitAnswer,
} from './api';
import type {
  NavigateIntent,
  Problem,
  SessionState,
  SubmitAnswerHandler,
  SubmissionResponse,
} from './types';

/**
 * Clears the optimistic-fetch slice of SessionState (current problem,
 * submit/next-problem gates, and Feedback fields) plus any stale error, in
 * one place. Called by every action that optimistically clears the board
 * before a network round-trip completes.
 */
function clearOptimisticState(
  setSessionState: Dispatch<SetStateAction<SessionState | null>>,
  setError: Dispatch<SetStateAction<string | null>>
) {
  setSessionState((prev) =>
    prev
      ? {
          ...prev,
          current_problem: null,
          can_submit: false,
          can_next_problem: false,
          feedback_type: null,
          feedback_msg: '',
        }
      : prev
  );
  setError(null);
}

interface UseProblemLifecycleOptions {
  sessionState: SessionState | null;
  setSessionState: Dispatch<SetStateAction<SessionState | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
  problem: Problem | null;
}

/**
 * Owns fetching/submitting/navigating/resetting problems for an active
 * session, including the shared optimistic-clear-and-scroll-preserve
 * behavior. Internal to lib/session/ — composed by useSession().
 */
export function useProblemLifecycle({
  sessionState,
  setSessionState,
  setError,
  problem,
}: UseProblemLifecycleOptions) {
  const [isNavigating, setIsNavigating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingNextProblem, setIsLoadingNextProblem] = useState(false);
  const isFetchingRef = useRef(false);
  const isLoadingNextProblemRef = useRef(false);

  const sessionId = sessionState?.session_id;

  const fetchNextProblem = useCallback(async (
    currentSessionId: string,
    options: { clearBeforeFetch?: boolean } = {}
  ) => {
    if (isFetchingRef.current) return false;
    isFetchingRef.current = true;
    const { clearBeforeFetch = true } = options;
    const scrollY = window.scrollY;

    if (clearBeforeFetch) {
      clearOptimisticState(setSessionState, setError);
    } else {
      setError(null);
    }

    try {
      const response = await getNextProblem(currentSessionId);
      setSessionState(response.state);
      requestAnimationFrame(() => window.scrollTo(0, scrollY));
      return true;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch problem';
      setError(errorMsg);
      console.error('Error fetching problem:', err);
      return false;
    } finally {
      isFetchingRef.current = false;
    }
  }, [setSessionState, setError]);

  const applySubmissionResponse = useCallback((response: SubmissionResponse) => {
    setSessionState(response.state);
    setError(null);
  }, [setSessionState, setError]);

  const handleSubmit = useCallback<SubmitAnswerHandler>(async (answer) => {
    if (isSubmitting || !sessionState?.can_submit) {
      return;
    }

    const trimmed = answer.trim();
    if (!sessionState?.session_id || !problem?.problem_id || trimmed === '') {
      return;
    }

    setIsSubmitting(true);
    const isInputMode = sessionState.current_input_mode === 'input';

    try {
      const response = await submitAnswer({
        session_id: sessionState.session_id,
        problem_id: problem.problem_id,
        user_input: trimmed,
        is_input_mode: isInputMode,
      });
      applySubmissionResponse(response);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to submit answer';
      setError(errorMsg);
      console.error('Error submitting answer:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [isSubmitting, sessionState, problem, applySubmissionResponse, setError]);

  const handleNavigate = useCallback(async (intent: NavigateIntent) => {
    if (!sessionId) {
      return;
    }

    const scrollY = window.scrollY;
    setIsNavigating(true);
    clearOptimisticState(setSessionState, setError);

    try {
      const nextState = await navigateSession({
        session_id: sessionId,
        ...intent,
      });

      setSessionState(nextState);
      await fetchNextProblem(nextState.session_id);
      requestAnimationFrame(() => window.scrollTo(0, scrollY));
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to navigate topic';
      setError(errorMsg);
      console.error('Error navigating topic:', err);
    } finally {
      setIsNavigating(false);
    }
  }, [sessionId, fetchNextProblem, setSessionState, setError]);

  const handleNextProblem = useCallback(async () => {
    if (!sessionState || !sessionState.can_next_problem || isLoadingNextProblemRef.current) return;

    isLoadingNextProblemRef.current = true;
    setIsLoadingNextProblem(true);

    try {
      await fetchNextProblem(sessionState.session_id, { clearBeforeFetch: false });
    } finally {
      isLoadingNextProblemRef.current = false;
      setIsLoadingNextProblem(false);
    }
  }, [sessionState, fetchNextProblem]);

  const handleReset = useCallback(async () => {
    if (!sessionState?.session_id) {
      return;
    }

    if (!confirm('Czy na pewno chcesz zresetować cały postęp? Ta operacja jest nieodwracalna.')) {
      return;
    }

    setIsNavigating(true);
    clearOptimisticState(setSessionState, setError);

    try {
      const nextState = await resetSession({
        session_id: sessionState.session_id,
      });

      setSessionState(nextState);
      await fetchNextProblem(nextState.session_id);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to reset progress';
      setError(errorMsg);
      console.error('Error resetting progress:', err);
    } finally {
      setIsNavigating(false);
    }
  }, [sessionState, fetchNextProblem, setSessionState, setError]);

  return {
    isNavigating,
    isSubmitting,
    isLoadingNextProblem,
    fetchNextProblem,
    handleSubmit,
    handleNavigate,
    handleNextProblem,
    handleReset,
  };
}
