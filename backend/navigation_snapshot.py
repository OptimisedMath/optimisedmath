"""Immutable navigation snapshot read model — one per request."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum_loader import TopicDict, get_chapters
from backend.models import ChapterFrontier, NavigationProgress, SessionState
from backend.navigation_helpers import (
    clamp_level,
    find_topic_by_id,
    get_level_options,
    topics_for_chapter,
)
from backend.play_mode import PlayMode
from backend.unlock import (
    Frontier,
    accessible_topics,
    can_access as unlock_can_access,
    first_topic_id,
    level_limit,
)


@dataclass(frozen=True, slots=True)
class ChapterNavigationContext:
    """Navigation read model for one chapter — admin fork applied at build time."""

    chapter_id: int
    chapter_topics: tuple[TopicDict, ...]
    effective_frontier: Frontier
    accessible_topics: tuple[TopicDict, ...]
    implicit_chapter_landing: tuple[int, int]
    is_admin: bool
    has_frontier_record: bool
    _play_mode: PlayMode
    _frontier_record: ChapterFrontier | None

    def level_limit_for(self, topic_id: int, topic_max_level: int) -> int:
        return level_limit(topic_id, topic_max_level, self.effective_frontier)

    def level_options_for(self, topic_id: int, topic_max_level: int) -> list[int]:
        return get_level_options(self.level_limit_for(topic_id, topic_max_level))

    def implicit_topic_landing(self, topic_id: int) -> int:
        return self._play_mode.implicit_topic_landing(
            list(self.chapter_topics), topic_id, self._frontier_record
        )

    def can_access(self, topic_id: int, level: int) -> bool:
        return unlock_can_access(topic_id, level, self.effective_frontier)

    def chapter_progress(self) -> NavigationProgress | None:
        if not self.chapter_topics:
            return None
        total = len(self.chapter_topics)
        if self.is_admin:
            return NavigationProgress(completed=total, total=total, percentage=100.0)
        completed = sum(
            1
            for topic_entry in self.chapter_topics
            if int(topic_entry["topic_id"]) < self.effective_frontier.frontier_topic_id
        )
        return NavigationProgress(
            completed=completed,
            total=total,
            percentage=(completed / total * 100) if total > 0 else 0.0,
        )

    def topic_progress(
        self, topic_id: int, selected_level: int
    ) -> NavigationProgress | None:
        topic_entry = find_topic_by_id(list(self.chapter_topics), topic_id)
        if topic_entry is None:
            return None
        max_level = int(topic_entry["max_level"])
        if self.is_admin:
            return NavigationProgress(
                completed=max_level,
                total=max_level,
                percentage=100.0,
            )
        completed_levels = selected_level - 1
        return NavigationProgress(
            completed=completed_levels,
            total=max_level,
            percentage=(completed_levels / max_level * 100) if max_level > 0 else 0.0,
        )

    def has_next_unlocked_topic(self, selected_topic_id: int | None) -> bool:
        if self.is_admin:
            return False
        if not self.has_frontier_record or selected_topic_id is None:
            return False
        return self.effective_frontier.frontier_topic_id > selected_topic_id


@dataclass(frozen=True, slots=True)
class NavigationSnapshot:
    """One immutable navigation snapshot per request."""

    selected_chapter_id: int
    selected_topic_id: int
    selected_level: int
    active_topic: TopicDict | None
    current: ChapterNavigationContext
    _state: SessionState
    _curriculum: dict[int, list[TopicDict]]
    _play_mode: PlayMode

    def chapter_context(self, chapter_id: int) -> ChapterNavigationContext:
        return _build_chapter_context(
            self._state,
            self._curriculum,
            self._play_mode,
            chapter_id,
        )


def _build_chapter_context(
    state: SessionState,
    curriculum: dict[int, list[TopicDict]],
    play_mode: PlayMode,
    chapter_id: int,
) -> ChapterNavigationContext:
    chapter_topics = topics_for_chapter(curriculum, chapter_id)
    frontier_record = state.chapter_frontiers.get(chapter_id)
    effective = play_mode.effective_frontier(chapter_topics, frontier_record)
    accessible = tuple(accessible_topics(chapter_topics, effective))
    implicit_landing = play_mode.implicit_chapter_landing(chapter_topics, frontier_record)
    return ChapterNavigationContext(
        chapter_id=chapter_id,
        chapter_topics=tuple(chapter_topics),
        effective_frontier=effective,
        accessible_topics=accessible,
        implicit_chapter_landing=implicit_landing,
        is_admin=play_mode.is_admin,
        has_frontier_record=chapter_id in state.chapter_frontiers,
        _play_mode=play_mode,
        _frontier_record=frontier_record,
    )


def build_navigation_snapshot(
    state: SessionState,
    curriculum: dict[int, list[TopicDict]],
    play_mode: PlayMode,
) -> NavigationSnapshot:
    """Build one immutable navigation snapshot from session state and play mode."""
    chapter_summaries = get_chapters()
    selected_chapter_id = state.selected_chapter_id or (
        chapter_summaries[0].chapter_id if chapter_summaries else 0
    )
    chapter_topics = topics_for_chapter(curriculum, selected_chapter_id)
    default_topic_id = first_topic_id(chapter_topics)
    selected_topic_id = state.selected_topic_id or default_topic_id
    active_topic = (
        find_topic_by_id(chapter_topics, selected_topic_id)
        or (chapter_topics[0] if chapter_topics else None)
    )
    selected_level = clamp_level(state.selected_level, active_topic)
    current = _build_chapter_context(
        state, curriculum, play_mode, selected_chapter_id
    )
    return NavigationSnapshot(
        selected_chapter_id=selected_chapter_id,
        selected_topic_id=selected_topic_id,
        selected_level=selected_level,
        active_topic=active_topic,
        current=current,
        _state=state,
        _curriculum=curriculum,
        _play_mode=play_mode,
    )
