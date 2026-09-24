import { describe, expect, it } from 'vitest';
import {
  NO_SESSION_DISPLAY_PROJECTION,
  projectSessionState,
} from '@/lib/session/projectSessionState';
import type { SessionResponse } from '@/lib/session/types';
import { baseSession, defaultNavigation } from './fakeBackend';

describe('projectSessionState', () => {
  it('maps every display field, preferring the session-selected chapter/topic over navigation', () => {
    const navigation = defaultNavigation();
    const state = baseSession({
      xp: 120,
      flawless_eligible: false,
      streak_meter: 2,
      max_streak: 5,
      current_input_mode: 'radio',
      selected_chapter_id: 10,
      selected_topic_id: 1,
      selected_level: 2,
      level_completed: true,
      topic_completed: false,
      navigation: {
        ...navigation,
        has_next_unlocked_topic: true,
        chapter_completion: { completed: 2, total: 5, percentage: 40 },
        topic_completion: { completed: 2, total: 3, percentage: 67 },
      },
    });

    expect(projectSessionState(state)).toEqual({
      hasNavigation: true,
      xp: 120,
      flawlessEligible: false,
      streakMeter: 2,
      maxStreak: 5,
      currentInputMode: 'radio',
      selectedChapterId: 10,
      selectedTopicId: 1,
      selectedLevel: 2,
      levelCompleted: true,
      topicCompleted: false,
      hasNextUnlockedTopic: true,
      chapterCompletion: { completed: 2, total: 5, percentage: 40 },
      topicCompletion: { completed: 2, total: 3, percentage: 67 },
      availableChapters: navigation.available_chapters,
      availableTopics: navigation.available_topics,
      availableLevels: navigation.available_levels,
    });
  });

  it('resolves selected chapter/topic from navigation fallbacks when session ids are null', () => {
    const navigation = defaultNavigation()!;
    const state = baseSession({
      selected_chapter_id: null,
      selected_topic_id: null,
      navigation,
    });

    expect(projectSessionState(state).selectedChapterId).toBe(10);
    expect(projectSessionState(state).selectedTopicId).toBe(1);
  });

  it('returns safe defaults when navigation is missing', () => {
    // #341 made `navigation` non-null on the wire — backend/session.py's single
    // SessionResponse builder always attaches one — but kept projectSessionState's
    // fallbacks. The cast reaches the shape the type now forbids, so the fallbacks
    // stay covered rather than silently rotting.
    const state = {
      ...baseSession({ selected_chapter_id: null, selected_topic_id: null }),
      navigation: null,
    } as unknown as SessionResponse;

    expect(projectSessionState(state)).toMatchObject({
      hasNavigation: false,
      hasNextUnlockedTopic: false,
      chapterCompletion: null,
      topicCompletion: null,
      availableChapters: [],
      availableTopics: [],
      availableLevels: [],
      selectedChapterId: 0,
      selectedTopicId: 1,
    });
  });

  it('NO_SESSION_DISPLAY_PROJECTION mirrors the backend SessionResponse defaults', () => {
    expect(NO_SESSION_DISPLAY_PROJECTION).toEqual({
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
    });
  });
});
