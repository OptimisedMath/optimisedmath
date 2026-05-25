import { Badge } from '@/components/ui/badge';
import type { GameState } from '@/lib/types';

interface XPBarProps {
  gameState: GameState;
}

export default function XPBar({ gameState }: XPBarProps) {
  return (
    <div className="w-full max-w-2xl bg-slate-800 p-4 rounded-xl flex justify-between items-center shadow-lg mb-8 border border-slate-700">
      <div className="text-xl">
        XP: <span className="text-yellow-400 font-bold">{gameState.xp}</span>
      </div>
      <div className="text-xl">
        Bonus:{' '}
        <Badge
          variant={gameState.flawless_eligible ? 'default' : 'destructive'}
          className="ml-2"
        >
          {gameState.flawless_eligible ? 'Active 💎' : 'Lost ❌'}
        </Badge>
      </div>
    </div>
  );
}
