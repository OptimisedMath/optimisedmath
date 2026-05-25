// TypeScript types matching FastAPI Pydantic models

export interface TopicProgress {
  unlocked_order: number;
  unlocked_level: number;
}

export interface GameState {
  session_id: string;
  username: string | null;
  xp: number;
  streak: number;
  flawless_eligible: boolean;
  max_streak: number;
  selected_macro: string | null;
  selected_topic_order: number | null;
  selected_level: number;
  problem_answered: boolean;
  current_input_mode: string;
  topic_completed: boolean;
  feedback_type: string | null;
  feedback_msg: string;
  show_balloons: boolean;
  progress: Record<string, TopicProgress>;
  current_problem: Problem | null;
}

export interface Problem {
  question: string;
  correct: string;
  options?: string[];
  options_map?: Record<string, string>;
  messages?: {
    t1: string;
    t2: string;
    t3: string;
  };
  level: number;
  level_name: string;
  problem_id: string;
  level_display: string;
  grading_policy?: string;
  keyboard_type?: string;
  input_mode?: string;
  image_html?: string;
}

export interface CurriculumTopic {
  order: number;
  name: string;
  max_level: number;
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
  selected_topic_order?: number;
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
}
