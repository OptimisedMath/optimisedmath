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
    <div className="w-full max-w-2xl bg-slate-800 dark:bg-slate-800 bg-white p-4 rounded-xl flex justify-between items-center shadow-lg mb-4 sm:mb-8 border border-slate-200 dark:border-slate-700">
      <div className="text-base sm:text-xl text-slate-900 dark:text-white">
        XP:{' '}
        <span className="text-yellow-500 dark:text-yellow-400 font-bold tabular-nums">
          {animatedXP}
        </span>
      </div>
      <div className="flex items-center gap-2 sm:gap-4">
        <div className="text-base sm:text-xl text-slate-900 dark:text-white">
          Bonus:{' '}
          <Badge
            variant={gameState.flawless_eligible ? 'default' : 'destructive'}
            className="ml-1 sm:ml-2"
          >
            {gameState.flawless_eligible ? 'Active 💎' : 'Lost ❌'}
          </Badge>
        </div>
        <button
          onClick={toggleTheme}
          className="bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border border-slate-300 dark:border-slate-600 whitespace-nowrap"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        {onLogout && (
          <button
            onClick={onLogout}
            className="bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border border-slate-300 dark:border-slate-600 whitespace-nowrap"
          >
            Wyloguj
          </button>
        )}
      </div>
    </div>
  );
}
