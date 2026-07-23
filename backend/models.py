"""Pydantic models for the Math Learning API and session state."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

import backend.config as config


def heal_legacy_state(data: dict) -> dict:
    """Normalize legacy dict keys from older saves into current field names."""
    healed = dict(data)

    if "selected_topic_order" in healed and "selected_micro_topic_order" not in healed:
        healed["selected_micro_topic_order"] = healed.pop("selected_topic_order")

    if "unlocked_order" in healed and "unlocked_micro_topic_order" not in healed:
        healed["unlocked_micro_topic_order"] = healed.pop("unlocked_order")

    progress = healed.get("progress")
    if isinstance(progress, dict):
        for macro, prog in progress.items():
            if isinstance(prog, dict):
                progress[macro] = heal_legacy_state(prog)

    return healed


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

    can_submit: bool = False
    can_advance: bool = False
    admin_mode: bool = Field(
        default=False,
        description="Whether the user has admin privileges (all topics + auto-solve)",
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
        """Build a GameState from persisted JSON, healing legacy keys."""
        healed = heal_legacy_state(data)
        progress = {}
        for macro, prog_data in healed.get("progress", {}).items():
            if isinstance(prog_data, dict):
                progress[macro] = TopicProgress(**heal_legacy_state(prog_data))
            else:
                progress[macro] = prog_data
        healed["progress"] = progress
        return cls.model_validate(healed)

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
        if not isinstance(copy.show_celebration, bool):
            if isinstance(copy.show_celebration, str):
                copy.show_celebration = copy.show_celebration.lower() == "true"
            else:
                copy.show_celebration = False
        copy.problem_start_time = None
        copy.admin_mode = config.is_admin_user(copy.username)
        return copy


class SessionStartRequest(BaseModel):
    username: str
    selected_macro: Optional[str] = None


class SessionNavigateRequest(BaseModel):
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
    session_id: str
    user_input: str
    is_text_mode: bool = False
    problem_id: Optional[str] = None


class CurriculumTopic(BaseModel):
    micro_topic_order: int
    name: str
    max_level: int
    text_mode_disabled: bool = False


class CurriculumResponse(BaseModel):
    macro_topics: list[str]
    topics: Dict[str, list[CurriculumTopic]]


class ProblemResponse(BaseModel):
    problem: Dict[str, Any]
    state: GameState


class SubmissionResponse(BaseModel):
    state: GameState
    is_correct: bool
    feedback: str
