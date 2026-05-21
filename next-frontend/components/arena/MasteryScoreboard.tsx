import type { GameState } from '@/lib/types';

interface MasteryScoreboardProps {
  gameState: GameState;
}

export default function MasteryScoreboard({ gameState }: MasteryScoreboardProps) {
  const { streak, max_streak } = gameState;
  const stars = '⭐'.repeat(streak);
  const emptyStars = '⬛'.repeat(max_streak - streak);

  return (
    <div className="w-full mb-4">
      <div className="text-center text-slate-300 text-sm mb-2">
        Postęp do kolejnego poziomu:
      </div>
      <div className="text-center text-4xl tracking-wider">
        {stars}
        {emptyStars}
      </div>
      <div className="text-center text-slate-400 text-xs mt-1">
        {streak}/{max_streak} gwiazdek
      </div>
    </div>
  );
}
