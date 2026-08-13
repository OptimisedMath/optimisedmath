'use client';

import { memo, useEffect, useRef, useState } from 'react';
import type { SessionView } from '@/lib/session';

interface MasteryScoreboardProps {
  view: SessionView;
}

function MasteryScoreboard({ view }: MasteryScoreboardProps) {
  const streakMeter = view.streakMeter;
  const maxStreak = view.maxStreak;
  const prevStreakMeter = useRef(streakMeter);
  const [animatingIndex, setAnimatingIndex] = useState<number | null>(null);

  useEffect(() => {
    if (streakMeter > prevStreakMeter.current) {
      setAnimatingIndex(streakMeter - 1);
      const timer = setTimeout(() => setAnimatingIndex(null), 400);
      prevStreakMeter.current = streakMeter;
      return () => clearTimeout(timer);
    }
    prevStreakMeter.current = streakMeter;
  }, [streakMeter]);

  return (
    <div className="glass-card w-full max-w-3xl mb-4 rounded-2xl p-4">
      <div className="text-center text-slate-600 dark:text-slate-300 text-sm font-medium mb-3">
        Postęp do kolejnego poziomu:
      </div>
      <div className="flex justify-center gap-1.5 sm:gap-2">
        {Array.from({ length: maxStreak }).map((_, i) => {
          const earned = i < streakMeter;
          return (
            <div
              key={i}
              className={`flex h-9 w-9 sm:h-11 sm:w-11 items-center justify-center rounded-xl text-2xl sm:text-3xl transition-all duration-300 ${
                earned
                  ? 'glow-xp gradient-xp scale-100'
                  : 'bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700'
              } ${i === animatingIndex ? 'scale-125' : ''}`}
              style={i === animatingIndex ? { animation: 'star-pop 0.4s ease-out' } : undefined}
            >
              {earned ? '⭐' : ''}
            </div>
          );
        })}
      </div>
      <div className="text-center text-slate-500 dark:text-slate-400 text-xs mt-3">
        {streakMeter}/{maxStreak} gwiazdek
      </div>
    </div>
  );
}

export default memo(MasteryScoreboard);
