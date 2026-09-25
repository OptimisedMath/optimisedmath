import type { SessionResponse } from './types';

/** Map a SessionResponse onto the display fields the arena renders. */
export function projectSessionState(state: SessionResponse) {
  const navigation = state.navigation;

  return {
    hasNavigation: Boolean(navigation),
    xp: state.xp,
    flawlessEligible: state.flawless_eligible,
    streakMeter: state.streak_meter,
    maxStreak: state.max_streak,
    currentInputMode: state.current_input_mode,
    selectedChapterId:
      state.selected_chapter_id ?? navigation?.available_chapters[0]?.chapter_id ?? 0,
    selectedTopicId:
      state.selected_topic_id ?? navigation?.available_topics[0]?.topic_id ?? 1,
    selectedLevel: state.selected_level,
    levelCompleted: state.level_completed,
    topicCompleted: state.topic_completed,
    hasNextUnlockedTopic: navigation?.has_next_unlocked_topic ?? false,
    chapterCompletion: navigation?.chapter_completion ?? null,
    topicCompletion: navigation?.topic_completion ?? null,
    availableChapters: navigation?.available_chapters ?? [],
    availableTopics: navigation?.available_topics ?? [],
    availableLevels: navigation?.available_levels ?? [],
  };
}

/** Display fields projected from SessionResponse for arena rendering. */
export type SessionDisplayProjection = ReturnType<typeof projectSessionState>;

/**
 * Mirrors backend/models.py's SessionResponse defaults, for the arena to render
 * before a Session exists. Nothing renders this today: the arena returns a
 * spinner or an error card before reaching any of these fields' readers.
 */
export const NO_SESSION_DISPLAY_PROJECTION: SessionDisplayProjection = {
  hasNavigation: false,
  xp: 0,
  flawlessEligible: true,
  streakMeter: 0,
  maxStreak: 3,
  currentInputMode: 'radio',
  selectedChapterId: 0,
  selectedTopicId: 1,
  selectedLevel: 1,
  levelCompleted: false,
  topicCompleted: false,
  hasNextUnlockedTopic: false,
  chapterCompletion: null,
  topicCompletion: null,
  availableChapters: [],
  availableTopics: [],
  availableLevels: [],
};
