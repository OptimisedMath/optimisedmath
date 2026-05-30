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
      <div className="w-full max-w-3xl mb-4 rounded-xl border border-white/70 bg-white/70 p-3 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-900/55">
        <div className="flex justify-between gap-4 text-sm text-slate-600 dark:text-slate-300 mb-2">
          <span className="truncate font-medium">🏆 {selectedMacro}</span>
          <span className="shrink-0 tabular-nums">{completedTopics}/{totalTopics} topics completed</span>
        </div>
        <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-gradient-to-r from-sky-500 to-blue-600 h-2.5 rounded-full transition-all duration-500 shadow-[0_0_18px_rgba(14,165,233,0.45)]"
            style={{ width: `${percentage}%` }}
          />
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
      <div className="w-full max-w-3xl mb-4 rounded-xl border border-white/70 bg-white/70 p-3 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-900/55">
        <div className="flex justify-between gap-4 text-sm text-slate-600 dark:text-slate-300 mb-2">
          <span className="truncate font-medium">📚 {currentTopic?.name || 'Current topic'}</span>
          <span className="shrink-0 tabular-nums">Level {selectedLevel}/{maxLevel}</span>
        </div>
        <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-gradient-to-r from-emerald-500 to-teal-400 h-2.5 rounded-full transition-all duration-500 shadow-[0_0_18px_rgba(16,185,129,0.45)]"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }

  return null;
}
