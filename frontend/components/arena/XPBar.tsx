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
    <div className="w-full max-w-2xl glass-card p-4 rounded-2xl flex justify-between items-center mb-4 sm:mb-6 animate-fade-slide-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl gradient-xp flex items-center justify-center text-lg shadow-md">
          ⚡
        </div>
        <div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">XP</div>
          <div className="text-xl sm:text-2xl font-bold tabular-nums text-amber-600 dark:text-amber-400">
            {animatedXP}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <Badge
          variant={gameState.flawless_eligible ? 'default' : 'destructive'}
          className={`text-xs sm:text-sm px-2.5 py-1 ${
            gameState.flawless_eligible
              ? 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30'
              : ''
          }`}
        >
          {gameState.flawless_eligible ? 'Bonus 💎' : 'Lost ❌'}
        </Badge>

        <button
          onClick={toggleTheme}
          className="w-9 h-9 rounded-xl bg-secondary hover:bg-accent flex items-center justify-center text-base transition-all hover:scale-105 active:scale-95 border border-border/50"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>

        {onLogout && (
          <button
            onClick={onLogout}
            className="h-9 px-3 rounded-xl bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-all hover:scale-105 active:scale-95 border border-border/50 whitespace-nowrap"
          >
            Wyloguj
          </button>
        )}
      </div>
    </div>
  );
}
