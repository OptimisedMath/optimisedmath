'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import XPBar from './XPBar';
import TopicToolbar from './TopicToolbar';
import ProblemDisplay from './ProblemDisplay';
import AnswerInput from './AnswerInput';
import FeedbackCard from './FeedbackCard';
import ProgressBar from './ProgressBar';
import MasteryScoreboard from './MasteryScoreboard';
import { getCurriculum, startSession, navigateSession, getNextProblem, submitAnswer, resetSession } from '@/lib/api';
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

  const fetchNextProblem = useCallback(async (currentSessionId: string) => {
    setFeedback(null);
    setUserAnswer('');
    setError(null);

    try {
      const response = await getNextProblem(currentSessionId);
      setProblem(response.problem);
      setGameState(response.state);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch problem';
      setError(errorMsg);
      console.error('Error fetching problem:', err);
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
        } else if (nextButton) {
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

      setFeedback({
        correct: response.is_correct,
        message: response.feedback,
      });
      setUserAnswer('');
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
    if (!problem?.correct) {
      return;
    }

    setUserAnswer(problem.correct);
    await handleSubmit();
  };

  const handleNavigate = async (macro: string, topicOrder: number, level: number) => {
    if (!gameState?.session_id) {
      return;
    }

    setIsNavigating(true);
    setFeedback(null);
    setUserAnswer('');
    setProblem(null);
    setError(null);

    try {
      const nextState = await navigateSession({
        session_id: gameState.session_id,
        selected_macro: macro,
        selected_topic_order: topicOrder,
        selected_level: level,
      });

      setGameState(nextState);
      await fetchNextProblem(nextState.session_id);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to navigate topic';
      setError(errorMsg);
      console.error('Error navigating topic:', err);
    } finally {
      setIsNavigating(false);
    }
  };

  const handleAdvance = useCallback(() => {
    if (!gameState) return;
    if (gameState.topic_completed) {
      const macro = gameState.selected_macro!;
      const nextOrder = gameState.progress[macro]?.unlocked_order;
      if (nextOrder === undefined) return;
      handleNavigate(macro, nextOrder, 1);
    } else {
      fetchNextProblem(gameState.session_id);
    }
  }, [gameState, handleNavigate, fetchNextProblem]);

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
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white p-8">
        <div className="max-w-md bg-red-900 border-2 border-red-600 rounded-lg p-6 text-center">
          <h2 className="text-2xl font-bold mb-4 text-red-200">Error</h2>
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
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white">
        Connecting to Python Brain...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8 font-sans flex flex-col items-center relative">
      <XPBar gameState={gameState} />
      <button
        onClick={handleLogout}
        className="absolute top-4 right-4 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg font-medium transition-colors border border-slate-600"
      >
        Wyloguj
      </button>

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

      <div className="w-full max-w-2xl bg-slate-800 p-8 rounded-2xl shadow-2xl border border-slate-700 text-center">
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
              disabled={feedback !== null}
              showFeedback={feedback !== null}
              problem={problem}
              gameState={gameState}
              onAutoSolve={handleAutoSolve}
            />

            {feedback && (
              <FeedbackCard
                feedback={feedback}
                onNextProblem={handleAdvance}
                topicCompleted={gameState.topic_completed}
                gameState={gameState}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
