import { useState, type ChangeEvent } from 'react';
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
    <div className="w-full max-w-2xl bg-slate-800 p-4 rounded-xl shadow-lg mb-4 border border-slate-700">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-300">Admin Mode:</span>
            <button
              onClick={() => setAdminMode(!adminMode)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                adminMode
                  ? 'bg-green-600 hover:bg-green-500 text-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
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
          <label className="flex flex-1 flex-col gap-2 text-sm font-medium text-slate-300">
            Macro topic
            <select
              value={selectedMacro}
              onChange={handleMacroChange}
              disabled={isNavigating}
              className="h-10 rounded-lg border border-slate-600 bg-slate-900 px-3 text-white outline-none focus:border-blue-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {curriculum.macro_topics.map((macro) => (
                <option key={macro} value={macro}>
                  {macro}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-1 flex-col gap-2 text-sm font-medium text-slate-300">
            Micro topic
            <select
              value={selectedTopicOrder}
              onChange={handleTopicChange}
              disabled={isNavigating || topicOptions.length === 0}
              className="h-10 rounded-lg border border-slate-600 bg-slate-900 px-3 text-white outline-none focus:border-blue-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {topicOptions.map((topic, index) => (
                <option key={topic.order} value={topic.order}>
                  {index + 1}. {topic.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-slate-300 lg:w-28">
            Level
            <select
              value={selectedLevel}
              onChange={handleLevelChange}
              disabled={isNavigating}
              className="h-10 rounded-lg border border-slate-600 bg-slate-900 px-3 text-white outline-none focus:border-blue-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {levelOptions.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400">
          <Badge variant="secondary">{selectedTopic?.name || 'No topic selected'}</Badge>
          <span>Level {selectedLevel}</span>
          {isNavigating && <span className="text-blue-300">Loading topic...</span>}
          {adminMode && <span className="text-green-400">🛠️ Admin mode active</span>}
        </div>
      </div>
    </div>
  );
}
