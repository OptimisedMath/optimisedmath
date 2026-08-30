// Session types matching FastAPI Pydantic models (backend SessionResponse and related);
// note the backend also has its own SessionState class for persisted sessions, which this
// interface does not mirror.

export interface ChapterFrontier {
  frontier_topic_id: number;
  frontier_level: number;
}

export interface NavigationChapterOption {
  chapter_id: number;
  name: string;
}

export interface NavigationTopicOption {
  topic_id: number;
  name: string;
}

export interface NavigationProgress {
  completed: number;
  total: number;
  percentage: number;
}

export interface NavigationView {
  available_chapters: NavigationChapterOption[];
  current_topic_name: string | null;
  available_topics: NavigationTopicOption[];
  available_levels: number[];
  has_next_unlocked_topic: boolean;
  radio_only: boolean;
  chapter_completion: NavigationProgress | null;
  topic_completion: NavigationProgress | null;
}

export interface SessionResponse {
  session_id: string;
  username: string | null;
  xp: number;
  streak: number;
  flawless_eligible: boolean;
  max_streak: number;
  streak_meter: number;
  selected_chapter_id: number | null;
  selected_topic_id: number | null;
  selected_level: number;
  problem_answered: boolean;
  current_input_mode: string;
  topic_completed: boolean;
  feedback_type: string | null;
  feedback_msg: string;
  level_completed: boolean;
  chapter_frontiers: Record<number, ChapterFrontier>;
  current_problem: Problem | null;
  can_submit: boolean;
  can_next_problem: boolean;
  admin_mode?: boolean;
  navigation?: NavigationView | null;
}

export interface Problem {
  question: string;
  answer_options?: string[];
  correct_answer?: string;
  level: number;
  level_name: string;
  problem_id: string;
  level_display: string;
  keyboard_type?: string;
  image_html?: string;
}

export interface SessionStartRequest {
  username: string;
  selected_chapter_id?: number;
}

export interface SessionNavigateRequest {
  session_id: string;
  selected_chapter_id?: number;
  selected_topic_id?: number;
  selected_level?: number;
}

export interface SessionResetRequest {
  session_id: string;
}

export interface ProblemSubmissionRequest {
  session_id: string;
  user_input: string;
  problem_id?: string;
}

export interface ProblemResponse {
  problem: Problem;
  state: SessionResponse;
}

export interface SubmissionResponse {
  state: SessionResponse;
  is_correct: boolean;
  feedback: string;
}

export type DeconstructionStepInputType = 'typed' | 'ordering';

export interface DeconstructionStepResponse {
  question: string;
  working_line: string | null;
  step_index: number;
  total_steps: number;
  misconception_name: string;
  revealed_answer: string | null;
  input_type: DeconstructionStepInputType;
  items: string[] | null;
}

export interface DeconstructionSubmissionRequest {
  session_id: string;
  user_input: string;
}

export interface DeconstructionSubmissionResponse {
  is_correct: boolean;
  feedback_msg: string | null;
  handback_question: string | null;
}

export interface DeconstructionAbandonRequest {
  session_id: string;
}

export type FeedbackPhase = 'none' | 'soft_error' | 'answer_locked';

export interface Feedback {
  correct: boolean;
  message: string;
  feedback_type: string | null;
}

export type SubmitAnswerHandler = (answer: string) => void | Promise<void>;

export type NavigateIntent = Pick<
  SessionNavigateRequest,
  'selected_chapter_id' | 'selected_topic_id' | 'selected_level'
>;

/**
 * Local takeover phase — never persisted, never a game-rule outcome. 'pause' holds
 * the triggering Feedback on screen; 'intro'/'step'/'handback' are the full takeover.
 */
export type DeconstructionPhase = 'idle' | 'pause' | 'intro' | 'step' | 'handback';

export interface DeconstructionStepView {
  question: string;
  workingLine: string | null;
  stepIndex: number;
  totalSteps: number;
  revealedAnswer: string | null;
  inputType: DeconstructionStepInputType;
  items: string[] | null;
}

/** Render model for the takeover — a pure projection of DeconstructionStepResponse plus local phase. */
export interface DeconstructionView {
  phase: DeconstructionPhase;
  misconceptionName: string | null;
  headerQuestion: string | null;
  step: DeconstructionStepView | null;
  stepFeedback: string | null;
  handbackQuestion: string | null;
  isLoadingStep: boolean;
  isSubmittingStep: boolean;
}

export interface DeconstructionActions {
  endPause: () => void;
  begin: () => void;
  submitStep: (answer: string) => Promise<void>;
  exit: () => Promise<void>;
  returnToProblem: () => void;
}

/** Render model returned by useSession — arena children read slices of this. */
export interface SessionView {
  needsLogin: boolean;
  isLoading: boolean;
  error: string | null;
  isNavigating: boolean;
  isSubmitting: boolean;
  isLoadingNextProblem: boolean;
  canSubmit: boolean;
  feedbackPhase: FeedbackPhase;
  answerLocked: boolean;
  isLoadingProblem: boolean;
  problem: Problem | null;
  feedback: Feedback | null;
  selectedChapterName: string | null;
  topicName: string;
  adminMode: boolean;
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
  deconstruction: DeconstructionView;
}

/** Handlers returned by useSession — arena children call these for interactions. */
export interface SessionActions {
  submit: SubmitAnswerHandler;
  navigate: (intent: NavigateIntent) => Promise<void>;
  nextProblem: () => Promise<void>;
  reset: () => Promise<void>;
  clearErrorAndReload: () => void;
  deconstruction: DeconstructionActions;
}
