'use client';

import { useEffect, useRef, useState } from 'react';
import type { GameState } from '@/lib/types';

interface MasteryScoreboardProps {
  gameState: GameState;
}

export default function MasteryScoreboard({ gameState }: MasteryScoreboardProps) {
  const { streak, max_streak } = gameState;
  const prevStreak = useRef(streak);
  const [animatingIndex, setAnimatingIndex] = useState<number | null>(null);

  useEffect(() => {
    if (streak > prevStreak.current) {
      setAnimatingIndex(streak - 1);
      const timer = setTimeout(() => setAnimatingIndex(null), 400);
      prevStreak.current = streak;
      return () => clearTimeout(timer);
    }
    prevStreak.current = streak;
  }, [streak]);

  return (
    <div className="w-full max-w-3xl mb-4 rounded-2xl border border-white/70 bg-white/75 p-4 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-900/55">
      <div className="text-center text-slate-600 dark:text-slate-300 text-sm font-medium mb-3">
        Postęp do kolejnego poziomu:
      </div>
      <div className="text-center text-3xl sm:text-4xl tracking-wider flex justify-center gap-1.5">
        {Array.from({ length: max_streak }).map((_, i) => (
          <span
            key={i}
            className={`inline-block rounded-lg transition-transform duration-300 ${
              i === animatingIndex ? 'scale-125' : 'scale-100'
            }`}
            style={i === animatingIndex ? { animation: 'star-pop 0.4s ease-out' } : undefined}
          >
            {i < streak ? '⭐' : '⬛'}
          </span>
        ))}
      </div>
      <div className="text-center text-slate-500 dark:text-slate-400 text-xs mt-2">
        {streak}/{max_streak} gwiazdek
      </div>
    </div>
  );
}
