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

  let buttonLabel = 'Następne zadanie';
  let buttonIcon = '→';
  if (topicCompleted) {
    buttonLabel = 'Następny temat';
    buttonIcon = '🎯';
  } else if (showBalloons) {
    buttonLabel = 'Następny poziom';
    buttonIcon = '🚀';
  }

  return (
    <div className="w-full flex flex-col items-center gap-4 mt-6 animate-fade-slide-up">
      {showBalloons && (
        <div className="text-5xl animate-bounce">
          🎉
        </div>
      )}

      <div
        className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl text-base sm:text-lg font-bold ${
          feedback.correct
            ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
            : 'bg-red-500/15 text-red-600 dark:text-red-400 border border-red-500/30'
        }`}
      >
        <span>{feedback.correct ? '✓' : '✗'}</span>
        {feedback.message}
      </div>

      {topicCompleted && !hasNextTopic ? (
        <div className="text-foreground/70 text-sm sm:text-base text-center px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
          🎊 Gratulacje! Ukończyłeś wszystkie tematy w tym dziale!
        </div>
      ) : (
        <Button
          type="button"
          onClick={onNextProblem}
          disabled={disabled}
          className="h-12 px-6 gradient-primary hover:opacity-90 disabled:opacity-40 text-white rounded-xl text-base font-semibold transition-all shadow-lg hover:shadow-xl hover:translate-y-[-1px] active:translate-y-0"
        >
          {buttonLabel} {buttonIcon}
        </Button>
      )}
    </div>
  );
}
