"""Unit tests for navigation intent resolution (pure rules)."""

import uuid

import pytest

from backend.curriculum import Curriculum, resolve_curriculum
from backend.models import ChapterFrontier, SessionState, SessionNavigateRequest
from backend.navigation import build_navigation_snapshot
from backend.play_mode import AdminPlayMode, StudentPlayMode
from backend.navigation import _get_level_options as get_level_options
import backend.navigation as resolution
import backend.session_state as session_state
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    TOPIC_MULTI,
    TOPIC_RADIO,
)

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


def _curriculum_and_chapters():
    curriculum = resolve_curriculum()
    chapter_ids = list(curriculum.chapter_ids())
    return curriculum, chapter_ids


def _fresh_state() -> SessionState:
    curriculum, _ = _curriculum_and_chapters()
    state = SessionState()
    session_state.init_defaults(state, curriculum)
    state.username = "nav-resolution-user"
    state.session_id = str(uuid.uuid4())
    return state


def _snapshot(state: SessionState, play_mode):
    return build_navigation_snapshot(state, resolve_curriculum(), play_mode)


def test_get_level_options_returns_one_through_limit():
    assert get_level_options(3) == [1, 2, 3]
    assert get_level_options(0) == [1]
    assert get_level_options(1) == [1]


def test_resolve_chapter_change_uses_unlocked_topic_and_level():
    curriculum, chapter_ids = _curriculum_and_chapters()
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    state = _fresh_state()
    target_chapter_id = chapter_ids[1]
    progress = state.chapter_frontiers[target_chapter_id]
    expected_topic_id = progress.frontier_topic_id
    chapter_topics = curriculum.topics(target_chapter_id)
    topic_entry = next(
        topic
        for topic in chapter_topics
        if int(topic["topic_id"]) == expected_topic_id
    )
    expected_level = min(progress.frontier_level, int(topic_entry["max_level"]))

    chapter_id, topic_id, level = resolution.resolve_chapter_change(
        curriculum, target_chapter_id, _snapshot(state, _STUDENT)
    )

    assert (chapter_id, topic_id, level) == (
        target_chapter_id,
        expected_topic_id,
        expected_level,
    )


def test_resolve_topic_change_resets_level_for_completed_topic():
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = _fresh_state()
    chapter_id = chapter_ids[0]
    chapter_topics = curriculum.topics(chapter_id)
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    frontier_topic_id = state.chapter_frontiers[chapter_id].frontier_topic_id
    completed_topics = [
        topic
        for topic in chapter_topics
        if int(topic["topic_id"]) < frontier_topic_id
    ]
    if not completed_topics:
        pytest.skip("Need a completed topic behind the Frontier")

    completed_topic_id = int(completed_topics[0]["topic_id"])
    topic_id, level = resolution.resolve_topic_change(
        curriculum, chapter_id, completed_topic_id, _snapshot(state, _STUDENT)
    )

    assert topic_id == completed_topic_id
    assert level == 1


def test_clamp_selected_level_caps_stale_level():
    state = _fresh_state()
    curriculum, chapter_ids = _curriculum_and_chapters()
    chapter_id = chapter_ids[0]
    topic_entry = curriculum.topics(chapter_id)[0]
    max_level = int(topic_entry["max_level"])

    state.selected_chapter_id = chapter_id
    state.selected_topic_id = int(topic_entry["topic_id"])
    state.selected_level = max_level + 10

    resolution.clamp_selected_level(state, curriculum)

    assert state.selected_level == max_level


def test_resolve_navigate_request_chapter_change():
    curriculum, chapter_ids = _curriculum_and_chapters()
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    state = _fresh_state()
    target_chapter_id = chapter_ids[1]
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=target_chapter_id,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, curriculum, request, _snapshot(state, _STUDENT)
    )

    progress = state.chapter_frontiers[target_chapter_id]
    assert chapter_id == target_chapter_id
    assert topic_id == progress.frontier_topic_id


def test_resolve_navigate_request_level_only():
    state = _fresh_state()
    curriculum, chapter_ids = _curriculum_and_chapters()
    chapter_id = chapter_ids[0]
    state.selected_chapter_id = chapter_id

    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_level=2,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, curriculum, request, _snapshot(state, _STUDENT)
    )

    assert chapter_id == state.selected_chapter_id
    assert level == 2


def test_admin_chapter_change_lands_on_first_topic_at_level_one():
    curriculum, chapter_ids = _curriculum_and_chapters()
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    state = _fresh_state()
    target_chapter_id = chapter_ids[1]
    chapter_topics = curriculum.topics(target_chapter_id)
    last_topic_id = int(chapter_topics[-1]["topic_id"])
    state.chapter_frontiers[target_chapter_id] = ChapterFrontier(
        frontier_topic_id=last_topic_id,
        frontier_level=3,
    )
    expected_first_topic_id = int(chapter_topics[0]["topic_id"])

    chapter_id, topic_id, level = resolution.resolve_chapter_change(
        curriculum, target_chapter_id, _snapshot(state, _ADMIN)
    )

    assert (chapter_id, topic_id, level) == (
        target_chapter_id,
        expected_first_topic_id,
        1,
    )


def test_admin_topic_change_lands_on_level_one():
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = _fresh_state()
    chapter_id = chapter_ids[0]
    chapter_topics = curriculum.topics(chapter_id)
    target_topic_id = int(chapter_topics[0]["topic_id"])
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=target_topic_id,
        frontier_level=3,
    )

    topic_id, level = resolution.resolve_topic_change(
        curriculum, chapter_id, target_topic_id, _snapshot(state, _ADMIN)
    )

    assert (topic_id, level) == (target_topic_id, 1)


def test_admin_explicit_topic_and_level_unchanged():
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = _fresh_state()
    chapter_id = chapter_ids[0]
    chapter_topics = curriculum.topics(chapter_id)
    target_topic_id = int(chapter_topics[0]["topic_id"])
    explicit_level = 3

    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_topic_id=target_topic_id,
        selected_level=explicit_level,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, curriculum, request, _snapshot(state, _ADMIN)
    )

    assert (chapter_id, topic_id, level) == (chapter_id, target_topic_id, explicit_level)


# --- resolve_navigation_target (validate-and-resolve) ---


def _fixture_state(fixture_curriculum: Curriculum) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = "nav-target-user"
    state.session_id = str(uuid.uuid4())
    return state


def test_resolve_navigation_target_returns_reachable_target(
    fixture_curriculum: Curriculum,
):
    state = _fixture_state(fixture_curriculum)
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=CHAPTER_ALPHA,
        selected_topic_id=TOPIC_MULTI,
        selected_level=1,
    )

    chapter_id, topic_id, level = resolution.resolve_navigation_target(
        state,
        fixture_curriculum,
        request,
        build_navigation_snapshot(state, fixture_curriculum, _STUDENT),
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_ALPHA, TOPIC_MULTI, 1)


def test_resolve_navigation_target_raises_for_missing_chapter(
    fixture_curriculum: Curriculum,
):
    state = _fixture_state(fixture_curriculum)
    request = SessionNavigateRequest(
        session_id=state.session_id, selected_chapter_id=999
    )

    with pytest.raises(resolution.NavigationChapterNotFoundError) as exc_info:
        resolution.resolve_navigation_target(
            state,
            fixture_curriculum,
            request,
            build_navigation_snapshot(state, fixture_curriculum, _STUDENT),
        )
    assert str(exc_info.value) == "Chapter id 999 not found in curriculum"


def test_resolve_navigation_target_raises_for_missing_topic(
    fixture_curriculum: Curriculum,
):
    state = _fixture_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    request = SessionNavigateRequest(
        session_id=state.session_id, selected_topic_id=999
    )

    with pytest.raises(resolution.NavigationTopicNotFoundError) as exc_info:
        resolution.resolve_navigation_target(
            state,
            fixture_curriculum,
            request,
            build_navigation_snapshot(state, fixture_curriculum, _STUDENT),
        )
    assert str(exc_info.value) == "Topic id 999 not found in curriculum"


def test_resolve_navigation_target_raises_for_out_of_range_level(
    fixture_curriculum: Curriculum,
):
    state = _fixture_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI, frontier_level=2
    )
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_topic_id=TOPIC_MULTI,
        selected_level=99,
    )

    with pytest.raises(resolution.NavigationLevelOutOfRangeError) as exc_info:
        resolution.resolve_navigation_target(
            state,
            fixture_curriculum,
            request,
            build_navigation_snapshot(state, fixture_curriculum, _STUDENT),
        )
    assert str(exc_info.value) == (
        f"Level 99 is not available for topic id {TOPIC_MULTI}"
    )


def test_resolve_navigation_target_raises_for_locked_topic(
    fixture_curriculum: Curriculum,
):
    state = _fixture_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI, frontier_level=1
    )
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=CHAPTER_ALPHA,
        selected_topic_id=TOPIC_RADIO,
        selected_level=1,
    )

    with pytest.raises(resolution.NavigationLockedError) as exc_info:
        resolution.resolve_navigation_target(
            state,
            fixture_curriculum,
            request,
            build_navigation_snapshot(state, fixture_curriculum, _STUDENT),
        )
    assert str(exc_info.value) == "Topic is locked"


def test_resolve_navigation_target_raises_for_locked_level(
    fixture_curriculum: Curriculum,
):
    state = _fixture_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI, frontier_level=1
    )
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=CHAPTER_ALPHA,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
    )

    with pytest.raises(resolution.NavigationLockedError) as exc_info:
        resolution.resolve_navigation_target(
            state,
            fixture_curriculum,
            request,
            build_navigation_snapshot(state, fixture_curriculum, _STUDENT),
        )
    assert str(exc_info.value) == "Level is locked"


def test_resolve_navigation_target_admin_bypasses_frontier_but_not_bounds(
    fixture_curriculum: Curriculum,
):
    state = _fixture_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI, frontier_level=1
    )
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=CHAPTER_ALPHA,
        selected_topic_id=TOPIC_RADIO,
        selected_level=1,
    )

    chapter_id, topic_id, level = resolution.resolve_navigation_target(
        state,
        fixture_curriculum,
        request,
        build_navigation_snapshot(state, fixture_curriculum, _ADMIN),
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_ALPHA, TOPIC_RADIO, 1)
