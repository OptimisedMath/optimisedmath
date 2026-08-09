'use client';

import { memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { useAnimatedNumber } from '@/lib/hooks';
import { useTheme } from '@/components/ThemeProvider';
import LogoutLink from '@/components/navigation/LogoutLink';
import type { SessionView } from '@/lib/session';

interface XPBarProps {
  view: SessionView;
}

function XPBar({ view }: XPBarProps) {
  const animatedXP = useAnimatedNumber(view.session!.xp);
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="glass-card w-full max-w-3xl rounded-2xl p-3 mb-4 sm:mb-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <div className="gradient-xp flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-lg shadow-md shadow-amber-500/30">
          ⭐
        </div>
        <div className="text-base sm:text-xl text-slate-900 dark:text-white font-semibold">
          XP:{' '}
          <span className="text-amber-500 dark:text-amber-400 font-bold tabular-nums">
            {animatedXP}
          </span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <div className="text-sm sm:text-base text-slate-700 dark:text-slate-200">
          Bonus:{' '}
          <Badge
            variant={view.session!.flawless_eligible ? 'default' : 'destructive'}
            className="ml-1 sm:ml-2 shadow-sm"
          >
            {view.session!.flawless_eligible ? 'Aktywny 💎' : 'Stracony ❌'}
          </Badge>
        </div>
        <button
          onClick={toggleTheme}
          className="bg-slate-100/90 dark:bg-slate-800/90 hover:bg-sky-50 dark:hover:bg-slate-700 text-slate-900 dark:text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all border border-slate-200 dark:border-slate-700 whitespace-nowrap shadow-sm hover:border-sky-200"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        <LogoutLink className="bg-slate-100/90 dark:bg-slate-800/90 hover:bg-rose-50 dark:hover:bg-slate-700 text-slate-900 dark:text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all border border-slate-200 dark:border-slate-700 whitespace-nowrap shadow-sm hover:border-rose-200" />
      </div>
      </div>
    </div>
  );
}

export default memo(XPBar);
