"""Pydantic models for the Math Learning API and session state."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

import backend.config as config

# --- Progress & navigation ---


class TopicProgress(BaseModel):
    """Progress for a single macro topic."""

    unlocked_micro_topic_order: int = Field(
        default=1,
        description="Highest micro-topic order unlocked for this macro topic",
    )
    unlocked_level: int = Field(
        default=1,
        description="Highest level unlocked for the current micro-topic",
    )


class NavigationMicroTopicOption(BaseModel):
    """One micro-topic entry in navigation dropdowns."""

    micro_topic_order: int
    name: str


class NavigationProgress(BaseModel):
    """Completed vs total counts for macro or micro progress bars."""

    completed: int
    total: int
    percentage: float


class NavigationView(BaseModel):
    """Computed navigation state attached to every GameState API response."""

    macro_topics: list[str]
    current_topic_name: Optional[str] = None
    available_micro_topics: list[NavigationMicroTopicOption]
    available_levels: list[int]
    has_next_unlocked_topic: bool
    text_mode_disabled: bool
    macro_progress: Optional[NavigationProgress] = None
    micro_progress: Optional[NavigationProgress] = None


# --- Session state ---


class GameState(BaseModel):
    """Mutable session state used by StateManager and API responses."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: Optional[str] = None

    xp: int = Field(default=0, ge=0)
    streak: int = Field(default=0, ge=0)
    flawless_eligible: bool = True
    max_streak: int = Field(default=3, ge=1)

    selected_macro: Optional[str] = None
    selected_micro_topic_order: Optional[int] = None
    selected_level: int = Field(default=1, ge=1)

    problem_answered: bool = False
    current_input_mode: str = "radio"
    topic_completed: bool = False

    feedback_type: Optional[str] = None
    feedback_msg: str = ""
    show_celebration: bool = False

    progress: Dict[str, TopicProgress] = Field(default_factory=dict)

    current_problem: Optional[Dict[str, Any]] = None
    problem_start_time: Optional[float] = None
    recent_problem_fingerprints: list[str] = Field(
        default_factory=list,
        description="Recent generated problem fingerprints for duplicate avoidance",
    )

    can_submit: bool = False
    can_advance: bool = False
    admin_mode: bool = Field(
        default=False,
        description="Whether the user has admin privileges (all topics + auto-solve)",
    )
    navigation: Optional[NavigationView] = Field(
        default=None,
        description="Computed UI navigation state (API responses only, not persisted)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "student123",
                "xp": 1500,
                "streak": 3,
                "flawless_eligible": True,
                "selected_macro": "Ułamki Zwykłe",
                "selected_micro_topic_order": 20,
                "selected_level": 2,
                "problem_answered": False,
                "current_input_mode": "radio",
                "topic_completed": False,
                "feedback_type": None,
                "feedback_msg": "",
                "show_celebration": False,
                "progress": {
                    "Ułamki Zwykłe": {
                        "unlocked_micro_topic_order": 30,
                        "unlocked_level": 2,
                    },
                },
            }
        }
    )

    @classmethod
    def from_storage(cls, data: dict) -> GameState:
        """Build a GameState from persisted JSON."""
        return cls.model_validate(data)

    def for_response(
        self,
        public_problem_fn: Callable[[Dict[str, Any], GameState], Dict[str, Any]],
    ) -> GameState:
        """Return a copy suitable for API serialization without mutating session state."""
        copy = deepcopy(self)
        if copy.current_problem:
            copy.current_problem = public_problem_fn(copy.current_problem, copy)
        copy.can_submit = bool(copy.current_problem and not copy.problem_answered)
        copy.can_advance = bool(copy.problem_answered)
        copy.problem_start_time = None
        copy.recent_problem_fingerprints = []
        copy.admin_mode = config.is_admin_user(copy.username)
        return copy


# --- Request models ---


class SessionStartRequest(BaseModel):
    """Start or resume a session for a username."""

    username: str
    selected_macro: Optional[str] = None


class SessionNavigateRequest(BaseModel):
    """Partial navigation intent; omitted fields keep current selection."""

    session_id: str
    selected_macro: Optional[str] = None
    selected_micro_topic_order: Optional[int] = None
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
    is_text_mode: bool = False
    problem_id: Optional[str] = None


# --- Response models ---


class CurriculumTopic(BaseModel):
    """One micro-topic in the curriculum index response."""

    micro_topic_order: int
    name: str
    max_level: int
    text_mode_disabled: bool = False


class CurriculumResponse(BaseModel):
    """Full curriculum metadata for macro and micro topics."""

    macro_topics: list[str]
    micro_topics: Dict[str, list[CurriculumTopic]]


class ProblemResponse(BaseModel):
    """Next problem payload plus updated session state."""

    problem: Dict[str, Any]
    state: GameState


class SubmissionResponse(BaseModel):
    """Grading outcome plus updated session state."""

    state: GameState
    is_correct: bool
    feedback: str
