import { Badge } from '@/components/ui/badge';
import type { GameState } from '@/lib/types';

interface XPBarProps {
  gameState: GameState;
  onLogout?: () => void;
}

export default function XPBar({ gameState, onLogout }: XPBarProps) {
  return (
    <div className="w-full max-w-2xl bg-slate-800 p-4 rounded-xl flex justify-between items-center shadow-lg mb-4 sm:mb-8 border border-slate-700">
      <div className="text-base sm:text-xl">
        XP: <span className="text-yellow-400 font-bold">{gameState.xp}</span>
      </div>
      <div className="flex items-center gap-2 sm:gap-4">
        <div className="text-base sm:text-xl">
          Bonus:{' '}
          <Badge
            variant={gameState.flawless_eligible ? 'default' : 'destructive'}
            className="ml-1 sm:ml-2"
          >
            {gameState.flawless_eligible ? 'Active 💎' : 'Lost ❌'}
          </Badge>
        </div>
        {onLogout && (
          <button
            onClick={onLogout}
            className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border border-slate-600 whitespace-nowrap"
          >
            Wyloguj
          </button>
        )}
      </div>
    </div>
  );
}
