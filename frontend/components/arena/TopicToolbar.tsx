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

  const selectClasses =
    'h-11 rounded-lg border border-slate-200 bg-white px-3 text-slate-950 shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/70 dark:text-white dark:focus:ring-sky-500/20';
  const labelClasses = 'flex flex-1 flex-col gap-2 text-sm font-medium text-slate-600 dark:text-slate-300';

  return (
    <div className="glass-card w-full max-w-3xl rounded-2xl p-4 mb-4">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-600 dark:text-slate-300">Wybór tematu</div>
          <Button
            onClick={onReset}
            disabled={isNavigating}
            variant="destructive"
            size="sm"
            className="text-sm hover:-translate-y-0.5"
          >
            🔄 Zresetuj postęp
          </Button>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <label className={labelClasses}>
            Macro topic
            <select
              value={selectedMacro}
              onChange={handleMacroChange}
              disabled={isNavigating}
              className={selectClasses}
            >
              {navigation.macro_topics.map((macro) => (
                <option key={macro} value={macro}>
                  {macro}
                </option>
              ))}
            </select>
          </label>

          <label className={labelClasses}>
            Micro topic
            <select
              value={selectedMicroTopicOrder}
              onChange={handleTopicChange}
              disabled={isNavigating || navigation.available_micro_topics.length === 0}
              className={selectClasses}
            >
              {navigation.available_micro_topics.map((topic, index) => (
                <option key={topic.micro_topic_order} value={topic.micro_topic_order}>
                  {index + 1}. {topic.name}
                </option>
              ))}
            </select>
          </label>

          <label className={`${labelClasses} lg:w-28 lg:flex-none`}>
            Level
            <select
              value={selectedLevel}
              onChange={handleLevelChange}
              disabled={isNavigating}
              className={selectClasses}
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
          {isNavigating && <span className="text-sky-500 dark:text-sky-300">Loading topic...</span>}
          {gameState.admin_mode && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-400/10 dark:text-emerald-300">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              Tryb administratora
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default memo(TopicToolbar);
