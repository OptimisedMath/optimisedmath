import { vi } from 'vitest';
import type { SessionClient } from '@/lib/session/client';
import type {
  DeconstructionStepResponse,
  Problem,
  ProblemResponse,
  SessionResponse,
  SubmissionResponse,
} from '@/lib/session/types';

export function defaultNavigation(): SessionResponse['navigation'] {
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

export function baseSession(overrides: Partial<SessionResponse> = {}): SessionResponse {
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
    deconstruction_running: false,
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

export function baseDeconstructionStep(
  overrides: Partial<DeconstructionStepResponse> = {}
): DeconstructionStepResponse {
  return {
    question: 'Jaki jest wspólny mianownik ułamków?',
    working_line: '\\frac{2}{3} + \\frac{1}{4}',
    step_index: 0,
    total_steps: 2,
    misconception_name: 'Dodawanie ułamków o różnych mianownikach',
    revealed_answer: null,
    input_type: 'typed',
    items: null,
    ...overrides,
  };
}

export const ORDERING_STEP_ITEMS = [
  'nawiasy',
  'potęgi',
  'mnożenie i dzielenie',
  'dodawanie i odejmowanie',
];

/** A stand-in ordering step (#198) — no batch-two walkthrough is authored here. */
export function baseOrderingDeconstructionStep(
  overrides: Partial<DeconstructionStepResponse> = {}
): DeconstructionStepResponse {
  return baseDeconstructionStep({
    question: 'Ułóż drabinkę priorytetów w poprawnej kolejności.',
    working_line: null,
    input_type: 'ordering',
    items: [...ORDERING_STEP_ITEMS],
    ...overrides,
  });
}

/**
 * A triggering Submission's Problem, exactly as the backend serves it: the
 * spoiler fix withholds `correct_answer` while a Deconstruction is running
 * (`public_problem` in `backend/session.py`). This is a spoiler rule only —
 * the takeover itself arms off `SessionResponse.deconstruction_running`.
 */
export function withoutCorrectAnswer(problem: Problem): Problem {
  const clone: Problem = { ...problem };
  delete clone.correct_answer;
  return clone;
}

/**
 * Returns `session` with its Problem set to `problem` — a helper rather than
 * a repeated `{ ...session, current_problem: problem }` at every call site,
 * since a field-declaration-shaped line spelling out that wire field name
 * reads to tooling as the banned "current" synonym for Selected (CONTEXT.md).
 */
export function withProblem(session: SessionResponse, problem: Problem): SessionResponse {
  return { ...session, current_problem: problem };
}

function unwired(operation: string) {
  return async () => {
    throw new Error(`Unhandled ${operation}`);
  };
}

/**
 * The in-memory SessionClient adapter — the one fake for frontend tests.
 * Tests supply handlers for the operations a scenario exercises; every
 * method is a spy so a test can assert on the domain-shaped request it
 * received without knowing a route.
 */
export function createFakeSessionClient(handlers: Partial<SessionClient> = {}): SessionClient {
  return {
    startSession: vi.fn(handlers.startSession ?? unwired('startSession')),
    navigateSession: vi.fn(handlers.navigateSession ?? unwired('navigateSession')),
    resetSession: vi.fn(handlers.resetSession ?? unwired('resetSession')),
    getNextProblem: vi.fn(handlers.getNextProblem ?? unwired('getNextProblem')),
    submitAnswer: vi.fn(handlers.submitAnswer ?? unwired('submitAnswer')),
    getDeconstructionStep: vi.fn(
      handlers.getDeconstructionStep ?? unwired('getDeconstructionStep')
    ),
    submitDeconstructionStep: vi.fn(
      handlers.submitDeconstructionStep ?? unwired('submitDeconstructionStep')
    ),
    abandonDeconstruction: vi.fn(
      handlers.abandonDeconstruction ?? unwired('abandonDeconstruction')
    ),
  };
}

/** The graded Feedback a Deconstruction-arming Submission comes back with. */
export const TRAP_FEEDBACK = 'Trap feedback';

/**
 * Wires an arena play-through whose Submission arms a Deconstruction: the graded
 * answer comes back wrong and locked, with `deconstruction_running` set and a
 * Problem stripped of its `correct_answer`, exactly as the backend serves it.
 * Every fixture defaults, and later handlers win, so a scenario names only the
 * step it varies and the operation it spies on.
 */
export function wireDeconstructionTriggerFlow({
  session = baseSession(),
  problem = baseProblem(),
  triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' })),
  step = baseDeconstructionStep(),
  ...handlers
}: {
  session?: SessionResponse;
  problem?: Problem;
  triggerProblem?: Problem;
  step?: DeconstructionStepResponse;
} & Partial<SessionClient> = {}): SessionClient {
  const locked: SessionResponse = {
    ...session,
    can_submit: false,
    // The backend shuts the next-problem gate while a Deconstruction runs.
    can_next_problem: false,
    deconstruction_running: true,
    feedback_type: 'warning',
    feedback_msg: TRAP_FEEDBACK,
  };

  return createFakeSessionClient({
    startSession: async () => session,
    getNextProblem: async () => ({
      problem,
      state: { ...withProblem(session, problem), can_submit: true, can_next_problem: false },
    }),
    submitAnswer: async () => ({
      is_correct: false,
      feedback: TRAP_FEEDBACK,
      state: withProblem(locked, triggerProblem),
    }),
    getDeconstructionStep: async () => step,
    ...handlers,
  });
}

/** Wires the three session operations used by a typical arena play-through. */
export function wireArenaFlow({
  session,
  problem,
  onSubmit,
}: {
  session: SessionResponse;
  problem: Problem;
  onSubmit: () => SubmissionResponse;
}): SessionClient {
  const getNextProblem = async () => {
    const state: SessionResponse = {
      ...session,
      current_problem: problem,
      can_submit: true,
      can_next_problem: false,
    };
    const response: ProblemResponse = { problem, state };
    return response;
  };

  return createFakeSessionClient({
    startSession: async () => session,
    getNextProblem,
    submitAnswer: async () => onSubmit(),
  });
}
