"""Play mode policy — student vs admin adapters resolved once per request.

Admin mode (`AdminPlayMode`) is QA/debug access for designated Usernames,
invisible to normal Students. It has no Frontier of its own — Frontier is a
Student-only concept — so it substitutes **effective full unlock**
(`chapter_max_frontier`) everywhere a Frontier would otherwise be read or
written, without touching the stored Frontier on the profile. Normal
navigation access rules still apply against that effective full unlock;
there is no separate admin navigation bypass elsewhere in the codebase.
Implicit navigation defaults (chapter-only or topic-only changes) land at
the start of the target (first Topic, level 1) rather than at a Frontier
position; explicit Topic/Level picks are unchanged.

Every Submission still runs the normal grade → progression → respond
pipeline (see `session.py`) and telemetry still logs, but
`persists_profile = False` means XP, Flawless, and Frontier advances are
never written back to the profile, and progress bars render fully
complete. Session streak still runs in-cycle (radio → input mode, wrong
answers decrement) for a realistic feel, but is never persisted — navigation
still resets it. Admin auto-solve in the UI is a visible shortcut through
that same Submission pipeline: the client selects or types the correct
answer, then calls `/problem/submit`. `session.auto_solve_problem` and
`/problem/auto-solve` are dev-tools-only shortcuts that skip the UI fill
step; the frontend does not call them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import backend.config as config
from backend.curriculum_loader import TopicDict
from backend.models import ChapterFrontier
from backend.unlock import (
    Frontier,
    chapter_max_frontier,
    first_topic_id,
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

    def effective_frontier(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> Frontier: ...

    def implicit_chapter_landing(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> tuple[int, int]: ...

    def implicit_topic_landing(
        self,
        chapter_topics: list[TopicDict],
        topic_id: int,
        frontier_record: ChapterFrontier | None,
    ) -> int: ...

    def chapter_progress_counts(
        self,
        chapter_topics: list[TopicDict],
        effective_frontier: Frontier,
    ) -> tuple[int, int]: ...

    def topic_progress_counts(
        self,
        topic_max_level: int,
        selected_level: int,
    ) -> tuple[int, int]: ...

    def has_next_unlocked_topic(
        self,
        effective_frontier: Frontier,
        has_frontier_record: bool,
        selected_topic_id: int | None,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class StudentPlayMode:
    """Normal student play — persisted Frontier, full profile writes."""

    is_admin: bool = False
    persists_profile: bool = True
    reveals_correct_answer: bool = False

    def effective_frontier(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> Frontier:
        return get_frontier(frontier_record, chapter_topics)

    def implicit_chapter_landing(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> tuple[int, int]:
        frontier = get_frontier(frontier_record, chapter_topics)
        return frontier.frontier_topic_id, frontier.frontier_level

    def implicit_topic_landing(
        self,
        chapter_topics: list[TopicDict],
        topic_id: int,
        frontier_record: ChapterFrontier | None,
    ) -> int:
        frontier = get_frontier(frontier_record, chapter_topics)
        if topic_id < frontier.frontier_topic_id:
            return 1
        return frontier.frontier_level

    def chapter_progress_counts(
        self,
        chapter_topics: list[TopicDict],
        effective_frontier: Frontier,
    ) -> tuple[int, int]:
        total = len(chapter_topics)
        completed = sum(
            1
            for topic_entry in chapter_topics
            if int(topic_entry["topic_id"]) < effective_frontier.frontier_topic_id
        )
        return completed, total

    def topic_progress_counts(
        self,
        topic_max_level: int,
        selected_level: int,
    ) -> tuple[int, int]:
        return selected_level - 1, topic_max_level

    def has_next_unlocked_topic(
        self,
        effective_frontier: Frontier,
        has_frontier_record: bool,
        selected_topic_id: int | None,
    ) -> bool:
        if not has_frontier_record or selected_topic_id is None:
            return False
        return effective_frontier.frontier_topic_id > selected_topic_id


@dataclass(frozen=True, slots=True)
class AdminPlayMode:
    """Admin QA play — effective full unlock, no profile progression writes."""

    is_admin: bool = True
    persists_profile: bool = False
    reveals_correct_answer: bool = True

    def effective_frontier(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> Frontier:
        return chapter_max_frontier(chapter_topics)

    def implicit_chapter_landing(
        self,
        chapter_topics: list[TopicDict],
        frontier_record: ChapterFrontier | None,
    ) -> tuple[int, int]:
        return first_topic_id(chapter_topics), 1

    def implicit_topic_landing(
        self,
        chapter_topics: list[TopicDict],
        topic_id: int,
        frontier_record: ChapterFrontier | None,
    ) -> int:
        return 1

    def chapter_progress_counts(
        self,
        chapter_topics: list[TopicDict],
        effective_frontier: Frontier,
    ) -> tuple[int, int]:
        total = len(chapter_topics)
        return total, total

    def topic_progress_counts(
        self,
        topic_max_level: int,
        selected_level: int,
    ) -> tuple[int, int]:
        return topic_max_level, topic_max_level

    def has_next_unlocked_topic(
        self,
        effective_frontier: Frontier,
        has_frontier_record: bool,
        selected_topic_id: int | None,
    ) -> bool:
        return False


def resolve_play_mode(username: str | None) -> PlayMode:
    """Resolve play mode from username once per session request."""
    if config.is_admin_user(username):
        return AdminPlayMode()
    return StudentPlayMode()
