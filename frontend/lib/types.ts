// TypeScript types matching FastAPI Pydantic models

export interface ChapterProgress {
  unlocked_topic_id: number;
  unlocked_level: number;
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
  text_mode_disabled: boolean;
  chapter_progress: NavigationProgress | null;
  topic_progress: NavigationProgress | null;
}

export interface GameState {
  session_id: string;
  username: string | null;
  xp: number;
  streak: number;
  flawless_eligible: boolean;
  max_streak: number;
  selected_chapter_id: number | null;
  selected_topic_id: number | null;
  selected_level: number;
  problem_answered: boolean;
  current_input_mode: string;
  topic_completed: boolean;
  feedback_type: string | null;
  feedback_msg: string;
  show_celebration: boolean;
  chapter_progress: Record<number, ChapterProgress>;
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

export interface TopicSummary {
  topic_id: number;
  name: string;
  max_level: number;
  text_mode_disabled?: boolean;
}

export interface ChapterSummary {
  chapter_id: number;
  name: string;
  topics: TopicSummary[];
}

export interface CurriculumResponse {
  chapters: ChapterSummary[];
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
