"""Chapter/Topic/Level Frontier — read gates and write advances."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum_loader import TopicDict
from backend.models import ChapterFrontier


@dataclass(frozen=True)
class Frontier:
    """Highest Topic and Level a student may reach in one Chapter."""

    frontier_topic_id: int
    frontier_level: int


@dataclass(frozen=True)
class AdvanceResult:
    """Frontier changes when a Level is mastered at the current boundary."""

    level_unlocked: bool = False
    topic_completed: bool = False
    new_frontier_level: int | None = None
    unlock_topic_id: int | None = None
    new_selected_level: int | None = None


def first_topic_id(chapter_topics: list[TopicDict]) -> int:
    """Return the first topic id in curriculum list order."""
    if chapter_topics:
        return int(chapter_topics[0]["topic_id"])
    return 1


def get_frontier(
    frontier_record: ChapterFrontier | None,
    chapter_topics: list[TopicDict],
) -> Frontier:
    """Resolve the Frontier for a chapter, defaulting safely for missing progress."""
    default_topic = first_topic_id(chapter_topics)
    if frontier_record is None:
        return Frontier(frontier_topic_id=default_topic, frontier_level=1)
    return Frontier(
        frontier_topic_id=frontier_record.frontier_topic_id,
        frontier_level=frontier_record.frontier_level,
    )


def chapter_max_frontier(chapter_topics: list[TopicDict]) -> Frontier:
    """Return the Frontier at the last topic and its max level in curriculum order."""
    if not chapter_topics:
        return Frontier(frontier_topic_id=1, frontier_level=1)
    last_topic = chapter_topics[-1]
    return Frontier(
        frontier_topic_id=int(last_topic["topic_id"]),
        frontier_level=int(last_topic["max_level"]),
    )


def can_access(
    topic_id: int,
    level: int,
    frontier: Frontier,
) -> bool:
    """Return whether a chapter/topic/level target is within the Frontier."""
    if topic_id > frontier.frontier_topic_id:
        return False
    if (
        topic_id == frontier.frontier_topic_id
        and level > frontier.frontier_level
    ):
        return False
    return True


def level_limit(
    topic_id: int,
    topic_max_level: int,
    frontier: Frontier,
) -> int:
    """Return the highest selectable level for a topic given the Frontier."""
    if topic_id < frontier.frontier_topic_id:
        return topic_max_level
    return min(frontier.frontier_level, topic_max_level)


def accessible_topics(
    chapter_topics: list[TopicDict],
    frontier: Frontier,
) -> list[TopicDict]:
    """Return topics visible in navigation dropdowns for the current Frontier."""
    available = [
        topic_entry
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) <= frontier.frontier_topic_id
    ]
    if available:
        return available
    return chapter_topics[:1]


def advance_on_mastery(
    frontier_level: int,
    topic_max_level: int,
    next_topic_ids: tuple[int, ...],
) -> AdvanceResult:
    """Advance the Frontier after streak mastery at the current boundary."""
    if frontier_level < topic_max_level:
        new_level = frontier_level + 1
        return AdvanceResult(
            level_unlocked=True,
            new_frontier_level=new_level,
            new_selected_level=new_level,
        )

    if next_topic_ids:
        return AdvanceResult(
            topic_completed=True,
            unlock_topic_id=next_topic_ids[0],
            new_frontier_level=1,
        )

    return AdvanceResult(topic_completed=True)
