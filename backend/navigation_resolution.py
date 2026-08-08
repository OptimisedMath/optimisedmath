"""Navigation intent resolution — resolve partial intents into chapter/topic/level targets."""

from __future__ import annotations

from backend.curriculum_loader import TopicDict, get_chapters
from backend.models import SessionState, SessionNavigateRequest
from backend.play_mode import PlayMode
from backend.unlock import first_topic_id


def topics_for_chapter(
    curriculum: dict[int, list[TopicDict]], chapter_id: int
) -> list[TopicDict]:
    return curriculum.get(chapter_id, [])


def find_topic_by_id(
    chapter_topics: list[TopicDict], topic_id: int
) -> TopicDict | None:
    for topic_entry in chapter_topics:
        if int(topic_entry["topic_id"]) == topic_id:
            return topic_entry
    return None


def clamp_level(level: int | None, topic_entry: TopicDict | None) -> int:
    """Return level capped to the topic's max_level (defensive for stale saves)."""
    effective = level if level is not None else 1
    max_level = int(topic_entry["max_level"]) if topic_entry else 1
    return min(effective, max_level)


def clamp_selected_level(
    state: SessionState, curriculum: dict[int, list[TopicDict]]
) -> None:
    """Clamp session selected_level to the current topic's max_level."""
    chapter_id = state.selected_chapter_id
    if chapter_id is None:
        return
    chapter_topics = topics_for_chapter(curriculum, chapter_id)
    if not chapter_topics:
        return
    first_topic_entry = chapter_topics[0]
    topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
    topic_entry = find_topic_by_id(chapter_topics, topic_id) or first_topic_entry
    state.selected_level = clamp_level(state.selected_level, topic_entry)


def get_level_options(level_limit_value: int) -> list[int]:
    return list(range(1, max(level_limit_value, 1) + 1))


def resolve_chapter_change(
    state: SessionState,
    curriculum: dict[int, list[TopicDict]],
    next_chapter_id: int,
    play_mode: PlayMode,
) -> tuple[int, int, int]:
    """Pick default topic and level when switching chapter."""
    next_chapter_topics = topics_for_chapter(curriculum, next_chapter_id)
    next_topic_id, next_level = play_mode.implicit_chapter_landing(
        next_chapter_topics, state.chapter_frontiers.get(next_chapter_id)
    )
    next_topic_entry = (
        find_topic_by_id(next_chapter_topics, next_topic_id)
        or (next_chapter_topics[0] if next_chapter_topics else None)
    )
    return next_chapter_id, next_topic_id, clamp_level(next_level, next_topic_entry)


def resolve_topic_change(
    state: SessionState,
    curriculum: dict[int, list[TopicDict]],
    chapter_id: int,
    next_topic_id: int,
    play_mode: PlayMode,
) -> tuple[int, int]:
    """Pick default level when switching topic within a chapter."""
    chapter_topics = topics_for_chapter(curriculum, chapter_id)
    next_level = play_mode.implicit_topic_landing(
        chapter_topics, next_topic_id, state.chapter_frontiers.get(chapter_id)
    )
    next_topic_entry = find_topic_by_id(chapter_topics, next_topic_id)
    return next_topic_id, clamp_level(next_level, next_topic_entry)


def resolve_navigate_request(
    state: SessionState,
    curriculum: dict[int, list[TopicDict]],
    request: SessionNavigateRequest,
    play_mode: PlayMode,
) -> tuple[int, int, int]:
    """Resolve partial navigation intents into a full chapter/topic/level target."""
    if (
        request.selected_chapter_id is not None
        and request.selected_chapter_id != state.selected_chapter_id
    ):
        return resolve_chapter_change(
            state, curriculum, request.selected_chapter_id, play_mode
        )

    chapter_id = request.selected_chapter_id or state.selected_chapter_id
    if chapter_id is None:
        chapter_summaries = get_chapters()
        chapter_id = chapter_summaries[0].chapter_id if chapter_summaries else 0

    chapter_topics = topics_for_chapter(curriculum, chapter_id)

    if request.selected_topic_id is not None:
        topic_id, level = resolve_topic_change(
            state, curriculum, chapter_id, int(request.selected_topic_id), play_mode
        )
        if request.selected_level is not None:
            level = int(request.selected_level)
        return chapter_id, topic_id, level

    if request.selected_level is not None:
        topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
        return chapter_id, int(topic_id), int(request.selected_level)

    topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
    return chapter_id, int(topic_id), int(state.selected_level)
