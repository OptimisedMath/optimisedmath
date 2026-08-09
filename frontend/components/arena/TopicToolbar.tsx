import { memo, type ChangeEvent } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { SessionActions, SessionView } from '@/lib/session';

interface TopicToolbarProps {
  view: SessionView;
  actions: SessionActions;
}

function TopicToolbar({ view, actions }: TopicToolbarProps) {
  const session = view.session!;
  const navigation = session.navigation;
  if (!navigation) {
    return null;
  }

  const selectedChapterId = session.selected_chapter_id ?? navigation.available_chapters[0]?.chapter_id ?? 0;
  const selectedTopicId = session.selected_topic_id ?? navigation.available_topics[0]?.topic_id ?? 1;
  const selectedLevel = session.selected_level;

  const handleChapterChange = (event: ChangeEvent<HTMLSelectElement>) => {
    actions.navigate({ selected_chapter_id: Number(event.target.value) });
  };

  const handleTopicChange = (event: ChangeEvent<HTMLSelectElement>) => {
    actions.navigate({ selected_topic_id: Number(event.target.value) });
  };

  const handleLevelChange = (event: ChangeEvent<HTMLSelectElement>) => {
    actions.navigate({ selected_level: Number(event.target.value) });
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
            onClick={actions.reset}
            disabled={view.isNavigating}
            variant="destructive"
            size="sm"
            className="text-sm hover:-translate-y-0.5"
          >
            🔄 Zresetuj postęp
          </Button>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <label className={labelClasses}>
            Dział
            <select
              value={selectedChapterId}
              onChange={handleChapterChange}
              disabled={view.isNavigating}
              className={selectClasses}
            >
              {navigation.available_chapters.map((chapter) => (
                <option key={chapter.chapter_id} value={chapter.chapter_id}>
                  {chapter.name}
                </option>
              ))}
            </select>
          </label>

          <label className={labelClasses}>
            Temat
            <select
              value={selectedTopicId}
              onChange={handleTopicChange}
              disabled={view.isNavigating || navigation.available_topics.length === 0}
              className={selectClasses}
            >
              {navigation.available_topics.map((topic, index) => (
                <option key={topic.topic_id} value={topic.topic_id}>
                  {index + 1}. {topic.name}
                </option>
              ))}
            </select>
          </label>

          <label className={`${labelClasses} lg:w-28 lg:flex-none`}>
            Poziom
            <select
              value={selectedLevel}
              onChange={handleLevelChange}
              disabled={view.isNavigating}
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
          <Badge variant="secondary">{view.topicName}</Badge>
          <span>Poziom {selectedLevel}</span>
          {view.isNavigating && <span className="text-sky-500 dark:text-sky-300">Ładowanie tematu...</span>}
          {view.adminMode && (
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
