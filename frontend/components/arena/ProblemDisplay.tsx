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
      <div className="flex flex-col items-center gap-3 py-8">
        <div className="w-10 h-10 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
        <span className="text-sm text-muted-foreground">Ładowanie zadania...</span>
      </div>
    );
  }

  if (!problem) {
    return null;
  }

  const selectedTopicOrder = gameState.selected_topic_order;
  const selectedLevel = gameState.selected_level;

  let microTopicName = 'Aktualny temat';
  if (selectedMacro && selectedTopicOrder && curriculum) {
    const topics = curriculum.topics[selectedMacro] || [];
    const currentTopic = topics.find((topic) => topic.order === selectedTopicOrder);
    microTopicName = currentTopic?.name || 'Aktualny temat';
  }

  return (
    <div className="mb-6 text-left">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-medium text-primary uppercase tracking-wider">{selectedMacro}</span>
      </div>
      <p className="text-sm sm:text-base font-medium text-foreground/80 mb-1">{microTopicName}</p>
      <div className="text-xs text-muted-foreground mb-5 flex items-center gap-1.5">
        <span className="w-4 h-4 rounded gradient-primary flex items-center justify-center text-[8px] text-white">📍</span>
        {problem.level_display || `Poziom ${selectedLevel}`}
      </div>

      <h2 className="text-lg sm:text-xl font-semibold mb-4 text-foreground">Zadanie</h2>

      <div className="text-lg sm:text-2xl font-bold p-4 sm:p-6 rounded-2xl bg-secondary/50 dark:bg-white/5 border border-border/30 relative overflow-hidden">
        <BlockMath math={problem.question} />
      </div>

      {problem.image_html && (
        <div className="mt-4 flex justify-center">
          <div
            className="w-full max-w-full rounded-xl overflow-hidden"
            style={{ maxWidth: '100%' }}
            dangerouslySetInnerHTML={{ __html: problem.image_html }}
          />
        </div>
      )}
    </div>
  );
}
