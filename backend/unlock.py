"""Chapter/Topic/Level UnlockedProgress — read gates and write advances."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum_loader import TopicDict
from backend.models import ChapterProgress


@dataclass(frozen=True)
class UnlockedProgress:
    """Highest Topic and Level a student may reach in one Chapter."""

    unlocked_topic_id: int
    unlocked_level: int


@dataclass(frozen=True)
class AdvanceResult:
    """UnlockedProgress changes when a Level is mastered at the current boundary."""

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


def get_unlocked_progress(
    progress: ChapterProgress | None,
    chapter_topics: list[TopicDict],
) -> UnlockedProgress:
    """Resolve UnlockedProgress for a chapter, defaulting safely for missing progress."""
    default_topic = first_topic_id(chapter_topics)
    if progress is None:
        return UnlockedProgress(unlocked_topic_id=default_topic, unlocked_level=1)
    return UnlockedProgress(
        unlocked_topic_id=progress.unlocked_topic_id,
        unlocked_level=progress.unlocked_level,
    )


def can_access(
    topic_id: int,
    level: int,
    unlocked_progress: UnlockedProgress,
    *,
    admin_mode: bool = False,
) -> bool:
    """Return whether a chapter/topic/level target is within UnlockedProgress."""
    if admin_mode:
        return True
    if topic_id > unlocked_progress.unlocked_topic_id:
        return False
    if (
        topic_id == unlocked_progress.unlocked_topic_id
        and level > unlocked_progress.unlocked_level
    ):
        return False
    return True


def level_limit(
    topic_id: int,
    topic_max_level: int,
    unlocked_progress: UnlockedProgress,
    *,
    admin_mode: bool = False,
) -> int:
    """Return the highest selectable level for a topic given UnlockedProgress."""
    if admin_mode or topic_id < unlocked_progress.unlocked_topic_id:
        return topic_max_level
    return min(unlocked_progress.unlocked_level, topic_max_level)


def accessible_topics(
    chapter_topics: list[TopicDict],
    unlocked_progress: UnlockedProgress,
    *,
    admin_mode: bool = False,
) -> list[TopicDict]:
    """Return topics visible in navigation dropdowns for the current UnlockedProgress."""
    if admin_mode:
        available = chapter_topics
    else:
        available = [
            topic_entry
            for topic_entry in chapter_topics
            if int(topic_entry["topic_id"]) <= unlocked_progress.unlocked_topic_id
        ]
    if available:
        return available
    return chapter_topics[:1]


def advance_on_mastery(
    unlocked_level: int,
    topic_max_level: int,
    next_topic_ids: tuple[int, ...],
) -> AdvanceResult:
    """Advance UnlockedProgress after streak mastery at the current boundary."""
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
