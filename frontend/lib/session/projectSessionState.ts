import type {
  NavigationChapterOption,
  NavigationProgress,
  NavigationTopicOption,
  SessionResponse,
} from './types';

export interface SessionDisplayProjection {
  hasNavigation: boolean;
  xp: number;
  flawlessEligible: boolean;
  streakMeter: number;
  maxStreak: number;
  currentInputMode: string;
  selectedChapterId: number;
  selectedTopicId: number;
  selectedLevel: number;
  levelCompleted: boolean;
  topicCompleted: boolean;
  hasNextUnlockedTopic: boolean;
  chapterCompletion: NavigationProgress | null;
  topicCompletion: NavigationProgress | null;
  availableChapters: NavigationChapterOption[];
  availableTopics: NavigationTopicOption[];
  availableLevels: number[];
}

export function emptySessionDisplayProjection(): SessionDisplayProjection {
  return {
    hasNavigation: false,
    xp: 0,
    flawlessEligible: false,
    streakMeter: 0,
    maxStreak: 0,
    currentInputMode: 'input',
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
}

export function projectSessionState(state: SessionResponse): SessionDisplayProjection {
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
