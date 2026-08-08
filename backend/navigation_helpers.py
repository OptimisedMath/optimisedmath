"""Shared pure navigation helpers used by resolution and snapshot modules."""

from __future__ import annotations

from backend.curriculum_loader import TopicDict


def topics_for_chapter(
    curriculum: dict[int, list[TopicDict]], chapter_id: int
) -> list[TopicDict]:
    return curriculum.get(chapter_id, [])


def find_topic_by_id(
    chapter_topics: list[TopicDict], topic_id: int
) -> TopicDict | None:
    for topic_entry in chapter_topics:
        if int(topic_entry["topic_id"]) == topic_id:
            return topic_entry
    return None


def clamp_level(level: int | None, topic_entry: TopicDict | None) -> int:
    """Return level capped to the topic's max_level (defensive for stale saves)."""
    effective = level if level is not None else 1
    max_level = int(topic_entry["max_level"]) if topic_entry else 1
    return min(effective, max_level)


def get_level_options(level_limit_value: int) -> list[int]:
    return list(range(1, max(level_limit_value, 1) + 1))
