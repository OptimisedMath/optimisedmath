import { memo, type ChangeEvent } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { GameState, SessionNavigateRequest } from '@/lib/types';

type NavigateIntent = Pick<
  SessionNavigateRequest,
  'selected_macro' | 'selected_micro_topic_order' | 'selected_level'
>;

interface TopicToolbarProps {
  gameState: GameState;
  isNavigating: boolean;
  onNavigate: (intent: NavigateIntent) => void;
  onReset: () => void;
}

function TopicToolbar({
  gameState,
  isNavigating,
  onNavigate,
  onReset,
}: TopicToolbarProps) {
  const navigation = gameState.navigation;
  if (!navigation) {
    return null;
  }

  const selectedMacro = gameState.selected_macro ?? '';
  const selectedMicroTopicOrder = gameState.selected_micro_topic_order ?? 1;
  const selectedLevel = gameState.selected_level;

  const handleMacroChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onNavigate({ selected_macro: event.target.value });
  };

  const handleTopicChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onNavigate({ selected_micro_topic_order: Number(event.target.value) });
  };

  const handleLevelChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onNavigate({ selected_level: Number(event.target.value) });
  };

  return (
    <div className="w-full max-w-3xl rounded-2xl border border-white/70 bg-white/80 p-4 shadow-[0_16px_50px_rgba(15,23,42,0.10)] backdrop-blur-xl mb-4 dark:border-white/10 dark:bg-slate-900/75">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-600 dark:text-slate-300">Wybór tematu</div>
          <Button
            onClick={onReset}
            disabled={isNavigating}
            variant="destructive"
            size="sm"
            className="text-sm"
          >
            🔄 Zresetuj postęp
          </Button>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <label className="flex flex-1 flex-col gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Macro topic
            <select
              value={selectedMacro}
              onChange={handleMacroChange}
              disabled={isNavigating}
              className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-slate-950 shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/70 dark:text-white dark:focus:ring-sky-500/20"
            >
              {navigation.macro_topics.map((macro) => (
                <option key={macro} value={macro}>
                  {macro}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-1 flex-col gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Micro topic
            <select
              value={selectedMicroTopicOrder}
              onChange={handleTopicChange}
              disabled={isNavigating || navigation.available_micro_topics.length === 0}
              className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-slate-950 shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/70 dark:text-white dark:focus:ring-sky-500/20"
            >
              {navigation.available_micro_topics.map((topic, index) => (
                <option key={topic.micro_topic_order} value={topic.micro_topic_order}>
                  {index + 1}. {topic.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-slate-600 dark:text-slate-300 lg:w-28">
            Level
            <select
              value={selectedLevel}
              onChange={handleLevelChange}
              disabled={isNavigating}
              className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-slate-950 shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/70 dark:text-white dark:focus:ring-sky-500/20"
            >
              {navigation.available_levels.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <Badge variant="secondary">{navigation.current_topic_name || 'No topic selected'}</Badge>
          <span>Level {selectedLevel}</span>
          {isNavigating && <span className="text-blue-300">Loading topic...</span>}
          {gameState.admin_mode && <span className="text-green-400">🛠️ Admin mode active</span>}
        </div>
      </div>
    </div>
  );
}

export default memo(TopicToolbar);
