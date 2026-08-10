"""Immutable Curriculum read model with a process-level provider override."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum_loader import (
    ChapterSummary,
    CurriculumStore,
    LevelConfig,
    TopicDict,
    TopicMeta,
    load_curriculum_store,
)
from backend.models import ChapterSummary as ChapterSummaryResponse
from backend.models import CurriculumResponse, TopicSummary

_curriculum_override: Curriculum | None = None


@dataclass(frozen=True, slots=True)
class Curriculum:
    """Read-only curriculum snapshot — Chapters, Topics and Levels.

    Delegates lookups to the wrapped `CurriculumStore` instead of
    re-deriving its own indexes.
    """

    _store: CurriculumStore

    def chapter_ids(self) -> tuple[int, ...]:
        """Chapter ids in curriculum order."""
        return tuple(bundle.chapter_id for bundle in self._store.bundles)

    def chapters(self) -> tuple[ChapterSummary, ...]:
        """Chapter id plus display name pairs for Navigation dropdowns."""
        return tuple(self._store.chapters)

    def has_chapter(self, chapter_id: int) -> bool:
        """Return whether a Chapter id exists."""
        return chapter_id in self._store.bundles_by_chapter_id

    def topics(self, chapter_id: int) -> tuple[TopicDict, ...]:
        """Topics for a Chapter in curriculum order (published Topics only)."""
        bundle = self._store.bundles_by_chapter_id.get(chapter_id)
        return bundle.topics_meta if bundle is not None else ()

    def topic(self, chapter_id: int, topic_id: int) -> TopicMeta | None:
        """Topic lookup by id within a Chapter (name, max level, radio-only)."""
        bundle = self._store.bundles_by_chapter_id.get(chapter_id)
        return bundle.topics_by_id.get(topic_id) if bundle is not None else None

    def chapter_name(self, chapter_id: int) -> str | None:
        """Chapter display name by id."""
        return self._store.chapter_name_by_id.get(chapter_id)

    def topic_name(self, chapter_id: int, topic_id: int) -> str | None:
        """Topic display name by Chapter and id."""
        meta = self.topic(chapter_id, topic_id)
        return meta["name"] if meta else None

    def level_config(
        self, chapter_id: int, topic_id: int, level: int
    ) -> LevelConfig | None:
        """Level config for a Chapter, Topic and Level, including published state."""
        bundle = self._store.bundles_by_chapter_id.get(chapter_id)
        return bundle.level_configs.get((topic_id, level)) if bundle is not None else None

    def keyboard_type(self, chapter_id: int) -> str:
        """Keyboard type for a Chapter."""
        bundle = self._store.bundles_by_chapter_id.get(chapter_id)
        return bundle.keyboard_type if bundle is not None else "default"


def curriculum_from_yaml() -> Curriculum:
    """Build a Curriculum wrapping the YAML-backed store (lru_cache stays in the loader)."""
    return Curriculum(_store=load_curriculum_store())


def set_curriculum(curriculum: Curriculum | None) -> None:
    """Override the active Curriculum (same shape as set_function_registry)."""
    global _curriculum_override
    _curriculum_override = curriculum


def resolve_curriculum() -> Curriculum:
    """Return the active Curriculum — override if set, otherwise YAML-backed."""
    if _curriculum_override is not None:
        return _curriculum_override
    return curriculum_from_yaml()


def get_curriculum_response(curriculum: Curriculum) -> CurriculumResponse:
    """Return curriculum metadata formatted for the API."""
    chapters: list[ChapterSummaryResponse] = []
    for chapter in curriculum.chapters():
        topic_list = curriculum.topics(chapter.chapter_id)
        chapters.append(
            ChapterSummaryResponse(
                chapter_id=chapter.chapter_id,
                name=chapter.name,
                topics=[TopicSummary(**topic_entry) for topic_entry in topic_list],
            )
        )
    return CurriculumResponse(chapters=chapters)
