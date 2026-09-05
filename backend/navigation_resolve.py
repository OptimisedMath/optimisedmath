"""Navigation resolve — validate and resolve a navigation intent into a target."""

from __future__ import annotations

from backend.curriculum import Curriculum
from backend.models import SessionNavigateRequest, SessionState
from backend.navigation_snapshot import NavigationSnapshot
from backend.unlock import first_topic_id


def clamp_selected_level(state: SessionState, curriculum: Curriculum) -> None:
    """Clamp session selected_level to the current topic's max_level."""
    chapter_id = state.selected_chapter_id
    if chapter_id is None:
        return
    chapter_topics = list(curriculum.topics(chapter_id))
    if not chapter_topics:
        return
    first_topic_entry = chapter_topics[0]
    topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
    topic_entry = curriculum.topic_by_id(chapter_id, topic_id) or first_topic_entry
    state.selected_level = curriculum.clamp_level(
        state.selected_level,
        chapter_id,
        int(topic_entry["topic_id"]),
    )


def resolve_chapter_change(
    next_chapter_id: int,
    snapshot: NavigationSnapshot,
) -> tuple[int, int, int]:
    """Pick default topic and level when switching chapter."""
    curriculum = snapshot.curriculum()
    ctx = snapshot.chapter_context(next_chapter_id)
    next_topic_id, next_level = ctx.implicit_chapter_landing
    next_chapter_topics = list(curriculum.topics(next_chapter_id))
    next_topic_entry = curriculum.topic_by_id(next_chapter_id, next_topic_id) or (
        next_chapter_topics[0] if next_chapter_topics else None
    )
    next_topic_for_clamp = (
        int(next_topic_entry["topic_id"]) if next_topic_entry is not None else None
    )
    return (
        next_chapter_id,
        next_topic_id,
        curriculum.clamp_level(next_level, next_chapter_id, next_topic_for_clamp),
    )


def resolve_topic_change(
    chapter_id: int,
    next_topic_id: int,
    snapshot: NavigationSnapshot,
) -> tuple[int, int]:
    """Pick default level when switching topic within a chapter."""
    curriculum = snapshot.curriculum()
    ctx = snapshot.chapter_context(chapter_id)
    next_level = ctx.implicit_topic_landing(next_topic_id)
    return next_topic_id, curriculum.clamp_level(next_level, chapter_id, next_topic_id)


def resolve_navigate_request(
    state: SessionState,
    request: SessionNavigateRequest,
    snapshot: NavigationSnapshot,
) -> tuple[int, int, int]:
    """Resolve partial navigation intents into a full chapter/topic/level target."""
    if (
        request.selected_chapter_id is not None
        and request.selected_chapter_id != state.selected_chapter_id
    ):
        return resolve_chapter_change(request.selected_chapter_id, snapshot)

    chapter_id = request.selected_chapter_id or state.selected_chapter_id
    if chapter_id is None:
        chapters = snapshot.chapters()
        chapter_id = chapters[0].chapter_id if chapters else 0

    curriculum = snapshot.curriculum()
    chapter_topics = list(curriculum.topics(chapter_id))

    if request.selected_topic_id is not None:
        topic_id, level = resolve_topic_change(
            chapter_id, int(request.selected_topic_id), snapshot
        )
        if request.selected_level is not None:
            level = int(request.selected_level)
        return chapter_id, topic_id, level

    if request.selected_level is not None:
        topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
        return chapter_id, int(topic_id), int(request.selected_level)

    topic_id = state.selected_topic_id or first_topic_id(chapter_topics)
    return chapter_id, int(topic_id), int(state.selected_level)


# --- Navigation intent validate-and-resolve ---


class NavigationResolutionError(Exception):
    """Base error for navigation intent validate-and-resolve failures."""


class NavigationChapterNotFoundError(NavigationResolutionError):
    """Resolved chapter id does not exist in the curriculum."""

    def __init__(self, chapter_id: int) -> None:
        super().__init__(f"Chapter id {chapter_id} not found in curriculum")


class NavigationChapterHasNoTopicsError(NavigationResolutionError):
    """Resolved chapter exists but has no topics defined."""

    def __init__(self, chapter_id: int) -> None:
        super().__init__(f"Chapter id {chapter_id} has no available topics")


class NavigationTopicNotFoundError(NavigationResolutionError):
    """Resolved topic id is not a member of the resolved chapter."""

    def __init__(self, topic_id: int) -> None:
        super().__init__(f"Topic id {topic_id} not found in curriculum")


class NavigationLevelOutOfRangeError(NavigationResolutionError):
    """Resolved level falls outside the topic's level bounds."""

    def __init__(self, level: int, topic_id: int) -> None:
        super().__init__(f"Level {level} is not available for topic id {topic_id}")


class NavigationLockedError(NavigationResolutionError):
    """Resolved target is Beyond the Frontier — Locked for the current Student."""


def resolve_navigation_target(
    state: SessionState,
    request: SessionNavigateRequest,
    snapshot: NavigationSnapshot,
) -> tuple[int, int, int]:
    """Validate and resolve a navigation intent into a Reachable target.

    Resolves the partial request into a full chapter/topic/level target, then
    validates curriculum existence, topic membership, level bounds, and
    Locked status against the Frontier captured on ``snapshot``. Does not
    mutate session state or call session use-cases.

    Raises:
        NavigationChapterNotFoundError: resolved chapter does not exist.
        NavigationChapterHasNoTopicsError: resolved chapter has no topics.
        NavigationTopicNotFoundError: resolved topic is not in the chapter.
        NavigationLevelOutOfRangeError: resolved level is out of bounds.
        NavigationLockedError: resolved target is Locked for this Student.
    """
    curriculum = snapshot.curriculum()
    chapter_id, topic_id, level = resolve_navigate_request(state, request, snapshot)

    if not curriculum.has_chapter(chapter_id):
        raise NavigationChapterNotFoundError(chapter_id)

    chapter_topics = list(curriculum.topics(chapter_id))
    if not chapter_topics:
        raise NavigationChapterHasNoTopicsError(chapter_id)

    available_topic_ids = [int(entry["topic_id"]) for entry in chapter_topics]
    if topic_id not in available_topic_ids:
        raise NavigationTopicNotFoundError(topic_id)

    topic_meta = curriculum.topic_by_id(chapter_id, topic_id)
    if topic_meta is None:
        raise NavigationTopicNotFoundError(topic_id)
    max_level = int(topic_meta["max_level"])

    if level < 1 or level > max_level:
        raise NavigationLevelOutOfRangeError(level, topic_id)

    ctx = snapshot.chapter_context(chapter_id)
    if not ctx.is_reachable(topic_id, level):
        if topic_id > ctx.resolve_frontier.frontier_topic_id:
            raise NavigationLockedError("Topic is locked")
        raise NavigationLockedError("Level is locked")

    return chapter_id, topic_id, level
