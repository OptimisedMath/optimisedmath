"""Pydantic models for the Math Learning API and session state."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

import backend.config as config
from backend.curriculum_loader import get_chapter_id_by_name

# --- Progress & navigation ---


class ChapterProgress(BaseModel):
    """Progress for a single chapter."""

    unlocked_topic_id: int = Field(
        default=1,
        description="Highest topic id unlocked for this chapter",
    )
    unlocked_level: int = Field(
        default=1,
        description="Highest level unlocked for the current topic",
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
    """Completed vs total counts for chapter or topic progress bars."""

    completed: int
    total: int
    percentage: float


class NavigationView(BaseModel):
    """Computed navigation state attached to every GameState API response."""

    available_chapters: list[NavigationChapterOption]
    current_topic_name: Optional[str] = None
    available_topics: list[NavigationTopicOption]
    available_levels: list[int]
    has_next_unlocked_topic: bool
    text_mode_disabled: bool
    chapter_progress: Optional[NavigationProgress] = None
    topic_progress: Optional[NavigationProgress] = None


# --- Session state ---


class GameState(BaseModel):
    """Mutable session state used by StateManager and API responses."""

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
    show_celebration: bool = False

    chapter_progress: Dict[int, ChapterProgress] = Field(default_factory=dict)

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
        description="Whether the user has admin privileges (all chapters + auto-solve)",
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
                "selected_chapter_id": 10,
                "selected_topic_id": 20,
                "selected_level": 2,
                "problem_answered": False,
                "current_input_mode": "radio",
                "topic_completed": False,
                "feedback_type": None,
                "feedback_msg": "",
                "show_celebration": False,
                "chapter_progress": {
                    10: {
                        "unlocked_topic_id": 30,
                        "unlocked_level": 2,
                    },
                },
            }
        }
    )

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_storage(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        data = dict(data)

        if "progress" in data and "chapter_progress" not in data:
            data["chapter_progress"] = data.pop("progress")

        if "macro_progress" in data and "chapter_progress" not in data:
            raw_progress = data.pop("macro_progress")
            migrated: dict[int, ChapterProgress] = {}
            for key, value in raw_progress.items():
                chapter_id: int | None
                if isinstance(key, int):
                    chapter_id = key
                elif isinstance(key, str):
                    chapter_id = get_chapter_id_by_name(key)
                else:
                    continue
                if chapter_id is None:
                    continue
                if isinstance(value, dict):
                    unlocked_topic_id = value.get("unlocked_topic_id")
                    if unlocked_topic_id is None:
                        unlocked_topic_id = value.get("unlocked_micro_topic_order", 1)
                    migrated[chapter_id] = ChapterProgress(
                        unlocked_topic_id=int(unlocked_topic_id),
                        unlocked_level=int(value.get("unlocked_level", 1)),
                    )
                else:
                    migrated[chapter_id] = value
            data["chapter_progress"] = migrated

        if "selected_chapter_id" not in data:
            if "selected_macro_id" in data:
                data["selected_chapter_id"] = data.pop("selected_macro_id")
            elif "selected_macro" in data and data["selected_macro"]:
                chapter_id = get_chapter_id_by_name(str(data.pop("selected_macro")))
                if chapter_id is not None:
                    data["selected_chapter_id"] = chapter_id

        if "selected_topic_id" not in data:
            if "selected_micro_id" in data:
                data["selected_topic_id"] = data.pop("selected_micro_id")
            elif "selected_micro_topic_order" in data:
                data["selected_topic_id"] = data.pop("selected_micro_topic_order")

        if "chapter_progress" in data and isinstance(data["chapter_progress"], dict):
            chapter_progress = data["chapter_progress"]
            needs_migration = any(
                isinstance(entry, dict) and "unlocked_micro_topic_order" in entry
                for entry in chapter_progress.values()
            )
            if needs_migration:
                migrated_progress: dict[int, ChapterProgress] = {}
                for key, value in chapter_progress.items():
                    chapter_id = int(key) if not isinstance(key, int) else key
                    if isinstance(value, dict):
                        unlocked_topic_id = value.get(
                            "unlocked_topic_id",
                            value.get("unlocked_micro_topic_order", 1),
                        )
                        migrated_progress[chapter_id] = ChapterProgress(
                            unlocked_topic_id=int(unlocked_topic_id),
                            unlocked_level=int(value.get("unlocked_level", 1)),
                        )
                    else:
                        migrated_progress[chapter_id] = value
                data["chapter_progress"] = migrated_progress

        return data

    @classmethod
    def from_storage(cls, data: dict) -> GameState:
        """Build a GameState from persisted JSON."""
        return cls.model_validate(data)

    def to_storage(self) -> str:
        """Serialize session state for SQLite persistence."""
        return self.model_dump_json(exclude={"navigation"})

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
    is_text_mode: bool = False
    problem_id: Optional[str] = None


# --- Response models ---


class TopicSummary(BaseModel):
    """One topic in the curriculum index response."""

    topic_id: int
    name: str
    max_level: int
    text_mode_disabled: bool = False


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
    state: GameState


class SubmissionResponse(BaseModel):
    """Grading outcome plus updated session state."""

    state: GameState
    is_correct: bool
    feedback: str
