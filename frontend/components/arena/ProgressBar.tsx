import type { GameState, CurriculumResponse } from '@/lib/types';

interface ProgressBarProps {
  gameState: GameState;
  curriculum: CurriculumResponse;
  type: 'macro' | 'micro';
}

export default function ProgressBar({ gameState, curriculum, type }: ProgressBarProps) {
  const selectedMacro = gameState.selected_macro;
  const selectedTopicOrder = gameState.selected_topic_order;
  const selectedLevel = gameState.selected_level;

  if (type === 'macro' && selectedMacro) {
    const topics = curriculum.topics[selectedMacro] || [];
    const progress = gameState.progress[selectedMacro];
    const unlockedOrder = progress?.unlocked_order ?? 1;
    const completedTopics = topics.filter((topic) => topic.order < unlockedOrder).length;
    const totalTopics = topics.length;
    const percentage = totalTopics > 0 ? (completedTopics / totalTopics) * 100 : 0;

    return (
      <div className="w-full max-w-2xl mb-3 animate-fade-slide-in" style={{ animationDelay: '0.1s' }}>
        <div className="flex justify-between text-xs text-muted-foreground mb-1.5 font-medium">
          <span className="flex items-center gap-1.5">
            <span className="w-5 h-5 rounded-md gradient-primary flex items-center justify-center text-[10px] text-white">🏆</span>
            {selectedMacro}
          </span>
          <span className="tabular-nums">{completedTopics}/{totalTopics} tematów</span>
        </div>
        <div className="w-full bg-secondary/80 dark:bg-white/5 rounded-full h-2.5 overflow-hidden border border-border/30">
          <div
            className="h-full rounded-full transition-all duration-500 ease-out relative gradient-primary"
            style={{ width: `${percentage}%` }}
          >
            {percentage > 5 && <div className="absolute inset-0 shimmer-bar rounded-full" />}
          </div>
        </div>
      </div>
    );
  }

  if (type === 'micro' && selectedMacro && selectedTopicOrder) {
    const topics = curriculum.topics[selectedMacro] || [];
    const currentTopic = topics.find((topic) => topic.order === selectedTopicOrder);
    const maxLevel = currentTopic?.max_level || 1;
    const completedLevels = selectedLevel - 1;
    const percentage = maxLevel > 0 ? (completedLevels / maxLevel) * 100 : 0;

    return (
      <div className="w-full max-w-2xl mb-3 animate-fade-slide-in" style={{ animationDelay: '0.15s' }}>
        <div className="flex justify-between text-xs text-muted-foreground mb-1.5 font-medium">
          <span className="flex items-center gap-1.5">
            <span className="w-5 h-5 rounded-md gradient-success flex items-center justify-center text-[10px] text-white">📚</span>
            {currentTopic?.name || 'Temat'}
          </span>
          <span className="tabular-nums">Poziom {selectedLevel}/{maxLevel}</span>
        </div>
        <div className="w-full bg-secondary/80 dark:bg-white/5 rounded-full h-2.5 overflow-hidden border border-border/30">
          <div
            className="h-full rounded-full transition-all duration-500 ease-out relative gradient-success"
            style={{ width: `${percentage}%` }}
          >
            {percentage > 5 && <div className="absolute inset-0 shimmer-bar rounded-full" />}
          </div>
        </div>
      </div>
    );
  }

  return null;
}
