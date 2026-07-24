import { type RefObject } from 'react';
import { Button } from '@/components/ui/button';
import { InlineMath } from 'react-katex';
import type { Feedback, GameState, Problem } from '@/lib/types';
import 'katex/dist/katex.min.css';

interface FeedbackCardProps {
  feedback: Feedback | null;
  onNextProblem: () => void;
  topicCompleted?: boolean;
  gameState: GameState;
  disabled?: boolean;
  nextButtonRef?: RefObject<HTMLButtonElement | null>;
  problem?: Problem | null;
}

export default function FeedbackCard({ feedback, onNextProblem, topicCompleted, gameState, disabled = false, nextButtonRef, problem }: FeedbackCardProps) {
  if (!feedback) {
    return null;
  }

  const showBalloons = gameState.show_celebration;

  const hasNextTopic = gameState.navigation?.has_next_unlocked_topic ?? false;

  const inputMode = problem?.input_mode ?? gameState.current_input_mode;
  const correctAnswer =
    !feedback.correct && inputMode !== 'radio' ? problem?.correct_answer : undefined;

  let buttonLabel = 'Następne zadanie ➡️';
  if (topicCompleted) {
    buttonLabel = 'Następny temat ➡️';
  } else if (showBalloons) {
    buttonLabel = 'Następny poziom ➡️';
  }

  return (
    <div className="w-full flex flex-col items-center gap-4 mt-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 animate-[fadeSlideIn_0.3s_ease-out] dark:border-slate-700 dark:bg-slate-950/50">
      {showBalloons && (
        <div className="text-5xl sm:text-6xl animate-bounce drop-shadow">
          🎉
        </div>
      )}
      <div className={`text-lg sm:text-2xl font-bold ${feedback.correct ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
        {feedback.message}
      </div>
      {correctAnswer && (
        <div className="flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-emerald-50 px-4 py-2 text-base sm:text-lg font-semibold text-emerald-700 dark:border-emerald-400/40 dark:bg-emerald-400/10 dark:text-emerald-300">
          <span>Poprawna odpowiedź:</span>
          <span className="font-bold">
            {correctAnswer.includes('\\') ? (
              <InlineMath math={correctAnswer} />
            ) : (
              correctAnswer
            )}
          </span>
        </div>
      )}
      {topicCompleted && !hasNextTopic ? (
        <div className="text-slate-600 dark:text-slate-300 text-base sm:text-lg text-center">
          🎊 Gratulacje! Ukończyłeś wszystkie tematy w tym dziale!
        </div>
      ) : (
        <Button
          ref={nextButtonRef}
          type="button"
          onClick={onNextProblem}
          disabled={disabled}
          className="bg-slate-900 hover:bg-slate-800 text-white px-5 py-3 sm:px-8 rounded-xl text-base sm:text-xl font-bold transition-all shadow-lg hover:shadow-slate-900/20 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100"
        >
          {buttonLabel}
        </Button>
      )}
    </div>
  );
}
