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
    <div className="w-full max-w-2xl mb-4 animate-fade-slide-in" style={{ animationDelay: '0.2s' }}>
      <div className="text-center text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
        Postęp do kolejnego poziomu
      </div>
      <div className="flex justify-center gap-1.5">
        {Array.from({ length: max_streak }).map((_, i) => {
          const isEarned = i < streak;
          const isAnimating = i === animatingIndex;

          return (
            <div
              key={i}
              className={`w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center text-lg transition-all duration-300 ${
                isEarned
                  ? 'bg-amber-400/20 dark:bg-amber-400/15 border border-amber-400/40 shadow-[0_0_8px_oklch(0.8_0.18_80/0.2)]'
                  : 'bg-secondary/50 dark:bg-white/5 border border-border/30'
              } ${isAnimating ? 'scale-125' : 'scale-100'}`}
              style={isAnimating ? { animation: 'star-pop 0.4s ease-out' } : undefined}
            >
              {isEarned ? '⭐' : (
                <span className="w-2 h-2 rounded-full bg-muted-foreground/20" />
              )}
            </div>
          );
        })}
      </div>
      <div className="text-center text-xs text-muted-foreground mt-2 tabular-nums">
        {streak}/{max_streak}
      </div>
    </div>
  );
}
