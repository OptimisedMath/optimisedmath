"""Play mode policy — student vs admin adapters resolved once per request. For conventions see 'backend/docs/play-mode.md'"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import backend.config as config
from backend.curriculum_loader import TopicDict
from backend.models import ChapterFrontier
from backend.unlock import (
    Frontier,
    chapter_max_frontier,
    get_frontier,
)


class PlayMode(Protocol):
    """Resolved identity and policy for one session request."""

    @property
    def is_admin(self) -> bool: ...

    @property
    def persists_profile(self) -> bool: ...

    @property
    def reveals_correct_answer(self) -> bool: ...

    def resolve_frontier(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> Frontier: ...


@dataclass(frozen=True, slots=True)
class StudentPlayMode:
    """Normal student play — persisted Frontier, full profile writes."""

    is_admin: bool = False
    persists_profile: bool = True
    reveals_correct_answer: bool = False

    def resolve_frontier(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> Frontier:
        return get_frontier(frontier_record, chapter_topics)


@dataclass(frozen=True, slots=True)
class AdminPlayMode:
    """Admin QA play — effective full unlock, no profile progression writes."""

    is_admin: bool = True
    persists_profile: bool = False
    reveals_correct_answer: bool = True

    def resolve_frontier(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> Frontier:
        return chapter_max_frontier(chapter_topics)


@dataclass(frozen=True, slots=True)
class DbWritePlan:
    write_xp: bool
    write_streak: bool
    write_flawless_eligible: bool
    write_chapter_frontiers: bool
    profile_xp: int | None = None
    profile_streak: int | None = None
    profile_chapter_frontiers: dict[int, ChapterFrontier] | None = None

    @classmethod
    def write_all(cls) -> DbWritePlan:
        return cls(
            write_xp=True,
            write_streak=True,
            write_flawless_eligible=True,
            write_chapter_frontiers=True,
        )


def resolve_play_mode(username: str | None) -> PlayMode:
    """Resolve play mode from username once per session request."""
    if config.is_admin_user(username):
        return AdminPlayMode()
    return StudentPlayMode()
