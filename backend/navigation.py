"""Navigation — snapshot, view, and intent resolution for session navigation."""

from __future__ import annotations

from dataclasses import dataclass

from backend.curriculum import Curriculum
from backend.curriculum_loader import ChapterSummary, TopicDict
from backend.models import (
    ChapterFrontier,
    NavigationChapterOption,
    NavigationProgress,
    NavigationTopicOption,
    NavigationView,
    SessionNavigateRequest,
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
        return _get_level_options(self.level_limit_for(topic_id, topic_max_level))

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
    chapter_summaries: tuple[ChapterSummary, ...]
    _state: SessionState
    _curriculum: Curriculum
    _play_mode: PlayMode

    def chapters(self) -> tuple[ChapterSummary, ...]:
        """Chapter list captured when this snapshot was built."""
        return self.chapter_summaries

    def chapter_context(self, chapter_id: int) -> ChapterNavigationContext:
        return _build_chapter_context(
            self._state,
            self._curriculum,
            self._play_mode,
            chapter_id,
        )


def _build_chapter_context(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode,
    chapter_id: int,
) -> ChapterNavigationContext:
    chapter_topics = _topics_for_chapter(curriculum, chapter_id)
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
    active_topic = (
        _find_topic_by_id(curriculum, selected_chapter_id, selected_topic_id)
        or (chapter_topics[0] if chapter_topics else None)
    )
    active_topic_id = (
        int(active_topic["topic_id"]) if active_topic is not None else None
    )
    selected_level = _clamp_level(
        state.selected_level, curriculum, selected_chapter_id, active_topic_id
    )
    current = _build_chapter_context(
        state, curriculum, play_mode, selected_chapter_id
    )
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

    radio_only = bool(
        snapshot.active_topic and snapshot.active_topic.get("radio_only")
    )

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


def clamp_selected_level(state: SessionState, curriculum: Curriculum) -> None:
    """Clamp session selected_level to the current topic's max_level."""
    chapter_id = state.selected_chapter_id
    if chapter_id is None:
        return
    chapter_topics = _topics_for_chapter(curriculum, chapter_id)
    if not chapter_topics:
        return
    first_topic_entry = chapter_topics[0]
    topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
    topic_entry = _find_topic_by_id(curriculum, chapter_id, topic_id) or first_topic_entry
    state.selected_level = _clamp_level(
        state.selected_level,
        curriculum,
        chapter_id,
        int(topic_entry["topic_id"]),
    )


def resolve_chapter_change(
    curriculum: Curriculum,
    next_chapter_id: int,
    snapshot: NavigationSnapshot,
) -> tuple[int, int, int]:
    """Pick default topic and level when switching chapter."""
    ctx = snapshot.chapter_context(next_chapter_id)
    next_topic_id, next_level = ctx.implicit_chapter_landing
    next_chapter_topics = _topics_for_chapter(curriculum, next_chapter_id)
    next_topic_entry = (
        _find_topic_by_id(curriculum, next_chapter_id, next_topic_id)
        or (next_chapter_topics[0] if next_chapter_topics else None)
    )
    next_topic_for_clamp = (
        int(next_topic_entry["topic_id"]) if next_topic_entry is not None else None
    )
    return (
        next_chapter_id,
        next_topic_id,
        _clamp_level(next_level, curriculum, next_chapter_id, next_topic_for_clamp),
    )


def resolve_topic_change(
    curriculum: Curriculum,
    chapter_id: int,
    next_topic_id: int,
    snapshot: NavigationSnapshot,
) -> tuple[int, int]:
    """Pick default level when switching topic within a chapter."""
    ctx = snapshot.chapter_context(chapter_id)
    next_level = ctx.implicit_topic_landing(next_topic_id)
    return next_topic_id, _clamp_level(
        next_level, curriculum, chapter_id, next_topic_id
    )


def resolve_navigate_request(
    state: SessionState,
    curriculum: Curriculum,
    request: SessionNavigateRequest,
    snapshot: NavigationSnapshot,
) -> tuple[int, int, int]:
    """Resolve partial navigation intents into a full chapter/topic/level target."""
    if (
        request.selected_chapter_id is not None
        and request.selected_chapter_id != state.selected_chapter_id
    ):
        return resolve_chapter_change(
            curriculum, request.selected_chapter_id, snapshot
        )

    chapter_id = request.selected_chapter_id or state.selected_chapter_id
    if chapter_id is None:
        chapter_ids = curriculum.chapter_ids()
        chapter_id = chapter_ids[0] if chapter_ids else 0

    chapter_topics = _topics_for_chapter(curriculum, chapter_id)

    if request.selected_topic_id is not None:
        topic_id, level = resolve_topic_change(
            curriculum, chapter_id, int(request.selected_topic_id), snapshot
        )
        if request.selected_level is not None:
            level = int(request.selected_level)
        return chapter_id, topic_id, level

    if request.selected_level is not None:
        topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
        return chapter_id, int(topic_id), int(request.selected_level)

    topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
    return chapter_id, int(topic_id), int(state.selected_level)
