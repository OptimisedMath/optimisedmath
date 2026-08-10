import type {
  Problem,
  ProblemResponse,
  SessionState,
  SubmissionResponse,
} from '@/lib/session/types';
import { onGet, onPost } from './apiMock';

export function defaultNavigation(): SessionState['navigation'] {
  return {
    available_chapters: [{ chapter_id: 10, name: 'Ułamki' }],
    current_topic_name: 'Dodawanie',
    available_topics: [{ topic_id: 1, name: 'Dodawanie' }],
    available_levels: [1, 2, 3],
    has_next_unlocked_topic: true,
    radio_only: false,
    chapter_completion: { completed: 1, total: 5, percentage: 20 },
    topic_completion: { completed: 1, total: 3, percentage: 33 },
  };
}

export function baseSession(overrides: Partial<SessionState> = {}): SessionState {
  return {
    session_id: 'sess-test',
    username: 'testuser',
    xp: 50,
    streak: 2,
    flawless_eligible: true,
    max_streak: 3,
    streak_meter: 2,
    selected_chapter_id: 10,
    selected_topic_id: 1,
    selected_level: 1,
    problem_answered: false,
    current_input_mode: 'input',
    topic_completed: false,
    feedback_type: null,
    feedback_msg: '',
    level_completed: false,
    chapter_frontiers: {},
    current_problem: null,
    can_submit: true,
    can_next_problem: false,
    navigation: defaultNavigation(),
    ...overrides,
  };
}

export function baseProblem(overrides: Partial<Problem> = {}): Problem {
  return {
    question: '2+2',
    correct_answer: '4',
    level: 1,
    level_name: 'Poziom 1',
    problem_id: 'prob-1',
    level_display: 'Poziom 1',
    keyboard_type: 'default',
    ...overrides,
  };
}

/** Wire the three session endpoints used by a typical arena play-through. */
export function wireArenaFlow({
  session,
  problem,
  onSubmit,
}: {
  session: SessionState;
  problem: Problem;
  onSubmit: () => SubmissionResponse;
}) {
  onPost('/session/start', () => session);

  onGet('/problem/next', () => {
    const state: SessionState = {
      ...session,
      current_problem: problem,
      can_submit: true,
      can_next_problem: false,
    };
    const response: ProblemResponse = { problem, state };
    return response;
  });

  onPost('/problem/submit', () => onSubmit());
}
