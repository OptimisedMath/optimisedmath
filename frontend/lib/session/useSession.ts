'use client';

import { useCallback, useMemo, useState } from 'react';
import { MISSING_TOPIC_NAME } from './constants';
import {
  emptySessionDisplayProjection,
  projectSessionState,
} from './projectSessionState';
import { useSessionBootstrap } from './useSessionBootstrap';
import { useProblemLifecycle } from './useProblemLifecycle';
import type {
  Feedback,
  FeedbackPhase,
  SessionActions,
  SessionState,
  SessionView,
} from './types';

export function useSession() {
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const problem = sessionState?.current_problem ?? null;

  const {
    isNavigating,
    isSubmitting,
    isLoadingNextProblem,
    fetchNextProblem,
    handleSubmit,
    handleNavigate,
    handleNextProblem,
    handleReset,
  } = useProblemLifecycle({ sessionState, setSessionState, setError, problem });

  const { needsLogin } = useSessionBootstrap({
    setSessionState,
    setError,
    onSessionStarted: fetchNextProblem,
  });

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

    const feedback: Feedback | null =
      session && session.feedback_type !== null
        ? {
            correct: session.feedback_type === 'success',
            message: session.feedback_msg,
            feedback_type: session.feedback_type,
          }
        : null;

    const feedbackPhase: FeedbackPhase =
      session && session.feedback_type !== null
        ? session.can_next_problem
          ? 'answer_locked'
          : 'soft_error'
        : 'none';

    const answerLocked = feedbackPhase === 'answer_locked';

    const display = session
      ? projectSessionState(session)
      : emptySessionDisplayProjection();

    return {
      needsLogin,
      isLoading: session === null && error === null,
      error,
      isNavigating,
      isSubmitting,
      isLoadingNextProblem,
      canSubmit: Boolean(session?.can_submit && !isSubmitting),
      feedbackPhase,
      answerLocked,
      isLoadingProblem: session !== null && problem === null,
      problem,
      feedback,
      selectedChapterName,
      topicName: navigation?.current_topic_name || MISSING_TOPIC_NAME,
      adminMode: session?.admin_mode ?? false,
      ...display,
    };
  }, [
    sessionState,
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
