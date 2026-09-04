"""Pydantic models for the Math Learning API and session state."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Progress & navigation ---


class ChapterFrontier(BaseModel):
    frontier_topic_id: int = Field(
        default=1,
        description="Frontier topic id — furthest Topic earned in this chapter",
    )
    frontier_level: int = Field(
        default=1,
        description="Frontier level — furthest Level earned at the frontier topic",
    )


class NavigationChapterOption(BaseModel):
    chapter_id: int
    name: str


class NavigationTopicOption(BaseModel):
    topic_id: int
    name: str


class NavigationProgress(BaseModel):
    completed: int
    total: int
    percentage: float


class NavigationView(BaseModel):
    available_chapters: list[NavigationChapterOption]
    current_topic_name: Optional[str] = None
    available_topics: list[NavigationTopicOption]
    available_levels: list[int]
    has_next_unlocked_topic: bool
    radio_only: bool
    chapter_completion: Optional[NavigationProgress] = None
    topic_completion: Optional[NavigationProgress] = None


# --- Session state ---


# Wire mirror of `deconstruction.StepInputType`, redeclared rather than imported so
# `models.py` stays the shared leaf every layer may import (import rule 2).
DeconstructionStepInputType = Literal["typed", "ordering"]


class DeconstructionStep(BaseModel):
    """One computed walkthrough question, mirroring `deconstruction.Step`."""

    question: str
    working_line: Optional[str] = None
    answer: str
    input_type: DeconstructionStepInputType = "typed"
    items: Optional[list[str]] = None


class DeconstructionState(BaseModel):
    misconception_slug: str
    steps: list[DeconstructionStep]
    step_index: int = 0
    step_attempts: int = 0
    step_revealed: bool = False
    deconstruction_id: Optional[int] = Field(
        default=None,
        description="Row id of the `deconstructions` header, for updating deconstruction_steps",
    )


class SessionState(BaseModel):
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

    deconstruction: Optional[DeconstructionState] = Field(
        default=None,
        description="The Deconstruction taking over the Session right now, if any",
    )
    deconstructed: list[str] = Field(
        default_factory=list,
        description=(
            "(Misconception, Level) pairs already deconstructed this Session — "
            "deliberately not folded into the per-Level hit counter, which Level "
            "changes reset"
        ),
    )
    discounted_problem_id: Optional[str] = Field(
        default=None,
        description="Problem available for a second, discounted-XP attempt after completion",
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
        },
    )

    def to_storage(self) -> str:
        return self.model_dump_json(include=set(SessionState.model_fields))


class SessionResponse(BaseModel):
    """Client Session payload — composed from `SessionState` plus derived response view.

    Shared persisted fields are copied in `from_state()`; derived view fields are
    passed explicitly by `session.build_session_response()`. Persisted-only fields (e.g.
    `problem_start_time`, `recent_problem_fingerprints`) never leak onto the wire when
    a new persisted field is added unless it is also wired through `from_state()`.
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
    can_next_problem: bool = False
    deconstruction_running: bool = Field(
        default=False,
        description=(
            "Whether a Deconstruction is taking over the Session right now. The "
            "client arms its takeover off this flag rather than inferring one from "
            "a withheld `correct_answer` (ADR-0002: the backend names the state it "
            "owns)"
        ),
    )
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

    @classmethod
    def from_state(
        cls,
        state: SessionState,
        *,
        current_problem: Optional[Dict[str, Any]],
        can_submit: bool,
        can_next_problem: bool,
        streak_meter: int,
        admin_mode: bool,
        navigation: Optional[NavigationView],
    ) -> SessionResponse:
        return cls(
            session_id=state.session_id,
            username=state.username,
            xp=state.xp,
            streak=state.streak,
            flawless_eligible=state.flawless_eligible,
            max_streak=state.max_streak,
            selected_chapter_id=state.selected_chapter_id,
            selected_topic_id=state.selected_topic_id,
            selected_level=state.selected_level,
            problem_answered=state.problem_answered,
            current_input_mode=state.current_input_mode,
            topic_completed=state.topic_completed,
            feedback_type=state.feedback_type,
            feedback_msg=state.feedback_msg,
            level_completed=state.level_completed,
            chapter_frontiers=deepcopy(state.chapter_frontiers),
            current_problem=current_problem,
            can_submit=can_submit,
            can_next_problem=can_next_problem,
            deconstruction_running=state.deconstruction is not None,
            streak_meter=streak_meter,
            admin_mode=admin_mode,
            navigation=navigation,
        )


# --- Request models ---


class SessionStartRequest(BaseModel):
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
    session_id: str
    user_input: str
    problem_id: Optional[str] = None


class DeconstructionSubmissionRequest(BaseModel):
    session_id: str
    user_input: str


class DeconstructionAbandonRequest(BaseModel):
    """End the running Deconstruction via its exit control, forfeiting the retry."""

    session_id: str


# --- Response models ---


class TopicSummary(BaseModel):
    topic_id: int
    name: str
    max_level: int
    radio_only: bool = False


class ChapterSummary(BaseModel):
    chapter_id: int
    name: str
    topics: list[TopicSummary]


class CurriculumResponse(BaseModel):
    chapters: list[ChapterSummary]


class ProblemResponse(BaseModel):
    problem: Dict[str, Any]
    state: SessionResponse


class SubmissionResponse(BaseModel):
    state: SessionResponse
    is_correct: bool
    feedback: str


class DeconstructionStepResponse(BaseModel):
    """Current Deconstruction step's wire payload for `GET /deconstruction/next`.

    `working_line: None` is load-bearing — some Misconceptions author no working line.
    `revealed_answer` is populated only once the Reveal threshold is hit, and the
    Student still has to type it in to advance.
    """

    question: str
    working_line: Optional[str] = None
    step_index: int
    total_steps: int
    misconception_name: str
    revealed_answer: Optional[str] = None
    input_type: DeconstructionStepInputType = "typed"
    items: Optional[list[str]] = None


class DeconstructionSubmissionResponse(BaseModel):
    """Grading outcome for one Deconstruction step submission.

    No attempt counter on the wire (ADR-0004) — a visible "one try left" makes
    the walkthrough feel like a test. `handback_question` carries the original
    Problem's question text, and is populated only on the submission that
    completes the final step — Handback has no separate endpoint.
    """

    is_correct: bool
    feedback_msg: Optional[str] = None
    handback_question: Optional[str] = None
