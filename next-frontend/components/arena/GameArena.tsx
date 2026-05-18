'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import XPBar from './XPBar';
import ProblemDisplay from './ProblemDisplay';
import AnswerInput from './AnswerInput';
import FeedbackCard from './FeedbackCard';
import { getCurriculum, startSession, getNextProblem, submitAnswer } from '@/lib/api';
import type { GameState, Problem, Feedback } from '@/lib/types';

const DEFAULT_USERNAME = 'Player1';
const PREFERRED_MACRO = 'Ułamki Zwykłe';

export default function GameArena() {
  const router = useRouter();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedMacro, setSelectedMacro] = useState<string | null>(null);

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

    const initializeGame = async () => {
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

        setSelectedMacro(initialMacro);

        const sessionResponse = await startSession({
          username: DEFAULT_USERNAME,
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
    };
  }, [fetchNextProblem]);

  const handleSubmit = async () => {
    if (!gameState?.session_id || !problem?.problem_id || userAnswer.trim() === '') {
      return;
    }

    try {
      const response = await submitAnswer({
        session_id: gameState.session_id,
        problem_id: problem.problem_id,
        user_input: userAnswer,
        is_text_mode: true,
      });
      setGameState(response.state);
      setFeedback({
        correct: response.is_correct,
        message: response.feedback,
      });
      setError(null);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to submit answer';
      setError(errorMsg);
      console.error('Error submitting answer:', err);
    }
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
    <div className="min-h-screen bg-slate-900 text-white p-8 font-sans flex flex-col items-center">
      <XPBar gameState={gameState} />

      <div className="w-full max-w-2xl bg-slate-800 p-8 rounded-2xl shadow-2xl border border-slate-700 text-center">
        <ProblemDisplay 
          problem={problem} 
          selectedMacro={selectedMacro} 
          isLoading={!problem} 
        />

        {problem && (
          <>
            <AnswerInput
              value={userAnswer}
              onChange={setUserAnswer}
              onSubmit={handleSubmit}
              disabled={feedback !== null}
              showFeedback={feedback !== null}
            />

            {feedback && (
              <FeedbackCard
                feedback={feedback}
                onNextProblem={() => fetchNextProblem(gameState.session_id)}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
