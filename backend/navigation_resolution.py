"""Navigation intent resolution — resolve partial intents into chapter/topic/level targets."""

from __future__ import annotations

from backend.curriculum import Curriculum
from backend.models import SessionState, SessionNavigateRequest
from backend.navigation_snapshot import (
    NavigationSnapshot,
    _clamp_level,
    _find_topic_by_id,
    _topics_for_chapter,
)
from backend.unlock import first_topic_id


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
