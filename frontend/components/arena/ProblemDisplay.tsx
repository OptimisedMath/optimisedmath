import { BlockMath } from 'react-katex';
import type { Problem, GameState, CurriculumResponse } from '@/lib/types';
import 'katex/dist/katex.min.css';

interface ProblemDisplayProps {
  problem: Problem | null;
  selectedMacro: string | null;
  isLoading?: boolean;
  gameState: GameState;
  curriculum: CurriculumResponse | null;
}

export default function ProblemDisplay({ problem, selectedMacro, isLoading, gameState, curriculum }: ProblemDisplayProps) {
  if (isLoading) {
    return (
      <div className="text-2xl text-slate-400 animate-pulse">
        Loading problem...
      </div>
    );
  }

  if (!problem) {
    return null;
  }

  const selectedTopicOrder = gameState.selected_topic_order;
  const selectedLevel = gameState.selected_level;

  let microTopicName = 'Current topic';
  if (selectedMacro && selectedTopicOrder && curriculum) {
    const topics = curriculum.topics[selectedMacro] || [];
    const currentTopic = topics.find((topic) => topic.order === selectedTopicOrder);
    microTopicName = currentTopic?.name || 'Current topic';
  }

  return (
    <div className="mb-6 text-slate-300">
      <p className="text-sm uppercase tracking-wide">{selectedMacro}</p>
      <p className="text-base sm:text-lg font-medium mb-2">{microTopicName}</p>
      <div className="text-sm text-slate-400 mb-4">
        📍 {problem.level_display || `Level ${selectedLevel}`}
      </div>
      <h2 className="text-xl sm:text-3xl font-medium mb-4">Zadanie:</h2>
      <div className="text-lg sm:text-2xl font-bold mb-4 sm:mb-8 p-3 sm:p-4 bg-slate-700 rounded-lg">
        <BlockMath math={problem.question} />
      </div>
      {problem.image_html && (
        <div className="mb-6 flex justify-center">
          <div style={{ width: '100%', maxWidth: '100%' }} dangerouslySetInnerHTML={{ __html: problem.image_html }} />
        </div>
      )}
    </div>
  );
}
