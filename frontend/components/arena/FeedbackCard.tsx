import { Button } from '@/components/ui/button';
import type { Feedback, GameState } from '@/lib/types';

interface FeedbackCardProps {
  feedback: Feedback | null;
  onNextProblem: () => void;
  topicCompleted?: boolean;
  gameState: GameState;
  disabled?: boolean;
}

export default function FeedbackCard({ feedback, onNextProblem, topicCompleted, gameState, disabled = false }: FeedbackCardProps) {
  if (!feedback) {
    return null;
  }

  const showBalloons = gameState.show_celebration;

  const macro = gameState.selected_macro;
  const unlockedOrder = macro ? gameState.progress[macro]?.unlocked_order : undefined;
  const hasNextTopic = unlockedOrder !== undefined &&
    gameState.selected_topic_order !== null &&
    unlockedOrder > (gameState.selected_topic_order ?? 0);

  let buttonLabel = 'Następne zadanie ➡️';
  if (topicCompleted) {
    buttonLabel = 'Następny temat ➡️';
  } else if (showBalloons) {
    buttonLabel = 'Następny poziom ➡️';
  }

  return (
    <div className="w-full flex flex-col items-center gap-4 mt-4 animate-[fadeSlideIn_0.3s_ease-out]">
      {showBalloons && (
        <div className="text-6xl animate-bounce">
          🎉
        </div>
      )}
      <div className={`text-lg sm:text-2xl font-bold ${feedback.correct ? 'text-green-400' : 'text-red-400'}`}>
        {feedback.message}
      </div>
      {topicCompleted && !hasNextTopic ? (
        <div className="text-slate-300 text-base sm:text-lg text-center">
          🎊 Gratulacje! Ukończyłeś wszystkie tematy w tym dziale!
        </div>
      ) : (
        <Button
          type="button"
          onClick={onNextProblem}
          disabled={disabled}
          className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 sm:px-8 sm:py-3 rounded-lg text-base sm:text-xl font-bold transition-all"
        >
          {buttonLabel}
        </Button>
      )}
    </div>
  );
}
