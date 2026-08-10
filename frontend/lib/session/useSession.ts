'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useAppNavigation } from '@/lib/navigation';
import { MISSING_TOPIC_NAME, PREFERRED_CHAPTER_ID } from './constants';
import {
  getNextProblem,
  navigateSession,
  resetSession,
  startSession,
  submitAnswer,
} from './api';
import {
  getStoredSessionId,
  getStoredUsername,
  setStoredSessionId,
} from './storage';
import type {
  Feedback,
  NavigateIntent,
  SessionActions,
  SessionState,
  SessionView,
  SubmitAnswerHandler,
  SubmissionResponse,
} from './types';

export function useSession() {
  const { exitToLogin, prefetchLogin } = useAppNavigation();
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingNextProblem, setIsLoadingNextProblem] = useState(false);
  const [needsLogin, setNeedsLogin] = useState(false);
  const isFetchingRef = useRef(false);
  const isLoadingNextProblemRef = useRef(false);

  const sessionId = sessionState?.session_id;
  const problem = sessionState?.current_problem ?? null;

  const fetchNextProblem = useCallback(async (
    currentSessionId: string,
    options: { clearBeforeFetch?: boolean } = {}
  ) => {
    if (isFetchingRef.current) return false;
    isFetchingRef.current = true;
    const { clearBeforeFetch = true } = options;
    const scrollY = window.scrollY;

    if (clearBeforeFetch) {
      setFeedback(null);
      setSessionState((prev) =>
        prev ? { ...prev, current_problem: null, can_submit: false, can_next_problem: false } : prev
      );
    }

    setError(null);

    try {
      const response = await getNextProblem(currentSessionId);
      setSessionState(response.state);
      setFeedback(null);
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
  }, []);

  useEffect(() => {
    let isMounted = true;

    const initializeGame = async () => {
      const storedUsername = getStoredUsername();
      const storedSessionId = getStoredSessionId();

      if (!storedUsername || !storedSessionId) {
        setNeedsLogin(true);
        exitToLogin();
        return;
      }

      try {
        const sessionResponse = await startSession({
          username: storedUsername,
          selected_chapter_id: PREFERRED_CHAPTER_ID,
        });
        if (!isMounted) return;

        setStoredSessionId(sessionResponse.session_id);
        setSessionState(sessionResponse);
        setError(null);
        fetchNextProblem(sessionResponse.session_id);
      } catch (err) {
        if (!isMounted) return;

        try {
          const fallbackSession = await startSession({
            username: storedUsername,
          });
          if (!isMounted) return;

          setStoredSessionId(fallbackSession.session_id);
          setSessionState(fallbackSession);
          setError(null);
          fetchNextProblem(fallbackSession.session_id);
          return;
        } catch {
          // Fall through to the original error message.
        }

        const errorMsg = err instanceof Error ? err.message : 'Failed to start session';
        setError(errorMsg);
        console.error('Error starting session:', err);
      }
    };

    initializeGame();

    return () => {
      isMounted = false;
    };
  }, [fetchNextProblem, exitToLogin]);

  useEffect(() => {
    prefetchLogin();
  }, [prefetchLogin]);

  const applySubmissionResponse = useCallback((response: SubmissionResponse) => {
    const nextState = response.state;
    setSessionState(nextState);
    setError(null);
    setFeedback({
      correct: response.is_correct,
      message: response.feedback,
      feedback_type: nextState.feedback_type,
      answer_locked: nextState.can_next_problem,
    });
  }, []);

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
  }, [isSubmitting, sessionState, problem, applySubmissionResponse]);

  const handleNavigate = useCallback(async (intent: NavigateIntent) => {
    if (!sessionId) {
      return;
    }

    const scrollY = window.scrollY;
    setIsNavigating(true);
    setFeedback(null);
    setSessionState((prev) =>
      prev ? { ...prev, current_problem: null, can_submit: false, can_next_problem: false } : prev
    );
    setError(null);

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
  }, [sessionId, fetchNextProblem]);

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
    setFeedback(null);
    setSessionState((prev) =>
      prev ? { ...prev, current_problem: null, can_submit: false, can_next_problem: false } : prev
    );
    setError(null);

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
  }, [sessionState, fetchNextProblem]);

  const clearErrorAndReload = useCallback(() => {
    setError(null);
    window.location.reload();
  }, []);

  const view = useMemo((): SessionView => {
    const session = sessionState;
    const navigation = session?.navigation;
    const selectedChapterName = navigation
      ? navigation.available_chapters.find(
          (chapter) => chapter.chapter_id === session?.selected_chapter_id
        )?.name ?? null
      : null;

    return {
      needsLogin,
      isLoading: session === null && error === null,
      error,
      isNavigating,
      isSubmitting,
      isLoadingNextProblem,
      canSubmit: Boolean(session?.can_submit && !isSubmitting),
      canNextProblem: Boolean(session?.can_next_problem && feedback !== null),
      session,
      problem,
      feedback,
      selectedChapterName,
      topicName: navigation?.current_topic_name || MISSING_TOPIC_NAME,
      adminMode: session?.admin_mode ?? false,
    };
  }, [
    sessionState,
    feedback,
    error,
    isNavigating,
    isSubmitting,
    isLoadingNextProblem,
    needsLogin,
    problem,
  ]);

  const actions = useMemo((): SessionActions => ({
    submit: handleSubmit,
    navigate: handleNavigate,
    nextProblem: handleNextProblem,
    reset: handleReset,
    clearErrorAndReload,
  }), [handleSubmit, handleNavigate, handleNextProblem, handleReset, clearErrorAndReload]);

  return { view, actions };
}
