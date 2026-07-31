"""Curriculum navigation rules and UI-ready navigation state for API responses."""

from __future__ import annotations

import backend.state_manager as state_manager
from backend.curriculum_loader import TopicDict, get_chapters
from backend.models import (
    GameState,
    NavigationChapterOption,
    NavigationProgress,
    NavigationTopicOption,
    NavigationView,
    SessionNavigateRequest,
)

# --- Private helpers ---


def _topics_for_chapter(
    curriculum: dict[int, list[TopicDict]], chapter_id: int
) -> list[TopicDict]:
    return curriculum.get(chapter_id, [])


def _find_topic_by_id(
    chapter_topics: list[TopicDict], topic_id: int
) -> TopicDict | None:
    for topic_entry in chapter_topics:
        if int(topic_entry["topic_id"]) == topic_id:
            return topic_entry
    return None


def _first_topic_id(chapter_topics: list[TopicDict]) -> int:
    if chapter_topics:
        return int(chapter_topics[0]["topic_id"])
    return 1


def _get_unlocked(
    state: GameState, chapter_id: int, chapter_topics: list[TopicDict]
) -> tuple[int, int]:
    progress = state.chapter_progress.get(chapter_id)
    first_topic_id = _first_topic_id(chapter_topics)
    unlocked_topic_id = progress.unlocked_topic_id if progress else first_topic_id
    unlocked_level = progress.unlocked_level if progress else 1
    return unlocked_topic_id, unlocked_level


def _clamp_level(level: int | None, topic_entry: TopicDict | None) -> int:
    """Return level capped to the topic's max_level (defensive for stale saves)."""
    effective = level if level is not None else 1
    max_level = int(topic_entry["max_level"]) if topic_entry else 1
    return min(effective, max_level)


def clamp_selected_level(
    state: GameState, curriculum: dict[int, list[TopicDict]]
) -> None:
    """Clamp session selected_level to the current topic's max_level."""
    chapter_id = state.selected_chapter_id
    if chapter_id is None:
        return
    chapter_topics = _topics_for_chapter(curriculum, chapter_id)
    if not chapter_topics:
        return
    first_topic_entry = chapter_topics[0]
    topic_id = state.selected_topic_id or _first_topic_id(chapter_topics)
    topic_entry = _find_topic_by_id(chapter_topics, topic_id) or first_topic_entry
    state.selected_level = _clamp_level(state.selected_level, topic_entry)


# --- Dropdown builders ---


def get_topic_options(
    chapter_topics: list[TopicDict], unlocked_topic_id: int, admin_mode: bool
) -> list[TopicDict]:
    """Return topics available in dropdowns, filtered by unlock progress."""
    if admin_mode:
        available = chapter_topics
    else:
        available = [
            topic_entry
            for topic_entry in chapter_topics
            if int(topic_entry["topic_id"]) <= unlocked_topic_id
        ]
    if available:
        return available
    return chapter_topics[:1]


def get_level_limit(
    active_topic_entry: TopicDict | None,
    unlocked_topic_id: int,
    unlocked_level: int,
    admin_mode: bool,
) -> int:
    """Return the highest selectable level for the current unlock state."""
    if not active_topic_entry:
        return 1
    topic_id = int(active_topic_entry["topic_id"])
    max_level = int(active_topic_entry["max_level"])
    if admin_mode or topic_id < unlocked_topic_id:
        return max_level
    return min(unlocked_level, max_level)


def get_level_options(level_limit: int) -> list[int]:
    return list(range(1, max(level_limit, 1) + 1))


# --- Navigation resolution ---


def resolve_chapter_change(
    state: GameState, curriculum: dict[int, list[TopicDict]], next_chapter_id: int
) -> tuple[int, int, int]:
    """Pick default topic and level when switching chapter."""
    next_chapter_topics = _topics_for_chapter(curriculum, next_chapter_id)
    next_chapter_progress = state.chapter_progress.get(next_chapter_id)
    next_topic_id = (
        next_chapter_progress.unlocked_topic_id
        if next_chapter_progress
        else _first_topic_id(next_chapter_topics)
    )
    next_topic_entry = (
        _find_topic_by_id(next_chapter_topics, next_topic_id)
        or (next_chapter_topics[0] if next_chapter_topics else None)
    )
    next_level = _clamp_level(
        next_chapter_progress.unlocked_level if next_chapter_progress else 1,
        next_topic_entry,
    )
    return next_chapter_id, next_topic_id, next_level


def resolve_topic_change(
    state: GameState,
    curriculum: dict[int, list[TopicDict]],
    chapter_id: int,
    next_topic_id: int,
) -> tuple[int, int]:
    """Pick default level when switching topic within a chapter."""
    chapter_topics = _topics_for_chapter(curriculum, chapter_id)
    unlocked_topic_id, unlocked_level = _get_unlocked(state, chapter_id, chapter_topics)
    next_topic_entry = _find_topic_by_id(chapter_topics, next_topic_id)
    if next_topic_id < unlocked_topic_id:
        next_level = 1
    else:
        next_level = _clamp_level(unlocked_level, next_topic_entry)
    return next_topic_id, next_level


def resolve_navigate_request(
    state: GameState,
    curriculum: dict[int, list[TopicDict]],
    request: SessionNavigateRequest,
) -> tuple[int, int, int]:
    """Resolve partial navigation intents into a full chapter/topic/level target."""
    if (
        request.selected_chapter_id is not None
        and request.selected_chapter_id != state.selected_chapter_id
    ):
        return resolve_chapter_change(state, curriculum, request.selected_chapter_id)

    chapter_id = request.selected_chapter_id or state.selected_chapter_id
    if chapter_id is None:
        chapter_summaries = get_chapters()
        chapter_id = chapter_summaries[0].chapter_id if chapter_summaries else 0

    if request.selected_topic_id is not None:
        topic_id, level = resolve_topic_change(
            state, curriculum, chapter_id, int(request.selected_topic_id)
        )
        if request.selected_level is not None:
            level = int(request.selected_level)
        return chapter_id, topic_id, level

    if request.selected_level is not None:
        topic_id = state.selected_topic_id or state_manager.StateManager._get_first_topic_id(
            curriculum, chapter_id
        )
        return chapter_id, int(topic_id), int(request.selected_level)

    topic_id = state.selected_topic_id or state_manager.StateManager._get_first_topic_id(
        curriculum, chapter_id
    )
    return chapter_id, int(topic_id), int(state.selected_level)


# --- API view builder ---


def build_navigation_view(
    state: GameState, curriculum: dict[int, list[TopicDict]]
) -> NavigationView:
    """Build dropdown options, progress counts, and level limits for the frontend."""
    chapter_summaries = get_chapters()
    available_chapters = [
        NavigationChapterOption(chapter_id=chapter.chapter_id, name=chapter.name)
        for chapter in chapter_summaries
    ]

    selected_chapter_id = state.selected_chapter_id or (
        chapter_summaries[0].chapter_id if chapter_summaries else 0
    )
    chapter_topics = _topics_for_chapter(curriculum, selected_chapter_id)
    first_topic_entry = chapter_topics[0] if chapter_topics else None
    first_topic_id = _first_topic_id(chapter_topics)

    selected_topic_id = state.selected_topic_id or first_topic_id
    active_topic_entry = (
        _find_topic_by_id(chapter_topics, selected_topic_id) or first_topic_entry
    )
    selected_level = _clamp_level(state.selected_level, active_topic_entry)

    unlocked_topic_id, unlocked_level = _get_unlocked(
        state, selected_chapter_id, chapter_topics
    )
    admin_mode = state.admin_mode

    available_topic_entries = get_topic_options(
        chapter_topics, unlocked_topic_id, admin_mode
    )
    available_topics = [
        NavigationTopicOption(
            topic_id=int(topic_entry["topic_id"]),
            name=str(topic_entry["name"]),
        )
        for topic_entry in available_topic_entries
    ]

    level_limit = get_level_limit(
        active_topic_entry, unlocked_topic_id, unlocked_level, admin_mode
    )
    available_levels = get_level_options(level_limit)

    has_next = (
        selected_chapter_id in state.chapter_progress
        and state.selected_topic_id is not None
        and state.chapter_progress[selected_chapter_id].unlocked_topic_id
        > (state.selected_topic_id or 0)
    )

    text_mode_disabled = bool(
        active_topic_entry and active_topic_entry.get("text_mode_disabled")
    )

    chapter_progress_view: NavigationProgress | None = None
    if selected_chapter_id and chapter_topics:
        completed = sum(
            1
            for topic_entry in chapter_topics
            if int(topic_entry["topic_id"]) < unlocked_topic_id
        )
        total = len(chapter_topics)
        chapter_progress_view = NavigationProgress(
            completed=completed,
            total=total,
            percentage=(completed / total * 100) if total > 0 else 0.0,
        )

    topic_progress_view: NavigationProgress | None = None
    if active_topic_entry:
        max_level = int(active_topic_entry["max_level"])
        completed_levels = selected_level - 1
        topic_progress_view = NavigationProgress(
            completed=completed_levels,
            total=max_level,
            percentage=(completed_levels / max_level * 100) if max_level > 0 else 0.0,
        )

    return NavigationView(
        available_chapters=available_chapters,
        current_topic_name=str(active_topic_entry["name"]) if active_topic_entry else None,
        available_topics=available_topics,
        available_levels=available_levels,
        has_next_unlocked_topic=has_next,
        text_mode_disabled=text_mode_disabled,
        chapter_progress=chapter_progress_view,
        topic_progress=topic_progress_view,
    )
