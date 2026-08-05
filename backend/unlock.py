"""Chapter/Topic/Level unlock frontier — read gates and write advances."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum_loader import TopicDict
from backend.models import ChapterProgress


@dataclass(frozen=True)
class UnlockFrontier:
    """Highest Topic and Level a student may reach in one Chapter."""

    unlocked_topic_id: int
    unlocked_level: int


@dataclass(frozen=True)
class AdvanceResult:
    """Frontier changes when a Level is mastered at the unlock boundary."""

    level_unlocked: bool = False
    topic_completed: bool = False
    new_unlocked_level: int | None = None
    unlock_topic_id: int | None = None
    new_selected_level: int | None = None


def first_topic_id(chapter_topics: list[TopicDict]) -> int:
    """Return the first topic id in curriculum list order."""
    if chapter_topics:
        return int(chapter_topics[0]["topic_id"])
    return 1


def get_frontier(
    progress: ChapterProgress | None,
    chapter_topics: list[TopicDict],
) -> UnlockFrontier:
    """Resolve the unlock frontier for a chapter, defaulting safely for missing progress."""
    default_topic = first_topic_id(chapter_topics)
    if progress is None:
        return UnlockFrontier(unlocked_topic_id=default_topic, unlocked_level=1)
    return UnlockFrontier(
        unlocked_topic_id=progress.unlocked_topic_id,
        unlocked_level=progress.unlocked_level,
    )


def can_access(
    topic_id: int,
    level: int,
    frontier: UnlockFrontier,
    *,
    admin_mode: bool = False,
) -> bool:
    """Return whether a chapter/topic/level target is within the unlock frontier."""
    if admin_mode:
        return True
    if topic_id > frontier.unlocked_topic_id:
        return False
    if topic_id == frontier.unlocked_topic_id and level > frontier.unlocked_level:
        return False
    return True


def level_limit(
    topic_id: int,
    topic_max_level: int,
    frontier: UnlockFrontier,
    *,
    admin_mode: bool = False,
) -> int:
    """Return the highest selectable level for a topic given the frontier."""
    if admin_mode or topic_id < frontier.unlocked_topic_id:
        return topic_max_level
    return min(frontier.unlocked_level, topic_max_level)


def accessible_topics(
    chapter_topics: list[TopicDict],
    frontier: UnlockFrontier,
    *,
    admin_mode: bool = False,
) -> list[TopicDict]:
    """Return topics visible in navigation dropdowns for the current frontier."""
    if admin_mode:
        available = chapter_topics
    else:
        available = [
            topic_entry
            for topic_entry in chapter_topics
            if int(topic_entry["topic_id"]) <= frontier.unlocked_topic_id
        ]
    if available:
        return available
    return chapter_topics[:1]


def advance_on_mastery(
    unlocked_level: int,
    topic_max_level: int,
    next_topic_ids: tuple[int, ...],
) -> AdvanceResult:
    """Advance the unlock frontier after Power of 3 mastery at the current boundary."""
    if unlocked_level < topic_max_level:
        new_level = unlocked_level + 1
        return AdvanceResult(
            level_unlocked=True,
            new_unlocked_level=new_level,
            new_selected_level=new_level,
        )

    if next_topic_ids:
        return AdvanceResult(
            topic_completed=True,
            unlock_topic_id=next_topic_ids[0],
            new_unlocked_level=1,
        )

    return AdvanceResult(topic_completed=True)
