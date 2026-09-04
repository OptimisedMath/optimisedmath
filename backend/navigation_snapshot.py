"""Navigation snapshot — read model builders for rendering session navigation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from backend.curriculum import Curriculum
from backend.curriculum_loader import ChapterSummary, TopicDict
from backend.models import (
    ChapterFrontier,
    NavigationChapterOption,
    NavigationProgress,
    NavigationTopicOption,
    NavigationView,
    SessionState,
)
from backend.play_mode import PlayMode
from backend.unlock import (
    Frontier,
    accessible_topics,
    is_reachable as unlock_can_access,
    first_topic_id,
    level_limit,
)


def _get_level_options(level_limit_value: int) -> list[int]:
    return list(range(1, max(level_limit_value, 1) + 1))


def _navigation_progress(completed: int, total: int) -> NavigationProgress:
    return NavigationProgress(
        completed=completed,
        total=total,
        percentage=(completed / total * 100) if total > 0 else 0.0,
    )


def _implicit_chapter_landing(
    is_admin: bool, chapter_topics: list[TopicDict], effective: Frontier
) -> tuple[int, int]:
    if is_admin:
        return first_topic_id(chapter_topics), 1
    return effective.frontier_topic_id, effective.frontier_level


def _implicit_topic_landing(is_admin: bool, topic_id: int, effective: Frontier) -> int:
    if is_admin or topic_id < effective.frontier_topic_id:
        return 1
    return effective.frontier_level


def _chapter_progress_counts(
    is_admin: bool, chapter_topics: list[TopicDict], effective: Frontier
) -> tuple[int, int]:
    total = len(chapter_topics)
    if is_admin:
        return total, total
    completed = sum(
        1
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) < effective.frontier_topic_id
    )
    return completed, total


def _topic_progress_counts(
    is_admin: bool, topic_max_level: int, selected_level: int
) -> tuple[int, int]:
    if is_admin:
        return topic_max_level, topic_max_level
    return selected_level - 1, topic_max_level


@dataclass(frozen=True, slots=True)
class ChapterNavigationContext:
    """Navigation read model for one chapter.

    Landing, progress, and unlock-visibility are derived once from
    ``resolve_frontier`` and ``is_admin`` when the context is built.
    """

    chapter_id: int
    chapter_topics: tuple[TopicDict, ...]
    resolve_frontier: Frontier
    accessible_topics: tuple[TopicDict, ...]
    implicit_chapter_landing: tuple[int, int]
    has_frontier_record: bool
    is_admin: bool
    _chapter_progress: NavigationProgress | None
    _implicit_topic_landings: dict[int, int]
    _next_unlocked_frontier_topic_id: int | None

    def level_limit_for(self, topic_id: int, topic_max_level: int) -> int:
        return level_limit(topic_id, topic_max_level, self.resolve_frontier)

    def level_options_for(self, topic_id: int, topic_max_level: int) -> list[int]:
        return _get_level_options(self.level_limit_for(topic_id, topic_max_level))

    def implicit_topic_landing(self, topic_id: int) -> int:
        stored = self._implicit_topic_landings.get(topic_id)
        if stored is not None:
            return stored
        return _implicit_topic_landing(self.is_admin, topic_id, self.resolve_frontier)

    def is_reachable(self, topic_id: int, level: int) -> bool:
        return unlock_can_access(topic_id, level, self.resolve_frontier)

    def chapter_progress(self) -> NavigationProgress | None:
        return self._chapter_progress

    def topic_progress(
        self, topic_id: int, selected_level: int
    ) -> NavigationProgress | None:
        topic_entry = next(
            (
                entry
                for entry in self.chapter_topics
                if int(entry["topic_id"]) == topic_id
            ),
            None,
        )
        if topic_entry is None:
            return None
        max_level = int(topic_entry["max_level"])
        completed, total = _topic_progress_counts(
            self.is_admin, max_level, selected_level
        )
        return _navigation_progress(completed, total)

    def has_next_unlocked_topic(self, selected_topic_id: int | None) -> bool:
        if self._next_unlocked_frontier_topic_id is None or selected_topic_id is None:
            return False
        return self._next_unlocked_frontier_topic_id > selected_topic_id


@dataclass(frozen=True, slots=True)
class NavigationSnapshot:
    """One immutable NavigationSnapshot per (state, mutation-epoch).

    Holds no live reference to a ``SessionState`` — every field a
    ``ChapterNavigationContext`` needs is copied at construction, and every
    Chapter's context is computed then, not on first access. Answers never
    move regardless of what the Session this value was built from does
    afterward, or which Chapter is asked about first.

    That immutability is why this value does not track the Session: a
    snapshot answers for the state as it stood when built, so once a
    use-case mutates that state the snapshot is stale by construction and
    the mutating use-case owes the response a fresh one. Two builds in one
    request is therefore correct, not redundant — see ``navigate_session``
    and ``next_problem`` in ``session.py``. See ADR-0003.
    """

    selected_chapter_id: int
    selected_topic_id: int
    selected_level: int
    selected_topic: TopicDict | None
    selected_chapter_context: ChapterNavigationContext
    chapter_summaries: tuple[ChapterSummary, ...]
    _curriculum: Curriculum
    _play_mode: PlayMode
    _chapter_frontiers: Mapping[int, ChapterFrontier]
    _chapter_contexts: Mapping[int, ChapterNavigationContext]

    def chapters(self) -> tuple[ChapterSummary, ...]:
        """Chapter list captured when this value was built."""
        return self.chapter_summaries

    def curriculum(self) -> Curriculum:
        """Curriculum this value was built from."""
        return self._curriculum

    def chapter_context(self, chapter_id: int) -> ChapterNavigationContext:
        """Return the chapter context computed for this value.

        Every Chapter in the Curriculum this value was built from has its
        context precomputed; a ``chapter_id`` outside the Curriculum (e.g. an
        unvalidated client request) falls back to a fresh empty-topics
        context derived from the same frozen inputs, still with no read of
        live Session state.
        """
        cached = self._chapter_contexts.get(chapter_id)
        if cached is not None:
            return cached
        return _build_chapter_context(
            self._chapter_frontiers,
            self._curriculum,
            self._play_mode,
            chapter_id,
        )


def _build_chapter_context(
    chapter_frontiers: Mapping[int, ChapterFrontier],
    curriculum: Curriculum,
    play_mode: PlayMode,
    chapter_id: int,
) -> ChapterNavigationContext:
    chapter_topics = list(curriculum.topics(chapter_id))
    frontier_record = chapter_frontiers.get(chapter_id)
    is_admin = play_mode.is_admin
    effective = play_mode.resolve_frontier(chapter_topics, frontier_record)
    accessible = tuple(accessible_topics(chapter_topics, effective))
    implicit_landing = _implicit_chapter_landing(is_admin, chapter_topics, effective)
    completed, total = _chapter_progress_counts(is_admin, chapter_topics, effective)
    has_frontier_record = chapter_id in chapter_frontiers
    implicit_topic_landings = {
        int(topic_entry["topic_id"]): _implicit_topic_landing(
            is_admin, int(topic_entry["topic_id"]), effective
        )
        for topic_entry in chapter_topics
    }
    next_unlocked_frontier_topic_id = (
        None if is_admin or not has_frontier_record else effective.frontier_topic_id
    )
    return ChapterNavigationContext(
        chapter_id=chapter_id,
        chapter_topics=tuple(chapter_topics),
        resolve_frontier=effective,
        accessible_topics=accessible,
        implicit_chapter_landing=implicit_landing,
        has_frontier_record=has_frontier_record,
        is_admin=is_admin,
        _chapter_progress=(
            _navigation_progress(completed, total) if chapter_topics else None
        ),
        _implicit_topic_landings=implicit_topic_landings,
        _next_unlocked_frontier_topic_id=next_unlocked_frontier_topic_id,
    )


def _build_all_chapter_contexts(
    chapter_frontiers: Mapping[int, ChapterFrontier],
    curriculum: Curriculum,
    play_mode: PlayMode,
    chapter_ids: tuple[int, ...],
) -> dict[int, ChapterNavigationContext]:
    return {
        chapter_id: _build_chapter_context(
            chapter_frontiers, curriculum, play_mode, chapter_id
        )
        for chapter_id in chapter_ids
    }


def build_navigation_snapshot(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode,
) -> NavigationSnapshot:
    """Build one immutable NavigationSnapshot from session state and Curriculum.

    Copies ``state.chapter_frontiers`` and computes every Chapter's context
    now, so the returned value holds no live reference into ``state`` and
    cannot see any mutation the caller makes to it afterward. Call this again
    after mutating ``state`` — the previous value still answers for the older
    state and will not follow the change.
    """
    chapter_frontiers = deepcopy(state.chapter_frontiers)
    chapter_ids = curriculum.chapter_ids()
    selected_chapter_id = state.selected_chapter_id or (
        chapter_ids[0] if chapter_ids else 0
    )
    chapter_topics = list(curriculum.topics(selected_chapter_id))
    default_topic_id = first_topic_id(chapter_topics)
    selected_topic_id = state.selected_topic_id or default_topic_id
    selected_topic = curriculum.topic_by_id(selected_chapter_id, selected_topic_id) or (
        chapter_topics[0] if chapter_topics else None
    )
    resolved_topic_id = (
        int(selected_topic["topic_id"]) if selected_topic is not None else None
    )
    selected_level = curriculum.clamp_level(
        state.selected_level, selected_chapter_id, resolved_topic_id
    )
    chapter_contexts = _build_all_chapter_contexts(
        chapter_frontiers, curriculum, play_mode, chapter_ids
    )
    selected_ctx = chapter_contexts.get(selected_chapter_id)
    if selected_ctx is None:
        selected_ctx = _build_chapter_context(
            chapter_frontiers, curriculum, play_mode, selected_chapter_id
        )
    return NavigationSnapshot(
        selected_chapter_id=selected_chapter_id,
        selected_topic_id=selected_topic_id,
        selected_level=selected_level,
        selected_topic=selected_topic,
        selected_chapter_context=selected_ctx,
        chapter_summaries=curriculum.chapters(),
        _curriculum=curriculum,
        _play_mode=play_mode,
        _chapter_frontiers=MappingProxyType(chapter_frontiers),
        _chapter_contexts=MappingProxyType(chapter_contexts),
    )


def build_navigation_view(nav: NavigationSnapshot) -> NavigationView:
    ctx = nav.selected_chapter_context
    available_chapters = [
        NavigationChapterOption(chapter_id=chapter.chapter_id, name=chapter.name)
        for chapter in nav.chapter_summaries
    ]

    available_topics_view = [
        NavigationTopicOption(
            topic_id=int(topic_entry["topic_id"]),
            name=str(topic_entry["name"]),
        )
        for topic_entry in ctx.accessible_topics
    ]

    available_levels = (
        ctx.level_options_for(
            nav.selected_topic_id,
            int(nav.selected_topic["max_level"]),
        )
        if nav.selected_topic
        else [1]
    )

    radio_only = bool(nav.selected_topic and nav.selected_topic.get("radio_only"))

    return NavigationView(
        available_chapters=available_chapters,
        current_topic_name=(
            str(nav.selected_topic["name"]) if nav.selected_topic else None
        ),
        available_topics=available_topics_view,
        available_levels=available_levels,
        has_next_unlocked_topic=ctx.has_next_unlocked_topic(nav.selected_topic_id),
        radio_only=radio_only,
        chapter_completion=ctx.chapter_progress(),
        topic_completion=ctx.topic_progress(nav.selected_topic_id, nav.selected_level),
    )
