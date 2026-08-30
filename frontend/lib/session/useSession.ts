'use client';

import { useCallback, useMemo, useState } from 'react';
import { MISSING_TOPIC_NAME } from './constants';
import {
  emptySessionDisplayProjection,
  projectSessionState,
} from './projectSessionState';
import { useSessionBootstrap } from './useSessionBootstrap';
import { useProblemLifecycle } from './useProblemLifecycle';
import { useDeconstruction } from './useDeconstruction';
import type {
  DeconstructionView,
  Feedback,
  FeedbackPhase,
  SessionActions,
  SessionResponse,
  SessionView,
} from './types';

export function useSession() {
  const [sessionState, setSessionState] = useState<SessionResponse | null>(null);
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

  const deconstruction = useDeconstruction({ sessionState, setSessionState, setError });
  const { reset: resetDeconstruction } = deconstruction;

  const navigate = useCallback(
    async (intent: Parameters<typeof handleNavigate>[0]) => {
      resetDeconstruction();
      await handleNavigate(intent);
    },
    [handleNavigate, resetDeconstruction]
  );

  const resetProgress = useCallback(async () => {
    resetDeconstruction();
    await handleReset();
  }, [handleReset, resetDeconstruction]);

  const clearErrorAndReload = useCallback(() => {
    setError(null);
    window.location.reload();
  }, []);

  const deconstructionView = useMemo((): DeconstructionView => {
    const step = deconstruction.step;
    return {
      phase: deconstruction.phase,
      misconceptionName: step?.misconception_name ?? null,
      headerQuestion: deconstruction.triggerProblem?.question ?? null,
      step: step
        ? {
            question: step.question,
            workingLine: step.working_line,
            stepIndex: step.step_index,
            totalSteps: step.total_steps,
            revealedAnswer: step.revealed_answer,
          }
        : null,
      stepFeedback: deconstruction.stepFeedback,
      handbackQuestion: deconstruction.handbackQuestion,
      isLoadingStep: deconstruction.isLoadingStep,
      isSubmittingStep: deconstruction.isSubmittingStep,
    };
  }, [
    deconstruction.phase,
    deconstruction.triggerProblem,
    deconstruction.step,
    deconstruction.stepFeedback,
    deconstruction.handbackQuestion,
    deconstruction.isLoadingStep,
    deconstruction.isSubmittingStep,
  ]);

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
      deconstruction: deconstructionView,
    };
  }, [
    sessionState,
    error,
    isNavigating,
    isSubmitting,
    isLoadingNextProblem,
    needsLogin,
    problem,
    deconstructionView,
  ]);

  const deconstructionActions = useMemo(
    () => ({
      endPause: deconstruction.endPause,
      begin: deconstruction.begin,
      submitStep: deconstruction.submitStep,
      exit: deconstruction.exit,
      returnToProblem: deconstruction.returnToProblem,
    }),
    [
      deconstruction.endPause,
      deconstruction.begin,
      deconstruction.submitStep,
      deconstruction.exit,
      deconstruction.returnToProblem,
    ]
  );

  const actions = useMemo((): SessionActions => ({
    submit: handleSubmit,
    navigate,
    nextProblem: handleNextProblem,
    reset: resetProgress,
    clearErrorAndReload,
    deconstruction: deconstructionActions,
  }), [
    handleSubmit,
    navigate,
    handleNextProblem,
    resetProgress,
    clearErrorAndReload,
    deconstructionActions,
  ]);

  return { view, actions };
}
