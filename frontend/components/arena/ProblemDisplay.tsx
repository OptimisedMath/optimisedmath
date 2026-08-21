import { memo } from 'react';
import { BlockMath } from 'react-katex';
import { Spinner } from '@/components/ui/spinner';
import type { Problem } from '@/lib/session';
import 'katex/dist/katex.min.css';

interface ProblemDisplayProps {
  isLoadingProblem: boolean;
  problem: Problem | null;
  selectedLevel: number;
  selectedChapterName: string | null;
  topicName: string;
}

function ProblemDisplay({
  isLoadingProblem,
  problem,
  selectedLevel,
  selectedChapterName,
  topicName,
}: ProblemDisplayProps) {
  if (isLoadingProblem) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500 dark:text-slate-400">
        <Spinner className="h-8 w-8 text-sky-500 dark:text-sky-400" />
        <span className="text-lg font-semibold">Ładowanie zadania...</span>
      </div>
    );
  }

  if (!problem) {
    return null;
  }

  return (
    <div className="mb-6 text-slate-700 dark:text-slate-300">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-sky-600 dark:text-sky-300">{selectedChapterName}</p>
      <p className="mx-auto mt-1 max-w-xl text-base sm:text-lg font-semibold text-slate-900 dark:text-white">{topicName}</p>
      <div className="mt-3 mb-5 inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm text-slate-500 shadow-sm dark:border-slate-700 dark:bg-slate-950/70 dark:text-slate-400">
        📍 {problem.level_display || `Level ${selectedLevel}`}
      </div>
      <h2 className="text-lg sm:text-2xl font-bold mb-3 text-slate-950 dark:text-white">Zadanie</h2>
      <div className="mb-4 sm:mb-8 rounded-2xl border border-slate-200 bg-linear-to-br from-slate-50 to-sky-50/70 p-3 text-lg font-bold shadow-inner sm:p-5 sm:text-2xl dark:border-slate-700 dark:from-slate-950 dark:to-slate-900">
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

export default memo(ProblemDisplay);
