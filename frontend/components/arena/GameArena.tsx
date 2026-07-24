'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import XPBar from './XPBar';
import TopicToolbar from './TopicToolbar';
import ProblemDisplay from './ProblemDisplay';
import AnswerInput from './AnswerInput';
import FeedbackCard from './FeedbackCard';
import ProgressBar from './ProgressBar';
import MasteryScoreboard from './MasteryScoreboard';
import { startSession, navigateSession, getNextProblem, submitAnswer, resetSession, autoSolve } from '@/lib/api';
import { scrollElementClearOfMobileChrome } from '@/lib/scroll';
import type { GameState, Feedback, SubmitAnswerHandler, SessionNavigateRequest } from '@/lib/types';

const PREFERRED_MACRO = 'Ułamki Zwykłe';

type NavigateIntent = Pick<
  SessionNavigateRequest,
  'selected_macro' | 'selected_micro_topic_order' | 'selected_level'
>;

export default function GameArena() {
  const router = useRouter();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const isFetchingRef = useRef(false);
  const isAdvancingRef = useRef(false);
  const userAnswerRef = useRef(userAnswer);
  userAnswerRef.current = userAnswer;
  const feedbackRef = useRef<HTMLDivElement>(null);
  const nextButtonRef = useRef<HTMLButtonElement>(null);
  const [needsLogin, setNeedsLogin] = useState(false);
  const sessionId = gameState?.session_id;

  const problem = gameState?.current_problem ?? null;

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
      setUserAnswer('');
      setGameState((prev) =>
        prev ? { ...prev, current_problem: null, can_submit: false, can_advance: false } : prev
      );
    }

    setError(null);

    try {
      const response = await getNextProblem(currentSessionId);
      setGameState(response.state);
      setFeedback(null);
      setUserAnswer('');
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
      const storedUsername = localStorage.getItem('username');
      const storedSessionId = localStorage.getItem('session_id');

      if (!storedUsername || !storedSessionId) {
        setNeedsLogin(true);
        router.push('/login');
        return;
      }

      try {
        const sessionResponse = await startSession({
          username: storedUsername,
          selected_macro: PREFERRED_MACRO,
        });
        if (!isMounted) return;

        localStorage.setItem('session_id', sessionResponse.session_id);
        setGameState(sessionResponse);
        setError(null);
        fetchNextProblem(sessionResponse.session_id);
      } catch (err) {
        if (!isMounted) return;

        try {
          const fallbackSession = await startSession({
            username: storedUsername,
          });
          if (!isMounted) return;

          localStorage.setItem('session_id', fallbackSession.session_id);
          setGameState(fallbackSession);
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
  }, [fetchNextProblem, router]);

  const applySubmissionResponse = useCallback((response: { state: GameState; is_correct: boolean; feedback: string }) => {
    const nextState = response.state;
    setGameState(nextState);
    setError(null);
    setFeedback({
      correct: response.is_correct,
      message: response.feedback,
      feedback_type: nextState.feedback_type ?? (response.is_correct ? 'success' : 'warning'),
      is_locked: nextState.can_advance,
    });
  }, []);

  const handleSubmit = useCallback<SubmitAnswerHandler>(async (answerOverride) => {
    if (isSubmitting || !gameState?.can_submit) {
      return;
    }

    const answer = (answerOverride ?? userAnswerRef.current).trim();
    if (!gameState?.session_id || !problem?.problem_id || answer === '') {
      return;
    }

    if (answerOverride !== undefined) {
      setUserAnswer(answerOverride);
    }

    setIsSubmitting(true);
    const isTextMode = gameState.current_input_mode === 'text';

    try {
      const response = await submitAnswer({
        session_id: gameState.session_id,
        problem_id: problem.problem_id,
        user_input: answer,
        is_text_mode: isTextMode,
      });
      applySubmissionResponse(response);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to submit answer';
      setError(errorMsg);
      console.error('Error submitting answer:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [isSubmitting, gameState, problem, applySubmissionResponse]);

  const handleAutoSolve = useCallback(async () => {
    if (isSubmitting || !gameState?.can_submit || !gameState.admin_mode) {
      return;
    }

    if (!gameState.session_id || !problem?.problem_id) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await autoSolve({
        session_id: gameState.session_id,
        problem_id: problem.problem_id,
      });
      applySubmissionResponse(response);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to auto-solve';
      setError(errorMsg);
      console.error('Error auto-solving:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [isSubmitting, gameState, problem, applySubmissionResponse]);

  const handleNavigate = useCallback(async (intent: NavigateIntent) => {
    if (!sessionId) {
      return;
    }

    const scrollY = window.scrollY;
    setIsNavigating(true);
    setFeedback(null);
    setUserAnswer('');
    setGameState((prev) =>
      prev ? { ...prev, current_problem: null, can_submit: false, can_advance: false } : prev
    );
    setError(null);

    try {
      const nextState = await navigateSession({
        session_id: sessionId,
        ...intent,
      });

      setGameState(nextState);
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

  const handleAdvance = useCallback(async () => {
    if (!gameState || !gameState.can_advance || isAdvancingRef.current) return;

    isAdvancingRef.current = true;
    setIsAdvancing(true);

    try {
      if (gameState.topic_completed) {
        const macro = gameState.selected_macro!;
        const nextOrder = gameState.progress[macro]?.unlocked_micro_topic_order;
        if (nextOrder === undefined) return;

        setIsNavigating(true);
        setError(null);

        try {
          const nextState = await navigateSession({
            session_id: gameState.session_id,
            selected_macro: macro,
            selected_micro_topic_order: nextOrder,
            selected_level: 1,
          });

          await fetchNextProblem(nextState.session_id, { clearBeforeFetch: false });
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to navigate topic';
          setError(errorMsg);
          console.error('Error navigating topic:', err);
        } finally {
          setIsNavigating(false);
        }
      } else {
        await fetchNextProblem(gameState.session_id, { clearBeforeFetch: false });
      }
    } finally {
      isAdvancingRef.current = false;
      setIsAdvancing(false);
    }
  }, [gameState, fetchNextProblem]);

  useEffect(() => {
    if (!feedback) return;

    const frameId = requestAnimationFrame(() => {
      const target = feedback.is_locked ? nextButtonRef.current : feedbackRef.current;
      if (target) {
        scrollElementClearOfMobileChrome(target);
      }
    });

    return () => cancelAnimationFrame(frameId);
  }, [feedback]);

  useEffect(() => {
    const handleAdvanceKey = (e: KeyboardEvent) => {
      if (
        e.key === 'Enter' &&
        gameState?.can_advance &&
        feedback &&
        !e.repeat &&
        !isAdvancingRef.current &&
        !isFetchingRef.current
      ) {
        e.preventDefault();
        void handleAdvance();
      }
    };

    window.addEventListener('keydown', handleAdvanceKey);
    return () => window.removeEventListener('keydown', handleAdvanceKey);
  }, [gameState?.can_advance, feedback, handleAdvance]);

  const handleReset = useCallback(async () => {
    if (!gameState?.session_id) {
      return;
    }

    if (!confirm('Czy na pewno chcesz zresetować cały postęp? Ta operacja jest nieodwracalna.')) {
      return;
    }

    setIsNavigating(true);
    setFeedback(null);
    setUserAnswer('');
    setGameState((prev) =>
      prev ? { ...prev, current_problem: null, can_submit: false, can_advance: false } : prev
    );
    setError(null);

    try {
      const nextState = await resetSession({
        session_id: gameState.session_id,
      });

      setGameState(nextState);
      await fetchNextProblem(nextState.session_id);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to reset progress';
      setError(errorMsg);
      console.error('Error resetting progress:', err);
    } finally {
      setIsNavigating(false);
    }
  }, [gameState?.session_id, fetchNextProblem]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('username');
    localStorage.removeItem('session_id');
    router.push('/login');
  }, [router]);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-white p-8">
        <div className="max-w-md bg-red-100 dark:bg-red-900 border-2 border-red-400 dark:border-red-600 rounded-lg p-6 text-center">
          <h2 className="text-2xl font-bold mb-4 text-red-700 dark:text-red-200">Error</h2>
          <p className="text-lg mb-6">{error}</p>
          <button
            onClick={() => {
              setError(null);
              window.location.reload();
            }}
            className="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded-lg font-bold"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!gameState) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-white">
        {needsLogin ? 'Redirecting to login...' : 'Connecting to Python Brain...'}
      </div>
    );
  }

  const showAdvance = gameState.can_advance && feedback !== null;
  const canSubmit = gameState.can_submit && !isSubmitting;
  const adminMode = gameState.admin_mode ?? false;
  const textModeDisabled = gameState.navigation?.text_mode_disabled ?? false;

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.20),_transparent_34%),radial-gradient(circle_at_top_right,_rgba(245,158,11,0.16),_transparent_28%),linear-gradient(180deg,_#f8fafc_0%,_#eef6ff_48%,_#f8fafc_100%)] p-3 pb-6 text-slate-900 sm:p-6 lg:p-8 dark:bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.18),_transparent_34%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.12),_transparent_28%),linear-gradient(180deg,_#020617_0%,_#0f172a_52%,_#111827_100%)] dark:text-white font-sans flex flex-col items-center">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 border-b border-white/50 bg-white/30 backdrop-blur-3xl dark:border-white/5 dark:bg-white/5" />
      <div className="relative z-10 flex w-full flex-col items-center">
      <XPBar
        xp={gameState.xp}
        flawlessEligible={gameState.flawless_eligible}
        onLogout={handleLogout}
      />

      {gameState.navigation && (
        <TopicToolbar
          gameState={gameState}
          isNavigating={isNavigating}
          onNavigate={handleNavigate}
          onReset={handleReset}
        />
      )}

      {gameState.navigation && (
        <>
          <ProgressBar
            type="macro"
            selectedMacro={gameState.selected_macro}
            macroProgress={gameState.navigation.macro_progress}
          />
          <ProgressBar
            type="micro"
            selectedLevel={gameState.selected_level}
            microProgress={gameState.navigation.micro_progress}
            currentTopicName={gameState.navigation.current_topic_name}
          />
        </>
      )}

      <MasteryScoreboard
        streak={gameState.streak}
        maxStreak={gameState.max_streak}
        problemAnswered={gameState.problem_answered}
        showCelebration={gameState.show_celebration}
      />

      <div className="relative w-full max-w-3xl overflow-hidden rounded-2xl border border-white/70 bg-white/85 p-4 text-center shadow-[0_24px_80px_rgba(15,23,42,0.16)] backdrop-blur-xl sm:p-8 dark:border-white/10 dark:bg-slate-900/78 dark:shadow-[0_24px_90px_rgba(0,0,0,0.35)]">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-sky-400 via-emerald-400 to-amber-300" />
        <ProblemDisplay
          problem={problem}
          selectedMacro={gameState.selected_macro}
          selectedLevel={gameState.selected_level}
          microTopicName={gameState.navigation?.current_topic_name ?? 'Current topic'}
          isLoading={!problem}
        />

        {problem && (
          <>
            <AnswerInput
              value={userAnswer}
              onChange={setUserAnswer}
              onSubmit={handleSubmit}
              disabled={!canSubmit}
              canSubmit={canSubmit}
              showFeedback={showAdvance}
              problem={problem}
              gameState={gameState}
              feedback={feedback}
              textModeDisabled={textModeDisabled}
              onAutoSolve={adminMode ? handleAutoSolve : undefined}
            />

            {feedback && !showAdvance && (
              <div
                ref={feedbackRef}
                className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-700 text-base sm:text-lg font-semibold text-center dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300"
              >
                {feedback.message}
              </div>
            )}

            {feedback && showAdvance && (
              <FeedbackCard
                feedback={feedback}
                onNextProblem={handleAdvance}
                topicCompleted={gameState.topic_completed}
                showCelebration={gameState.show_celebration}
                hasNextTopic={gameState.navigation?.has_next_unlocked_topic ?? false}
                currentInputMode={gameState.current_input_mode}
                disabled={isAdvancing}
                nextButtonRef={nextButtonRef}
                problem={problem}
              />
            )}
          </>
        )}
      </div>
      </div>
    </div>
  );
}
