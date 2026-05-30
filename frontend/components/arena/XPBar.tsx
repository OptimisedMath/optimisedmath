'use client';

import { Badge } from '@/components/ui/badge';
import type { GameState } from '@/lib/types';
import { useAnimatedNumber } from '@/lib/hooks';
import { useTheme } from '@/components/ThemeProvider';

interface XPBarProps {
  gameState: GameState;
  onLogout?: () => void;
}

export default function XPBar({ gameState, onLogout }: XPBarProps) {
  const animatedXP = useAnimatedNumber(gameState.xp);
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="w-full max-w-3xl rounded-2xl border border-white/70 bg-white/80 p-3 shadow-[0_16px_50px_rgba(15,23,42,0.12)] backdrop-blur-xl mb-4 sm:mb-6 dark:border-white/10 dark:bg-slate-900/75">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="text-base sm:text-xl text-slate-900 dark:text-white font-semibold">
        XP:{' '}
        <span className="text-yellow-500 dark:text-yellow-400 font-bold tabular-nums">
          {animatedXP}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <div className="text-sm sm:text-base text-slate-700 dark:text-slate-200">
          Bonus:{' '}
          <Badge
            variant={gameState.flawless_eligible ? 'default' : 'destructive'}
            className="ml-1 sm:ml-2 shadow-sm"
          >
            {gameState.flawless_eligible ? 'Active 💎' : 'Lost ❌'}
          </Badge>
        </div>
        <button
          onClick={toggleTheme}
          className="bg-slate-100/90 dark:bg-slate-800/90 hover:bg-sky-50 dark:hover:bg-slate-700 text-slate-900 dark:text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all border border-slate-200 dark:border-slate-700 whitespace-nowrap shadow-sm hover:border-sky-200"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        {onLogout && (
          <button
            onClick={onLogout}
            className="bg-slate-100/90 dark:bg-slate-800/90 hover:bg-rose-50 dark:hover:bg-slate-700 text-slate-900 dark:text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all border border-slate-200 dark:border-slate-700 whitespace-nowrap shadow-sm hover:border-rose-200"
          >
            Wyloguj
          </button>
        )}
      </div>
      </div>
    </div>
  );
}
