"""Pydantic models for the Math Learning API and session state."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Progress & navigation ---


class ChapterFrontier(BaseModel):
    """Persisted Frontier for a single chapter on the student profile."""

    frontier_topic_id: int = Field(
        default=1,
        description="Frontier topic id — furthest Topic earned in this chapter",
    )
    frontier_level: int = Field(
        default=1,
        description="Frontier level — furthest Level earned at the frontier topic",
    )


class NavigationChapterOption(BaseModel):
    """One chapter entry in navigation dropdowns."""

    chapter_id: int
    name: str


class NavigationTopicOption(BaseModel):
    """One topic entry in navigation dropdowns."""

    topic_id: int
    name: str


class NavigationProgress(BaseModel):
    """Completed vs total counts for chapter or topic completion meters."""

    completed: int
    total: int
    percentage: float


class NavigationView(BaseModel):
    """Computed navigation state attached to every SessionResponse."""

    available_chapters: list[NavigationChapterOption]
    current_topic_name: Optional[str] = None
    available_topics: list[NavigationTopicOption]
    available_levels: list[int]
    has_next_unlocked_topic: bool
    radio_only: bool
    chapter_completion: Optional[NavigationProgress] = None
    topic_completion: Optional[NavigationProgress] = None


# --- Session state ---


class SessionState(BaseModel):
    """Persisted Session — identity, progression, selection, submission cycle, Frontier, problem plumbing."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: Optional[str] = None

    xp: int = Field(default=0, ge=0)
    streak: int = Field(default=0, ge=0)
    flawless_eligible: bool = True
    max_streak: int = Field(default=3, ge=1)

    selected_chapter_id: Optional[int] = None
    selected_topic_id: Optional[int] = None
    selected_level: int = Field(default=1, ge=1)

    problem_answered: bool = False
    current_input_mode: str = "radio"
    topic_completed: bool = False

    feedback_type: Optional[str] = None
    feedback_msg: str = ""
    level_completed: bool = False

    chapter_frontiers: Dict[int, ChapterFrontier] = Field(default_factory=dict)

    current_problem: Optional[Dict[str, Any]] = None
    problem_start_time: Optional[float] = None
    recent_problem_fingerprints: list[str] = Field(
        default_factory=list,
        description="Recent generated problem fingerprints for duplicate avoidance",
    )

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "student123",
                "xp": 1500,
                "streak": 3,
                "flawless_eligible": True,
                "selected_chapter_id": 10,
                "selected_topic_id": 20,
                "selected_level": 2,
                "problem_answered": False,
                "current_input_mode": "radio",
                "topic_completed": False,
                "feedback_type": None,
                "feedback_msg": "",
                "level_completed": False,
                "chapter_frontiers": {
                    "10": {
                        "frontier_topic_id": 30,
                        "frontier_level": 2,
                    },
                },
            }
        }
    )

    def to_storage(self) -> str:
        """Serialize persisted Session fields for SQLite."""
        return self.model_dump_json(include=set(SessionState.model_fields))


class SessionResponse(BaseModel):
    """Client Session payload — composed from `SessionState` plus derived response view.

    Fields are opt-in (selected explicitly by `session.respond()`), not inherited from
    the persisted `SessionState` superset, so persisted-only fields (e.g.
    `problem_start_time`, `recent_problem_fingerprints`) never leak onto the wire by
    default when a new persisted field is added.
    """

    session_id: str
    username: Optional[str] = None

    xp: int = Field(default=0, ge=0)
    streak: int = Field(default=0, ge=0)
    flawless_eligible: bool = True
    max_streak: int = Field(default=3, ge=1)

    selected_chapter_id: Optional[int] = None
    selected_topic_id: Optional[int] = None
    selected_level: int = Field(default=1, ge=1)

    problem_answered: bool = False
    current_input_mode: str = "radio"
    topic_completed: bool = False

    feedback_type: Optional[str] = None
    feedback_msg: str = ""
    level_completed: bool = False

    chapter_frontiers: Dict[int, ChapterFrontier] = Field(default_factory=dict)

    current_problem: Optional[Dict[str, Any]] = None

    can_submit: bool = False
    can_advance: bool = False
    streak_meter: int = Field(
        default=0,
        ge=0,
        description="Streak meter display value for the star UI (API responses only)",
    )
    admin_mode: bool = Field(
        default=False,
        description="Whether the user has admin privileges (all chapters + auto-solve)",
    )
    navigation: Optional[NavigationView] = Field(
        default=None,
        description="Computed UI navigation state (API responses only, not persisted)",
    )


# --- Request models ---


class SessionStartRequest(BaseModel):
    """Start or resume a session for a username."""

    username: str
    selected_chapter_id: Optional[int] = None


class SessionNavigateRequest(BaseModel):
    """Partial navigation intent; omitted fields keep current selection."""

    session_id: str
    selected_chapter_id: Optional[int] = None
    selected_topic_id: Optional[int] = None
    selected_level: Optional[int] = Field(default=None, ge=1)


class SessionResetRequest(BaseModel):
    session_id: str


class AutoSolveRequest(BaseModel):
    session_id: str
    problem_id: Optional[str] = None


class ProblemSubmissionRequest(BaseModel):
    """Submit an answer for the active problem in a session."""

    session_id: str
    user_input: str
    is_input_mode: bool = False
    problem_id: Optional[str] = None


# --- Response models ---


class TopicSummary(BaseModel):
    """One topic in the curriculum index response."""

    topic_id: int
    name: str
    max_level: int
    radio_only: bool = False


class ChapterSummary(BaseModel):
    """One chapter in the curriculum index response."""

    chapter_id: int
    name: str
    topics: list[TopicSummary]


class CurriculumResponse(BaseModel):
    """Full curriculum metadata for chapters and topics."""

    chapters: list[ChapterSummary]


class ProblemResponse(BaseModel):
    """Next problem payload plus updated session state."""

    problem: Dict[str, Any]
    state: SessionResponse


class SubmissionResponse(BaseModel):
    """Grading outcome plus updated session state."""

    state: SessionResponse
    is_correct: bool
    feedback: str
