"""Unit tests for read-only navigation view building."""

import uuid

import pytest

from backend.curriculum_loader import get_curriculum
from backend.models import SessionState
from backend import navigation_snapshot as snapshot_module
from backend import navigation_view as view
from backend.play_mode import resolve_play_mode
import backend.session_state as session_state


def _curriculum_and_chapters():
    curriculum = get_curriculum()
    chapter_ids = sorted(curriculum.keys())
    return curriculum, chapter_ids


def _fresh_state(*, username: str = "nav-view-user") -> SessionState:
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = SessionState()
    session_state.init_defaults(state, chapter_ids, curriculum)
    state.username = username
    state.session_id = str(uuid.uuid4())
    state.selected_chapter_id = chapter_ids[0]
    state.selected_topic_id = int(curriculum[chapter_ids[0]][0]["topic_id"])
    state.selected_level = 1
    return state


def _selected_chapter_id(state: SessionState) -> int:
    chapter_id = state.selected_chapter_id
    assert chapter_id is not None
    return chapter_id


def _build_view(state: SessionState):
    curriculum = get_curriculum()
    play_mode = resolve_play_mode(state.username)
    snapshot = snapshot_module.build_navigation_snapshot(state, curriculum, play_mode)
    return view.build_navigation_view(snapshot)


def test_build_navigation_view_includes_dropdown_payload():
    state = _fresh_state()
    nav = _build_view(state)

    assert len(nav.available_chapters) > 0
    assert len(nav.available_topics) > 0
    assert len(nav.available_levels) > 0
    assert nav.current_topic_name is not None


def test_available_topics_respect_locks():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    frontier_topic_id = state.chapter_frontiers[chapter_id].frontier_topic_id
    nav = _build_view(state)
    available_topic_ids = {topic.topic_id for topic in nav.available_topics}
    expected = {
        int(topic_entry["topic_id"])
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) <= frontier_topic_id
    }
    assert available_topic_ids == expected


def test_admin_sees_all_topics():
    state = _fresh_state(username="Antoni")
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]

    nav = _build_view(state)

    assert len(nav.available_topics) == len(chapter_topics)


def test_admin_progress_bars_show_full_completion():
    state = _fresh_state(username="Antoni")
    state.selected_level = 1
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    current_topic = next(
        topic_entry
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) == state.selected_topic_id
    )
    max_level = int(current_topic["max_level"])
    total = len(chapter_topics)

    nav = _build_view(state)

    assert nav.chapter_completion is not None
    assert nav.topic_completion is not None
    assert nav.chapter_completion.percentage == 100.0
    assert nav.chapter_completion.completed == total
    assert nav.chapter_completion.total == total
    assert nav.topic_completion.percentage == 100.0
    assert nav.topic_completion.completed == max_level
    assert nav.topic_completion.total == max_level


def test_admin_has_next_unlocked_topic_is_false():
    state = _fresh_state(username="Antoni")
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    second_topic_id = int(chapter_topics[1]["topic_id"])
    state.selected_topic_id = int(chapter_topics[0]["topic_id"])
    state.chapter_frontiers[chapter_id].frontier_topic_id = second_topic_id

    nav = _build_view(state)

    assert nav.has_next_unlocked_topic is False


def test_has_next_unlocked_topic():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    first_topic_id = int(chapter_topics[0]["topic_id"])
    second_topic_id = int(chapter_topics[1]["topic_id"])
    state.selected_topic_id = first_topic_id
    state.chapter_frontiers[chapter_id].frontier_topic_id = second_topic_id

    nav = _build_view(state)
    assert nav.has_next_unlocked_topic is True

    state.chapter_frontiers[chapter_id].frontier_topic_id = first_topic_id
    nav = _build_view(state)
    assert nav.has_next_unlocked_topic is False


def test_progress_counts():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    frontier_topic_id = state.chapter_frontiers[chapter_id].frontier_topic_id
    completed = sum(
        1
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) < frontier_topic_id
    )
    total = len(chapter_topics)

    nav = _build_view(state)

    assert nav.chapter_completion is not None
    assert nav.topic_completion is not None
    assert nav.chapter_completion.completed == completed
    assert nav.chapter_completion.total == total
    assert nav.chapter_completion.percentage == pytest.approx(
        (completed / total * 100) if total else 0.0
    )

    current_topic = next(
        topic_entry
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) == state.selected_topic_id
    )
    max_level = int(current_topic["max_level"])
    assert nav.topic_completion.completed == state.selected_level - 1
    assert nav.topic_completion.total == max_level
    assert nav.topic_completion.percentage == pytest.approx(
        ((state.selected_level - 1) / max_level * 100) if max_level else 0.0
    )
