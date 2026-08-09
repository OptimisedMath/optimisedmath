"""Immutable Curriculum read model with a process-level provider override."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum_loader import (
    ChapterSummary,
    LevelConfig,
    TopicDict,
    TopicMeta,
    load_curriculum_store,
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
    store = load_curriculum_store()
    chapter_ids = tuple(bundle.chapter_id for bundle in store.bundles)
    chapter_names = {bundle.chapter_id: bundle.chapter_name for bundle in store.bundles}
    topics: dict[int, tuple[TopicDict, ...]] = {
        bundle.chapter_id: bundle.topics_meta for bundle in store.bundles
    }
    topics_by_id: dict[int, dict[int, TopicMeta]] = {
        bundle.chapter_id: dict(bundle.topics_by_id) for bundle in store.bundles
    }
    keyboard_types: dict[int, str] = {
        bundle.chapter_id: bundle.keyboard_type for bundle in store.bundles
    }
    level_configs: dict[tuple[int, int, int], LevelConfig] = {
        (bundle.chapter_id, topic_id, level): config
        for bundle in store.bundles
        for (topic_id, level), config in bundle.level_configs.items()
    }

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
