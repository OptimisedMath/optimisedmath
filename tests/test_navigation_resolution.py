"""Unit tests for navigation intent resolution (pure rules)."""

import uuid

import pytest

from backend.curriculum_loader import get_curriculum
from backend.models import ChapterFrontier, SessionState, SessionNavigateRequest
from backend.play_mode import AdminPlayMode, StudentPlayMode
from backend import navigation_resolution as resolution
import backend.session_state as session_state

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


def _curriculum_and_chapters():
    curriculum = get_curriculum()
    chapter_ids = sorted(curriculum.keys())
    return curriculum, chapter_ids


def _fresh_state() -> SessionState:
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = SessionState()
    session_state.init_defaults(state, chapter_ids, curriculum)
    state.username = "nav-resolution-user"
    state.session_id = str(uuid.uuid4())
    return state


def test_get_level_options_returns_one_through_limit():
    assert resolution.get_level_options(3) == [1, 2, 3]
    assert resolution.get_level_options(0) == [1]
    assert resolution.get_level_options(1) == [1]


def test_resolve_chapter_change_uses_unlocked_topic_and_level():
    curriculum, chapter_ids = _curriculum_and_chapters()
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    state = _fresh_state()
    target_chapter_id = chapter_ids[1]
    progress = state.chapter_frontiers[target_chapter_id]
    expected_topic_id = progress.frontier_topic_id
    chapter_topics = curriculum[target_chapter_id]
    topic_entry = next(
        topic
        for topic in chapter_topics
        if int(topic["topic_id"]) == expected_topic_id
    )
    expected_level = min(progress.frontier_level, int(topic_entry["max_level"]))

    chapter_id, topic_id, level = resolution.resolve_chapter_change(
        state, curriculum, target_chapter_id, _STUDENT
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
    chapter_topics = curriculum[chapter_id]
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
        state, curriculum, chapter_id, completed_topic_id, _STUDENT
    )

    assert topic_id == completed_topic_id
    assert level == 1


def test_clamp_selected_level_caps_stale_level():
    state = _fresh_state()
    curriculum, chapter_ids = _curriculum_and_chapters()
    chapter_id = chapter_ids[0]
    topic_entry = curriculum[chapter_id][0]
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
        state, curriculum, request, _STUDENT
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
        state, curriculum, request, _STUDENT
    )

    assert chapter_id == state.selected_chapter_id
    assert level == 2


def test_admin_chapter_change_lands_on_first_topic_at_level_one():
    curriculum, chapter_ids = _curriculum_and_chapters()
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    state = _fresh_state()
    target_chapter_id = chapter_ids[1]
    chapter_topics = curriculum[target_chapter_id]
    last_topic_id = int(chapter_topics[-1]["topic_id"])
    state.chapter_frontiers[target_chapter_id] = ChapterFrontier(
        frontier_topic_id=last_topic_id,
        frontier_level=3,
    )
    expected_first_topic_id = int(chapter_topics[0]["topic_id"])

    chapter_id, topic_id, level = resolution.resolve_chapter_change(
        state, curriculum, target_chapter_id, _ADMIN
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
    chapter_topics = curriculum[chapter_id]
    target_topic_id = int(chapter_topics[0]["topic_id"])
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=target_topic_id,
        frontier_level=3,
    )

    topic_id, level = resolution.resolve_topic_change(
        state, curriculum, chapter_id, target_topic_id, _ADMIN
    )

    assert (topic_id, level) == (target_topic_id, 1)


def test_admin_explicit_topic_and_level_unchanged():
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = _fresh_state()
    chapter_id = chapter_ids[0]
    chapter_topics = curriculum[chapter_id]
    target_topic_id = int(chapter_topics[0]["topic_id"])
    explicit_level = 3

    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_topic_id=target_topic_id,
        selected_level=explicit_level,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, curriculum, request, _ADMIN
    )

    assert (chapter_id, topic_id, level) == (chapter_id, target_topic_id, explicit_level)
