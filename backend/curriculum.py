"""Immutable Curriculum read model with a process-level provider override."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum_loader import (
    ChapterSummary,
    LevelConfig,
    TopicDict,
    TopicMeta,
    get_chapter_keyboard_type,
    get_chapter_yaml,
    get_chapters,
    get_curriculum,
    get_level_config,
    get_topics_by_id,
)

_curriculum_override: Curriculum | None = None


@dataclass(frozen=True, slots=True)
class Curriculum:
    """Read-only curriculum snapshot — Chapters, Topics and Levels."""

    _chapter_ids: tuple[int, ...]
    _chapter_names: dict[int, str]
    _topics: dict[int, tuple[TopicDict, ...]]
    _topics_by_id: dict[int, dict[int, TopicMeta]]
    _level_configs: dict[tuple[int, int, int], LevelConfig]
    _keyboard_types: dict[int, str]

    def chapter_ids(self) -> tuple[int, ...]:
        """Chapter ids in curriculum order."""
        return self._chapter_ids

    def chapters(self) -> tuple[ChapterSummary, ...]:
        """Chapter id plus display name pairs for Navigation dropdowns."""
        return tuple(
            ChapterSummary(chapter_id=chapter_id, name=self._chapter_names[chapter_id])
            for chapter_id in self._chapter_ids
        )

    def has_chapter(self, chapter_id: int) -> bool:
        """Return whether a Chapter id exists."""
        return chapter_id in self._chapter_names

    def topics(self, chapter_id: int) -> tuple[TopicDict, ...]:
        """Topics for a Chapter in curriculum order (published Topics only)."""
        return self._topics.get(chapter_id, ())

    def topic(self, chapter_id: int, topic_id: int) -> TopicMeta | None:
        """Topic lookup by id within a Chapter (name, max level, radio-only)."""
        return self._topics_by_id.get(chapter_id, {}).get(topic_id)

    def chapter_name(self, chapter_id: int) -> str | None:
        """Chapter display name by id."""
        return self._chapter_names.get(chapter_id)

    def topic_name(self, chapter_id: int, topic_id: int) -> str | None:
        """Topic display name by Chapter and id."""
        meta = self.topic(chapter_id, topic_id)
        return meta["name"] if meta else None

    def level_config(
        self, chapter_id: int, topic_id: int, level: int
    ) -> LevelConfig | None:
        """Level config for a Chapter, Topic and Level, including published state."""
        return self._level_configs.get((chapter_id, topic_id, level))

    def keyboard_type(self, chapter_id: int) -> str:
        """Keyboard type for a Chapter."""
        return self._keyboard_types.get(chapter_id, "default")


def curriculum_from_yaml() -> Curriculum:
    """Build a Curriculum from the YAML-backed loader (lru_cache stays in the loader)."""
    chapters = get_chapters()
    chapter_ids = tuple(chapter.chapter_id for chapter in chapters)
    chapter_names = {chapter.chapter_id: chapter.name for chapter in chapters}
    nav_curriculum = get_curriculum()

    topics: dict[int, tuple[TopicDict, ...]] = {}
    topics_by_id: dict[int, dict[int, TopicMeta]] = {}
    level_configs: dict[tuple[int, int, int], LevelConfig] = {}
    keyboard_types: dict[int, str] = {}

    for chapter_id in chapter_ids:
        topics[chapter_id] = tuple(nav_curriculum.get(chapter_id, []))
        topics_by_id[chapter_id] = get_topics_by_id(chapter_id)
        keyboard_types[chapter_id] = get_chapter_keyboard_type(chapter_id)
        for topic_entry in get_chapter_yaml(chapter_id).get("topics", []):
            topic_id = int(topic_entry["id"])
            for level_entry in topic_entry.get("levels", []):
                level = int(level_entry["level"])
                config = get_level_config(chapter_id, topic_id, level)
                if config is not None:
                    level_configs[(chapter_id, topic_id, level)] = config

    return Curriculum(
        _chapter_ids=chapter_ids,
        _chapter_names=chapter_names,
        _topics=topics,
        _topics_by_id=topics_by_id,
        _level_configs=level_configs,
        _keyboard_types=keyboard_types,
    )


def set_curriculum(curriculum: Curriculum | None) -> None:
    """Override the active Curriculum (same shape as set_function_registry)."""
    global _curriculum_override
    _curriculum_override = curriculum


def resolve_curriculum() -> Curriculum:
    """Return the active Curriculum — override if set, otherwise YAML-backed."""
    if _curriculum_override is not None:
        return _curriculum_override
    return curriculum_from_yaml()
