import { memo } from 'react';
import type { NavigationProgress } from '@/lib/types';

interface ProgressBarProps {
  type: 'chapter' | 'topic';
  selectedChapterName?: string | null;
  selectedLevel?: number;
  chapterProgress?: NavigationProgress | null;
  topicProgress?: NavigationProgress | null;
  currentTopicName?: string | null;
}

function ProgressBar({
  type,
  selectedChapterName,
  selectedLevel,
  chapterProgress,
  topicProgress,
  currentTopicName,
}: ProgressBarProps) {
  if (type === 'chapter' && selectedChapterName && chapterProgress) {
    const { completed, total, percentage } = chapterProgress;

    return (
      <div className="glass-card w-full max-w-3xl mb-4 rounded-xl p-3">
        <div className="flex justify-between gap-4 text-sm text-slate-600 dark:text-slate-300 mb-2">
          <span className="truncate font-medium">🏆 {selectedChapterName}</span>
          <span className="shrink-0 tabular-nums">{completed}/{total} tematów ukończonych</span>
        </div>
        <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div
            className="shimmer-bar bg-gradient-to-r from-sky-500 to-blue-600 h-2.5 rounded-full transition-all duration-500 shadow-[0_0_18px_rgba(14,165,233,0.45)]"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }

  if (type === 'topic' && topicProgress && selectedLevel !== undefined) {
    const { total, percentage } = topicProgress;

    return (
      <div className="glass-card w-full max-w-3xl mb-4 rounded-xl p-3">
        <div className="flex justify-between gap-4 text-sm text-slate-600 dark:text-slate-300 mb-2">
          <span className="truncate font-medium">📚 {currentTopicName || 'Aktualny temat'}</span>
          <span className="shrink-0 tabular-nums">Poziom {selectedLevel}/{total}</span>
        </div>
        <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div
            className="shimmer-bar bg-gradient-to-r from-emerald-500 to-teal-400 h-2.5 rounded-full transition-all duration-500 shadow-[0_0_18px_rgba(16,185,129,0.45)]"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }

  return null;
}

export default memo(ProgressBar);
