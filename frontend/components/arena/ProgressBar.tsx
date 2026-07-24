import type { GameState } from '@/lib/types';

interface ProgressBarProps {
  gameState: GameState;
  type: 'macro' | 'micro';
}

export default function ProgressBar({ gameState, type }: ProgressBarProps) {
  const navigation = gameState.navigation;
  if (!navigation) {
    return null;
  }

  if (type === 'macro' && gameState.selected_macro && navigation.macro_progress) {
    const { completed, total, percentage } = navigation.macro_progress;

    return (
      <div className="w-full max-w-3xl mb-4 rounded-xl border border-white/70 bg-white/70 p-3 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-900/55">
        <div className="flex justify-between gap-4 text-sm text-slate-600 dark:text-slate-300 mb-2">
          <span className="truncate font-medium">🏆 {gameState.selected_macro}</span>
          <span className="shrink-0 tabular-nums">{completed}/{total} tematów ukończonych</span>
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

  if (type === 'micro' && navigation.micro_progress) {
    const { total, percentage } = navigation.micro_progress;
    const selectedLevel = gameState.selected_level;

    return (
      <div className="w-full max-w-3xl mb-4 rounded-xl border border-white/70 bg-white/70 p-3 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-900/55">
        <div className="flex justify-between gap-4 text-sm text-slate-600 dark:text-slate-300 mb-2">
          <span className="truncate font-medium">📚 {navigation.current_topic_name || 'Current topic'}</span>
          <span className="shrink-0 tabular-nums">Level {selectedLevel}/{total}</span>
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
