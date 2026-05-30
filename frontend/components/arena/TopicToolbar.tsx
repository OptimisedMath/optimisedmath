import { type ChangeEvent } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { CurriculumResponse, GameState } from '@/lib/types';

interface TopicToolbarProps {
  curriculum: CurriculumResponse;
  gameState: GameState;
  isNavigating: boolean;
  onNavigate: (macro: string, topicOrder: number, level: number) => void;
  onReset: () => void;
  adminMode: boolean;
  setAdminMode: (value: boolean) => void;
}

export default function TopicToolbar({
  curriculum,
  gameState,
  isNavigating,
  onNavigate,
  onReset,
  adminMode,
  setAdminMode,
}: TopicToolbarProps) {
  const selectedMacro = gameState.selected_macro || curriculum.macro_topics[0] || '';
  const topics = curriculum.topics[selectedMacro] || [];
  const firstTopic = topics[0];
  const selectedTopicOrder = gameState.selected_topic_order || firstTopic?.order || 1;
  const selectedTopic = topics.find((topic) => topic.order === selectedTopicOrder) || firstTopic;
  const selectedLevel = Math.min(gameState.selected_level || 1, selectedTopic?.max_level || 1);
  const progress = selectedMacro ? gameState.progress[selectedMacro] : undefined;
  const unlockedOrder = progress?.unlocked_order ?? firstTopic?.order ?? 1;
  const unlockedLevel = progress?.unlocked_level ?? 1;

  // When admin mode is enabled, show all topics and levels
  const availableTopics = adminMode ? topics : topics.filter((topic) => topic.order <= unlockedOrder);
  const topicOptions = availableTopics.length > 0 ? availableTopics : topics.slice(0, 1);
  const levelLimit = selectedTopic
    ? adminMode || selectedTopic.order < unlockedOrder
      ? selectedTopic.max_level
      : Math.min(unlockedLevel, selectedTopic.max_level)
    : 1;
  const levelOptions = Array.from({ length: Math.max(levelLimit, 1) }, (_, index) => index + 1);

  const handleMacroChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextMacro = event.target.value;
    const nextProgress = gameState.progress[nextMacro];
    const nextTopics = curriculum.topics[nextMacro] || [];
    const nextTopicOrder = nextProgress?.unlocked_order ?? nextTopics[0]?.order ?? 1;
    const nextTopic = nextTopics.find((topic) => topic.order === nextTopicOrder) || nextTopics[0];
    const nextLevel = Math.min(nextProgress?.unlocked_level ?? 1, nextTopic?.max_level ?? 1);

    onNavigate(nextMacro, nextTopicOrder, nextLevel);
  };

  const handleTopicChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextTopicOrder = Number(event.target.value);
    const nextTopic = topics.find((topic) => topic.order === nextTopicOrder);
    const nextLevel = nextTopicOrder < unlockedOrder
      ? 1
      : Math.min(unlockedLevel, nextTopic?.max_level ?? 1);

    onNavigate(selectedMacro, nextTopicOrder, nextLevel);
  };

  const handleLevelChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onNavigate(selectedMacro, selectedTopicOrder, Number(event.target.value));
  };

  return (
    <div className="w-full max-w-3xl rounded-2xl border border-white/70 bg-white/80 p-4 shadow-[0_16px_50px_rgba(15,23,42,0.10)] backdrop-blur-xl mb-4 dark:border-white/10 dark:bg-slate-900/75">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Admin Mode:</span>
            <button
              onClick={() => setAdminMode(!adminMode)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all shadow-sm ${
                adminMode
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300 dark:border-slate-700'
              }`}
            >
              {adminMode ? 'ON 🛠️' : 'OFF'}
            </button>
          </div>
          <Button
            onClick={onReset}
            disabled={isNavigating}
            variant="destructive"
            size="sm"
            className="text-sm"
          >
            🔄 Reset Progress
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
              {curriculum.macro_topics.map((macro) => (
                <option key={macro} value={macro}>
                  {macro}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-1 flex-col gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Micro topic
            <select
              value={selectedTopicOrder}
              onChange={handleTopicChange}
              disabled={isNavigating || topicOptions.length === 0}
              className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-slate-950 shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/70 dark:text-white dark:focus:ring-sky-500/20"
            >
              {topicOptions.map((topic, index) => (
                <option key={topic.order} value={topic.order}>
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
              {levelOptions.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <Badge variant="secondary">{selectedTopic?.name || 'No topic selected'}</Badge>
          <span>Level {selectedLevel}</span>
          {isNavigating && <span className="text-blue-300">Loading topic...</span>}
          {adminMode && <span className="text-green-400">🛠️ Admin mode active</span>}
        </div>
      </div>
    </div>
  );
}
