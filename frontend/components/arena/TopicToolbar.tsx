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

  const selectClasses = "h-10 rounded-xl border border-border bg-secondary/50 dark:bg-white/5 px-3 text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50 transition-all";

  return (
    <div className="w-full max-w-2xl glass-card p-4 rounded-2xl mb-4 animate-fade-slide-in" style={{ animationDelay: '0.05s' }}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Admin</span>
            <button
              onClick={() => setAdminMode(!adminMode)}
              className={`relative w-11 h-6 rounded-full transition-all duration-300 ${
                adminMode
                  ? 'bg-emerald-500 shadow-[0_0_10px_oklch(0.6_0.2_155/0.3)]'
                  : 'bg-secondary border border-border'
              }`}
            >
              <span
                className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-all duration-300 ${
                  adminMode ? 'left-[22px]' : 'left-0.5'
                }`}
              />
            </button>
          </div>
          <Button
            onClick={onReset}
            disabled={isNavigating}
            variant="destructive"
            size="sm"
            className="text-xs rounded-xl"
          >
            🔄 Reset
          </Button>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex flex-1 flex-col gap-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Dział
            <select
              value={selectedMacro}
              onChange={handleMacroChange}
              disabled={isNavigating}
              className={selectClasses}
            >
              {curriculum.macro_topics.map((macro) => (
                <option key={macro} value={macro}>
                  {macro}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-1 flex-col gap-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Temat
            <select
              value={selectedTopicOrder}
              onChange={handleTopicChange}
              disabled={isNavigating || topicOptions.length === 0}
              className={selectClasses}
            >
              {topicOptions.map((topic, index) => (
                <option key={topic.order} value={topic.order}>
                  {index + 1}. {topic.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider lg:w-24">
            Poziom
            <select
              value={selectedLevel}
              onChange={handleLevelChange}
              disabled={isNavigating}
              className={selectClasses}
            >
              {levelOptions.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <Badge variant="secondary" className="rounded-lg bg-primary/10 text-primary border border-primary/20">
            {selectedTopic?.name || 'Brak tematu'}
          </Badge>
          <span className="text-muted-foreground">Poziom {selectedLevel}</span>
          {isNavigating && (
            <span className="text-primary flex items-center gap-1">
              <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Ładowanie...
            </span>
          )}
          {adminMode && <span className="text-emerald-500">🛠️ Admin</span>}
        </div>
      </div>
    </div>
  );
}
