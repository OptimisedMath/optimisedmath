"""Navigation snapshot — read model builders for rendering session navigation."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.curriculum import Curriculum
from backend.curriculum_loader import ChapterSummary, TopicDict
from backend.models import (
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
    can_access as unlock_can_access,
    first_topic_id,
    level_limit,
)


def _topics_for_chapter(curriculum: Curriculum, chapter_id: int) -> list[TopicDict]:
    return list(curriculum.topics(chapter_id))


def _find_topic_by_id(
    curriculum: Curriculum, chapter_id: int, topic_id: int
) -> TopicDict | None:
    for topic_entry in curriculum.topics(chapter_id):
        if int(topic_entry["topic_id"]) == topic_id:
            return topic_entry
    return None


def _clamp_level(
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
    ``effective_frontier`` and ``is_admin`` when the context is built.
    """

    chapter_id: int
    chapter_topics: tuple[TopicDict, ...]
    effective_frontier: Frontier
    accessible_topics: tuple[TopicDict, ...]
    implicit_chapter_landing: tuple[int, int]
    has_frontier_record: bool
    is_admin: bool
    _chapter_progress: NavigationProgress | None
    _implicit_topic_landings: dict[int, int]
    _next_unlocked_frontier_topic_id: int | None

    def level_limit_for(self, topic_id: int, topic_max_level: int) -> int:
        return level_limit(topic_id, topic_max_level, self.effective_frontier)

    def level_options_for(self, topic_id: int, topic_max_level: int) -> list[int]:
        return _get_level_options(self.level_limit_for(topic_id, topic_max_level))

    def implicit_topic_landing(self, topic_id: int) -> int:
        stored = self._implicit_topic_landings.get(topic_id)
        if stored is not None:
            return stored
        return _implicit_topic_landing(self.is_admin, topic_id, self.effective_frontier)

    def can_access(self, topic_id: int, level: int) -> bool:
        return unlock_can_access(topic_id, level, self.effective_frontier)

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
    """One immutable navigation snapshot per request."""

    selected_chapter_id: int
    selected_topic_id: int
    selected_level: int
    active_topic: TopicDict | None
    current: ChapterNavigationContext
    chapter_summaries: tuple[ChapterSummary, ...]
    _state: SessionState
    _curriculum: Curriculum
    _play_mode: PlayMode
    _context_cache: dict[int, ChapterNavigationContext] = field(
        default_factory=dict, repr=False, compare=False
    )

    def chapters(self) -> tuple[ChapterSummary, ...]:
        """Chapter list captured when this snapshot was built."""
        return self.chapter_summaries

    def curriculum(self) -> Curriculum:
        """Curriculum this snapshot was built from."""
        return self._curriculum

    def chapter_context(self, chapter_id: int) -> ChapterNavigationContext:
        """Return the chapter context, memoized per chapter_id for this snapshot."""
        cached = self._context_cache.get(chapter_id)
        if cached is not None:
            return cached
        context = _build_chapter_context(
            self._state,
            self._curriculum,
            self._play_mode,
            chapter_id,
        )
        self._context_cache[chapter_id] = context
        return context


def _build_chapter_context(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode,
    chapter_id: int,
) -> ChapterNavigationContext:
    chapter_topics = _topics_for_chapter(curriculum, chapter_id)
    frontier_record = state.chapter_frontiers.get(chapter_id)
    is_admin = play_mode.is_admin
    effective = play_mode.effective_frontier(chapter_topics, frontier_record)
    accessible = tuple(accessible_topics(chapter_topics, effective))
    implicit_landing = _implicit_chapter_landing(is_admin, chapter_topics, effective)
    completed, total = _chapter_progress_counts(is_admin, chapter_topics, effective)
    has_frontier_record = chapter_id in state.chapter_frontiers
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
        effective_frontier=effective,
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


def build_navigation_snapshot(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode,
) -> NavigationSnapshot:
    """Build one immutable navigation snapshot from session state and Curriculum."""
    chapter_ids = curriculum.chapter_ids()
    selected_chapter_id = state.selected_chapter_id or (
        chapter_ids[0] if chapter_ids else 0
    )
    chapter_topics = _topics_for_chapter(curriculum, selected_chapter_id)
    default_topic_id = first_topic_id(chapter_topics)
    selected_topic_id = state.selected_topic_id or default_topic_id
    active_topic = _find_topic_by_id(
        curriculum, selected_chapter_id, selected_topic_id
    ) or (chapter_topics[0] if chapter_topics else None)
    active_topic_id = (
        int(active_topic["topic_id"]) if active_topic is not None else None
    )
    selected_level = _clamp_level(
        state.selected_level, curriculum, selected_chapter_id, active_topic_id
    )
    current = _build_chapter_context(state, curriculum, play_mode, selected_chapter_id)
    return NavigationSnapshot(
        selected_chapter_id=selected_chapter_id,
        selected_topic_id=selected_topic_id,
        selected_level=selected_level,
        active_topic=active_topic,
        current=current,
        chapter_summaries=curriculum.chapters(),
        _state=state,
        _curriculum=curriculum,
        _play_mode=play_mode,
    )


def build_navigation_view(snapshot: NavigationSnapshot) -> NavigationView:
    """Map a navigation snapshot to the API NavigationView DTO."""
    ctx = snapshot.current
    available_chapters = [
        NavigationChapterOption(chapter_id=chapter.chapter_id, name=chapter.name)
        for chapter in snapshot.chapter_summaries
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
            snapshot.selected_topic_id,
            int(snapshot.active_topic["max_level"]),
        )
        if snapshot.active_topic
        else [1]
    )

    radio_only = bool(snapshot.active_topic and snapshot.active_topic.get("radio_only"))

    return NavigationView(
        available_chapters=available_chapters,
        current_topic_name=(
            str(snapshot.active_topic["name"]) if snapshot.active_topic else None
        ),
        available_topics=available_topics_view,
        available_levels=available_levels,
        has_next_unlocked_topic=ctx.has_next_unlocked_topic(snapshot.selected_topic_id),
        radio_only=radio_only,
        chapter_completion=ctx.chapter_progress(),
        topic_completion=ctx.topic_progress(
            snapshot.selected_topic_id, snapshot.selected_level
        ),
    )
