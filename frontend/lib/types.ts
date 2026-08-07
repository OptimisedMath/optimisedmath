// Curriculum catalog types matching FastAPI Pydantic models.

export interface TopicSummary {
  topic_id: number;
  name: string;
  max_level: number;
  radio_only?: boolean;
}

export interface ChapterSummary {
  chapter_id: number;
  name: string;
  topics: TopicSummary[];
}

export interface CurriculumResponse {
  chapters: ChapterSummary[];
}
