"""Unit tests for the navigation snapshot read model."""

import uuid

import pytest

from backend.curriculum_loader import get_curriculum
from backend.models import ChapterFrontier, SessionState
from backend.navigation_snapshot import build_navigation_snapshot
from backend.play_mode import AdminPlayMode, StudentPlayMode, resolve_play_mode
import backend.session_state as session_state

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


def _curriculum_and_chapters():
    curriculum = get_curriculum()
    chapter_ids = sorted(curriculum.keys())
    return curriculum, chapter_ids


def _fresh_state(*, username: str = "nav-snapshot-user") -> SessionState:
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


def test_snapshot_is_immutable():
    state = _fresh_state()
    curriculum = get_curriculum()
    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    with pytest.raises(AttributeError):
        snapshot.selected_level = 2  # type: ignore[misc]


def test_snapshot_includes_effective_frontier():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    stored = state.chapter_frontiers[chapter_id]

    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    ctx = snapshot.current

    assert ctx.effective_frontier.frontier_topic_id == stored.frontier_topic_id
    assert ctx.effective_frontier.frontier_level == stored.frontier_level


def test_admin_snapshot_uses_chapter_max_frontier():
    state = _fresh_state(username="Antoni")
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    last_topic = chapter_topics[-1]

    snapshot = build_navigation_snapshot(state, curriculum, _ADMIN)
    ctx = snapshot.current

    assert ctx.effective_frontier.frontier_topic_id == int(last_topic["topic_id"])
    assert ctx.effective_frontier.frontier_level == int(last_topic["max_level"])


def test_snapshot_accessible_topics_respect_locks():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    frontier_topic_id = state.chapter_frontiers[chapter_id].frontier_topic_id
    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    accessible_ids = {int(t["topic_id"]) for t in snapshot.current.accessible_topics}
    expected = {
        int(topic_entry["topic_id"])
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) <= frontier_topic_id
    }
    assert accessible_ids == expected


def test_admin_snapshot_includes_all_topics():
    state = _fresh_state(username="Antoni")
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]

    snapshot = build_navigation_snapshot(state, curriculum, _ADMIN)

    assert len(snapshot.current.accessible_topics) == len(chapter_topics)


def test_snapshot_level_limit_for_active_topic():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    frontier = state.chapter_frontiers[chapter_id]

    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    topic_id = snapshot.selected_topic_id
    topic_entry = next(
        t for t in curriculum[chapter_id] if int(t["topic_id"]) == topic_id
    )
    max_level = int(topic_entry["max_level"])

    assert snapshot.current.level_limit_for(topic_id, max_level) == min(
        frontier.frontier_level, max_level
    )


def test_snapshot_implicit_chapter_landing_student():
    state = _fresh_state()
    curriculum, chapter_ids = _curriculum_and_chapters()
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    target_chapter_id = chapter_ids[1]
    progress = state.chapter_frontiers[target_chapter_id]
    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    ctx = snapshot.chapter_context(target_chapter_id)

    topic_id, level = ctx.implicit_chapter_landing
    assert topic_id == progress.frontier_topic_id
    assert level == progress.frontier_level


def test_snapshot_implicit_chapter_landing_admin():
    state = _fresh_state(username="Antoni")
    curriculum, chapter_ids = _curriculum_and_chapters()
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    target_chapter_id = chapter_ids[1]
    chapter_topics = curriculum[target_chapter_id]
    last_topic_id = int(chapter_topics[-1]["topic_id"])
    state.chapter_frontiers[target_chapter_id] = ChapterFrontier(
        frontier_topic_id=last_topic_id,
        frontier_level=3,
    )
    expected_first = int(chapter_topics[0]["topic_id"])

    snapshot = build_navigation_snapshot(state, curriculum, _ADMIN)
    ctx = snapshot.chapter_context(target_chapter_id)

    assert ctx.implicit_chapter_landing == (expected_first, 1)


def test_snapshot_implicit_topic_landing():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    frontier_topic_id = state.chapter_frontiers[chapter_id].frontier_topic_id
    completed_topic_id = int(chapter_topics[0]["topic_id"])
    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    ctx = snapshot.chapter_context(chapter_id)

    assert ctx.implicit_topic_landing(completed_topic_id) == 1
    assert ctx.implicit_topic_landing(frontier_topic_id) == state.chapter_frontiers[
        chapter_id
    ].frontier_level


def test_snapshot_can_access():
    state = _fresh_state()
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    frontier_topic_id = state.chapter_frontiers[chapter_id].frontier_topic_id
    locked_topic_id = int(chapter_topics[-1]["topic_id"])
    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    ctx = snapshot.chapter_context(chapter_id)

    assert ctx.can_access(frontier_topic_id, 1) is True
    if locked_topic_id > frontier_topic_id:
        assert ctx.can_access(locked_topic_id, 1) is False


def test_snapshot_progress_counts_student():
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

    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    chapter_progress = snapshot.current.chapter_progress()
    topic_progress = snapshot.current.topic_progress(
        snapshot.selected_topic_id, snapshot.selected_level
    )

    assert chapter_progress is not None
    assert chapter_progress.completed == completed
    assert chapter_progress.total == total
    assert topic_progress is not None
    assert topic_progress.completed == snapshot.selected_level - 1


def test_snapshot_progress_counts_admin():
    state = _fresh_state(username="Antoni")
    curriculum = get_curriculum()
    chapter_id = _selected_chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    current_topic = next(
        t for t in chapter_topics if int(t["topic_id"]) == state.selected_topic_id
    )
    max_level = int(current_topic["max_level"])
    total = len(chapter_topics)

    snapshot = build_navigation_snapshot(state, curriculum, _ADMIN)
    chapter_progress = snapshot.current.chapter_progress()
    topic_progress = snapshot.current.topic_progress(
        snapshot.selected_topic_id, snapshot.selected_level
    )

    assert chapter_progress is not None
    assert chapter_progress.percentage == 100.0
    assert chapter_progress.completed == total
    assert topic_progress is not None
    assert topic_progress.percentage == 100.0
    assert topic_progress.completed == max_level


def test_snapshot_has_next_unlocked_topic():
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

    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is True

    state.chapter_frontiers[chapter_id].frontier_topic_id = first_topic_id
    snapshot = build_navigation_snapshot(state, curriculum, _STUDENT)
    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is False


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

    snapshot = build_navigation_snapshot(state, curriculum, resolve_play_mode(state.username))
    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is False
