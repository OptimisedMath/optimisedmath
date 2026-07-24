// TypeScript types matching FastAPI Pydantic models

export interface TopicProgress {
  unlocked_micro_topic_order: number;
  unlocked_level: number;
}

export interface NavigationMicroTopicOption {
  micro_topic_order: number;
  name: string;
}

export interface NavigationProgress {
  completed: number;
  total: number;
  percentage: number;
}

export interface NavigationView {
  macro_topics: string[];
  current_topic_name: string | null;
  available_micro_topics: NavigationMicroTopicOption[];
  available_levels: number[];
  has_next_unlocked_topic: boolean;
  text_mode_disabled: boolean;
  macro_progress: NavigationProgress | null;
  micro_progress: NavigationProgress | null;
}

export interface GameState {
  session_id: string;
  username: string | null;
  xp: number;
  streak: number;
  flawless_eligible: boolean;
  max_streak: number;
  selected_macro: string | null;
  selected_micro_topic_order: number | null;
  selected_level: number;
  problem_answered: boolean;
  current_input_mode: string;
  topic_completed: boolean;
  feedback_type: string | null;
  feedback_msg: string;
  show_celebration: boolean;
  progress: Record<string, TopicProgress>;
  current_problem: Problem | null;
  can_submit: boolean;
  can_advance: boolean;
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
  input_mode?: string;
  image_html?: string;
}

export interface CurriculumTopic {
  micro_topic_order: number;
  name: string;
  max_level: number;
  text_mode_disabled?: boolean;
}

export interface CurriculumResponse {
  macro_topics: string[];
  topics: Record<string, CurriculumTopic[]>;
}

export interface SessionStartRequest {
  username: string;
  selected_macro?: string;
}

export interface SessionNavigateRequest {
  session_id: string;
  selected_macro?: string;
  selected_micro_topic_order?: number;
  selected_level?: number;
}

export interface SessionResetRequest {
  session_id: string;
}

export interface ProblemSubmissionRequest {
  session_id: string;
  user_input: string;
  is_text_mode: boolean;
  problem_id?: string;
}

export interface AutoSolveRequest {
  session_id: string;
  problem_id?: string;
}

export interface ProblemResponse {
  problem: Problem;
  state: GameState;
}

export interface SubmissionResponse {
  state: GameState;
  is_correct: boolean;
  feedback: string;
}

export interface Feedback {
  correct: boolean;
  message: string;
  feedback_type: string;
  is_locked: boolean;
}

export type SubmitAnswerHandler = (answer: string) => void | Promise<void>;
