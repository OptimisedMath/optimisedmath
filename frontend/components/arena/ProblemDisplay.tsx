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
      <div className="py-16 text-xl font-semibold text-slate-500 animate-pulse dark:text-slate-400">
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
    <div className="mb-6 text-slate-700 dark:text-slate-300">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-sky-600 dark:text-sky-300">{selectedMacro}</p>
      <p className="mx-auto mt-1 max-w-xl text-base sm:text-lg font-semibold text-slate-900 dark:text-white">{microTopicName}</p>
      <div className="mt-3 mb-5 inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm text-slate-500 shadow-sm dark:border-slate-700 dark:bg-slate-950/70 dark:text-slate-400">
        📍 {problem.level_display || `Level ${selectedLevel}`}
      </div>
      <h2 className="text-lg sm:text-2xl font-bold mb-3 text-slate-950 dark:text-white">Zadanie</h2>
      <div className="mb-4 sm:mb-8 rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-sky-50/70 p-3 text-lg font-bold shadow-inner sm:p-5 sm:text-2xl dark:border-slate-700 dark:from-slate-950 dark:to-slate-900">
        <BlockMath math={problem.question} />
      </div>
      {problem.image_html && (
        <div className="mb-6 flex justify-center">
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-700 dark:bg-slate-950/60" style={{ width: '100%', maxWidth: '100%' }} dangerouslySetInnerHTML={{ __html: problem.image_html }} />
        </div>
      )}
    </div>
  );
}
