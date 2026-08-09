"""Shared pure navigation helpers used by resolution and snapshot modules."""

from __future__ import annotations

from backend.curriculum import Curriculum
from backend.curriculum_loader import TopicDict


def topics_for_chapter(curriculum: Curriculum, chapter_id: int) -> list[TopicDict]:
    return list(curriculum.topics(chapter_id))


def find_topic_by_id(
    curriculum: Curriculum, chapter_id: int, topic_id: int
) -> TopicDict | None:
    for topic_entry in curriculum.topics(chapter_id):
        if int(topic_entry["topic_id"]) == topic_id:
            return topic_entry
    return None


def clamp_level(
    level: int | None,
    curriculum: Curriculum,
    chapter_id: int,
    topic_id: int | None,
) -> int:
    """Return level capped to the topic's max_level (defensive for stale saves)."""
    effective = level if level is not None else 1
    if topic_id is None:
        return min(effective, 1)
    meta = curriculum.topic(chapter_id, topic_id)
    max_level = int(meta["max_level"]) if meta else 1
    return min(effective, max_level)


def get_level_options(level_limit_value: int) -> list[int]:
    return list(range(1, max(level_limit_value, 1) + 1))
