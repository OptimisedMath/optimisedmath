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
      <div className="w-full mb-4">
        <div className="flex justify-between text-sm text-slate-300 mb-1">
          <span>🏆 {selectedMacro}</span>
          <span>{completedTopics}/{totalTopics} topics completed</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
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
      <div className="w-full mb-4">
        <div className="flex justify-between text-sm text-slate-300 mb-1">
          <span>📚 {currentTopic?.name || 'Current topic'}</span>
          <span>Level {selectedLevel}/{maxLevel}</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }

  return null;
}
