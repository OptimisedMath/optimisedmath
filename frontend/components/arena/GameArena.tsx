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
import { getCurriculum, startSession, navigateSession, getNextProblem, submitAnswer, resetSession, autoSolve } from '@/lib/api';
import type { CurriculumResponse, GameState, Problem, Feedback } from '@/lib/types';

const PREFERRED_MACRO = 'Ułamki Zwykłe';

export default function GameArena() {
  const router = useRouter();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [curriculum, setCurriculum] = useState<CurriculumResponse | null>(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [adminMode, setAdminMode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const isFetchingRef = useRef(false);
  const isAdvancingRef = useRef(false);
  const sessionId = gameState?.session_id;

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
      setProblem(null);
    }

    setError(null);

    try {
      const response = await getNextProblem(currentSessionId);
      setProblem(response.problem);
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

    // Global Enter key handler
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        // Check if we should submit answer
        const submitButton = document.querySelector('button[type="submit"]') as HTMLButtonElement;
        const checkButton = Array.from(document.querySelectorAll('button')).find(btn => 
          btn.textContent?.includes('Sprawdź odpowiedź')
        ) as HTMLButtonElement;
        const nextButton = Array.from(document.querySelectorAll('button')).find(btn => 
          btn.textContent?.includes('Następne zadanie') ||
          btn.textContent?.includes('Następny poziom') ||
          btn.textContent?.includes('Następny temat')
        ) as HTMLButtonElement;

        if (submitButton && !submitButton.disabled) {
          e.preventDefault();
          submitButton.click();
        } else if (checkButton && !checkButton.disabled) {
          e.preventDefault();
          checkButton.click();
        } else if (
          nextButton &&
          document.activeElement !== nextButton &&
          !e.repeat &&
          !isAdvancingRef.current &&
          !isFetchingRef.current
        ) {
          e.preventDefault();
          nextButton.click();
        }
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);

    const initializeGame = async () => {
      const storedUsername = localStorage.getItem('username');
      const storedSessionId = localStorage.getItem('session_id');

      if (!storedUsername || !storedSessionId) {
        router.push('/login');
        return;
      }

      try {
        const curriculumResponse = await getCurriculum();
        if (!isMounted) return;

        const availableMacros = curriculumResponse.macro_topics || [];
        if (availableMacros.length === 0) {
          throw new Error('No curriculum data available');
        }

        const initialMacro = availableMacros.includes(PREFERRED_MACRO)
          ? PREFERRED_MACRO
          : availableMacros[0];

        setCurriculum(curriculumResponse);

        const sessionResponse = await startSession({
          username: storedUsername,
          selected_macro: initialMacro,
        });
        if (!isMounted) return;

        localStorage.setItem('session_id', sessionResponse.session_id);
        setGameState(sessionResponse);
        setError(null);
        fetchNextProblem(sessionResponse.session_id);
      } catch (err) {
        if (!isMounted) return;
        const errorMsg = err instanceof Error ? err.message : 'Failed to start session';
        setError(errorMsg);
        console.error('Error starting session:', err);
      }
    };

    initializeGame();

    return () => {
      isMounted = false;
      window.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, [fetchNextProblem, router]);

  const handleSubmit = async () => {
    console.log('handleSubmit called', { gameState, problem, userAnswer, isSubmitting });
    if (isSubmitting) {
      console.log('Already submitting, ignoring duplicate call');
      return;
    }
    if (!gameState?.session_id || !problem?.problem_id || userAnswer.trim() === '') {
      console.log('handleSubmit validation failed');
      return;
    }

    setIsSubmitting(true);
    const isTextMode = gameState.current_input_mode === 'text';
    console.log('Submitting answer', { session_id: gameState.session_id, problem_id: problem.problem_id, user_input: userAnswer, is_text_mode: isTextMode });

    try {
      const response = await submitAnswer({
        session_id: gameState.session_id,
        problem_id: problem.problem_id,
        user_input: userAnswer,
        is_text_mode: isTextMode,
      });
      console.log('Submit response received', response);

      const oldTopicOrder = gameState.selected_topic_order;
      const oldLevel = gameState.selected_level;
      const newState = response.state;

      setGameState(newState);
      setError(null);

      const topicChanged = newState.selected_topic_order !== oldTopicOrder;
      const levelChanged = newState.selected_level !== oldLevel;
      console.log('State update', { topicChanged, levelChanged, topic_completed: newState.topic_completed });

      const isLocked = newState.problem_answered;
      setFeedback({
        correct: response.is_correct,
        message: response.feedback,
        feedback_type: newState.feedback_type ?? (response.is_correct ? 'success' : 'warning'),
        is_locked: isLocked,
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to submit answer';
      setError(errorMsg);
      console.error('Error submitting answer:', err);
      console.error('Error details:', {
        message: err instanceof Error ? err.message : 'Unknown error',
        stack: err instanceof Error ? err.stack : 'No stack trace',
        gameState,
        problem
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAutoSolve = async () => {
    if (!gameState?.session_id || !problem?.problem_id) return;

    setIsSubmitting(true);
    try {
      const response = await autoSolve(gameState.session_id, problem.problem_id);

      const oldTopicOrder = gameState.selected_topic_order;
      const oldLevel = gameState.selected_level;
      const newState = response.state;

      setGameState(newState);
      setError(null);

      const topicChanged = newState.selected_topic_order !== oldTopicOrder;
      const levelChanged = newState.selected_level !== oldLevel;
      console.log('Auto-solve state update', { topicChanged, levelChanged, topic_completed: newState.topic_completed });

      const isLocked = newState.problem_answered;
      setFeedback({
        correct: response.is_correct,
        message: response.feedback,
        feedback_type: newState.feedback_type ?? (response.is_correct ? 'success' : 'warning'),
        is_locked: isLocked,
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to auto-solve';
      setError(errorMsg);
      console.error('Error auto-solving:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNavigate = useCallback(async (macro: string, topicOrder: number, level: number) => {
    if (!sessionId) {
      return;
    }

    const scrollY = window.scrollY;
    setIsNavigating(true);
    setFeedback(null);
    setUserAnswer('');
    setProblem(null);
    setError(null);

    try {
      const nextState = await navigateSession({
        session_id: sessionId,
        selected_macro: macro,
        selected_topic_order: topicOrder,
        selected_level: level,
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
    if (!gameState || isAdvancingRef.current) return;

    isAdvancingRef.current = true;
    setIsAdvancing(true);

    try {
      if (gameState.topic_completed) {
        const macro = gameState.selected_macro!;
        const nextOrder = gameState.progress[macro]?.unlocked_order;
        if (nextOrder === undefined) return;

        setIsNavigating(true);
        setError(null);

        try {
          const nextState = await navigateSession({
            session_id: gameState.session_id,
            selected_macro: macro,
            selected_topic_order: nextOrder,
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

  const handleReset = async () => {
    if (!gameState?.session_id) {
      return;
    }

    if (!confirm('Czy na pewno chcesz zresetować cały postęp? Ta operacja jest nieodwracalna.')) {
      return;
    }

    setIsNavigating(true);
    setFeedback(null);
    setUserAnswer('');
    setProblem(null);
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
  };

  const handleLogout = () => {
    localStorage.removeItem('username');
    localStorage.removeItem('session_id');
    router.push('/login');
  };

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center gradient-bg-light dark:gradient-bg-dark p-8">
        <div className="max-w-md glass-card-strong rounded-3xl p-8 text-center animate-scale-in">
          <div className="w-14 h-14 rounded-2xl bg-red-500/15 flex items-center justify-center text-3xl mx-auto mb-4 border border-red-500/30">
            ⚠️
          </div>
          <h2 className="text-xl font-bold mb-3 text-foreground">Wystąpił błąd</h2>
          <p className="text-sm text-muted-foreground mb-6">{error}</p>
          <button
            onClick={() => {
              setError(null);
              window.location.reload();
            }}
            className="h-10 px-6 gradient-primary text-white rounded-xl font-semibold text-sm transition-all hover:opacity-90 shadow-lg"
          >
            Spróbuj ponownie
          </button>
        </div>
      </div>
    );
  }

  if (!gameState) {
    return (
      <div className="flex h-screen items-center justify-center gradient-bg-light dark:gradient-bg-dark">
        <div className="flex flex-col items-center gap-4 animate-fade-slide-up">
          <div className="w-12 h-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
          <span className="text-sm text-muted-foreground">Łączenie z serwerem...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-bg-light dark:gradient-bg-dark p-4 sm:p-8 font-sans flex flex-col items-center">
      <XPBar gameState={gameState} onLogout={handleLogout} />

      {curriculum && (
        <TopicToolbar
          curriculum={curriculum}
          gameState={gameState}
          isNavigating={isNavigating}
          onNavigate={handleNavigate}
          onReset={handleReset}
          adminMode={adminMode}
          setAdminMode={setAdminMode}
        />
      )}

      {curriculum && (
        <>
          <ProgressBar gameState={gameState} curriculum={curriculum} type="macro" />
          <ProgressBar gameState={gameState} curriculum={curriculum} type="micro" />
        </>
      )}

      <MasteryScoreboard gameState={gameState} />

      <div className="w-full max-w-2xl glass-card-strong p-5 sm:p-8 rounded-3xl text-center animate-fade-slide-in" style={{ animationDelay: '0.25s' }}>
        <ProblemDisplay
          problem={problem}
          selectedMacro={gameState.selected_macro}
          isLoading={!problem}
          gameState={gameState}
          curriculum={curriculum}
        />

        {problem && (
          <>
            <AnswerInput
              value={userAnswer}
              onChange={setUserAnswer}
              onSubmit={handleSubmit}
              disabled={feedback?.is_locked ?? false}
              showFeedback={feedback?.is_locked ?? false}
              problem={problem}
              gameState={gameState}
              onAutoSolve={handleAutoSolve}
              feedback={feedback}
            />

            {feedback && !feedback.is_locked && (
              <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-base font-semibold text-center">
                {feedback.message}
              </div>
            )}

            {feedback && feedback.is_locked && (
              <FeedbackCard
                feedback={feedback}
                onNextProblem={handleAdvance}
                topicCompleted={gameState.topic_completed}
                gameState={gameState}
                disabled={isAdvancing}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
