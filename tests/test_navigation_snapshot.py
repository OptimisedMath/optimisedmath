"""Unit tests for navigation snapshot and view — by play mode and frontier position."""

import uuid

import pytest

from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.navigation_snapshot import build_navigation_snapshot, build_navigation_view
from backend.play_mode import AdminPlayMode, StudentPlayMode, resolve_play_mode
import backend.session_state as session_state
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    CHAPTER_BETA,
    TOPIC_MULTI,
    TOPIC_RADIO,
    TOPIC_SINGLE,
)

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


def _fresh_state(
    fixture_curriculum: Curriculum, *, username: str = "nav-user"
) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = username
    state.session_id = str(uuid.uuid4())
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = 1
    return state


def _build(state: SessionState, fixture_curriculum: Curriculum, play_mode):
    snapshot = build_navigation_snapshot(state, fixture_curriculum, play_mode)
    view = build_navigation_view(snapshot)
    return snapshot, view


# --- Snapshot invariants ---


def test_snapshot_is_immutable(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)
    with pytest.raises(AttributeError):
        snapshot.selected_level = 2  # type: ignore[misc]


def test_snapshot_exposes_chapters_from_handed_curriculum(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    snapshot, view = _build(state, fixture_curriculum, _STUDENT)

    assert [chapter.chapter_id for chapter in snapshot.chapters()] == [
        CHAPTER_ALPHA,
        CHAPTER_BETA,
    ]
    assert [chapter.name for chapter in snapshot.chapters()] == [
        "Chapter Alpha",
        "Chapter Beta",
    ]
    assert [(c.chapter_id, c.name) for c in view.available_chapters] == [
        (CHAPTER_ALPHA, "Chapter Alpha"),
        (CHAPTER_BETA, "Chapter Beta"),
    ]


def test_snapshot_defaults_selected_chapter_from_handed_curriculum(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = None
    state.selected_topic_id = None

    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)

    assert snapshot.selected_chapter_id == CHAPTER_ALPHA
    assert snapshot.selected_topic_id == TOPIC_MULTI


# --- Student · at the Frontier ---


def test_student_at_frontier_topic_and_level_limits(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )
    snapshot, view = _build(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.current
    frontier = state.chapter_frontiers[CHAPTER_ALPHA]

    assert ctx.effective_frontier.frontier_topic_id == frontier.frontier_topic_id
    assert ctx.effective_frontier.frontier_level == frontier.frontier_level
    assert ctx.level_limit_for(TOPIC_MULTI, 2) == min(frontier.frontier_level, 2)
    assert view.available_levels == [1]


def test_student_at_frontier_has_no_next_unlocked_topic(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_MULTI

    _, view = _build(state, fixture_curriculum, _STUDENT)

    assert view.has_next_unlocked_topic is False


def test_student_at_frontier_with_next_topic_unlocked(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_RADIO

    snapshot, view = _build(state, fixture_curriculum, _STUDENT)

    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is True
    assert view.has_next_unlocked_topic is True


# --- Student · behind the Frontier ---


def test_student_behind_frontier_sees_reachable_topics_and_levels(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.selected_topic_id = TOPIC_MULTI
    snapshot, view = _build(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.current

    accessible_ids = {int(t["topic_id"]) for t in ctx.accessible_topics}
    assert accessible_ids == {TOPIC_MULTI, TOPIC_RADIO}
    assert [t.topic_id for t in view.available_topics] == [TOPIC_MULTI, TOPIC_RADIO]
    assert view.current_topic_name == "Multi Level Topic"
    assert view.available_levels == [1, 2]
    assert ctx.can_access(TOPIC_MULTI, 1) is True
    assert ctx.can_access(TOPIC_MULTI, 2) is True


def test_student_behind_frontier_progress(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.selected_topic_id = TOPIC_RADIO
    state.selected_level = 1

    snapshot, view = _build(state, fixture_curriculum, _STUDENT)
    chapter_progress = snapshot.current.chapter_progress()
    topic_progress = snapshot.current.topic_progress(
        snapshot.selected_topic_id, snapshot.selected_level
    )

    assert chapter_progress is not None
    assert chapter_progress.completed == 1
    assert chapter_progress.total == 2
    assert chapter_progress.percentage == pytest.approx(50.0)
    assert view.chapter_completion == chapter_progress
    assert topic_progress is not None
    assert topic_progress.completed == 0
    assert topic_progress.total == 1
    assert topic_progress.percentage == pytest.approx(0.0)
    assert view.topic_completion == topic_progress


# --- Student · beyond the Frontier ---


def test_student_beyond_frontier_topics_are_locked(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    # Default frontier is TOPIC_MULTI level 1 — TOPIC_RADIO stays beyond.
    snapshot, view = _build(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.current

    accessible_ids = {int(t["topic_id"]) for t in ctx.accessible_topics}
    assert accessible_ids == {TOPIC_MULTI}
    assert TOPIC_RADIO not in accessible_ids
    assert [t.topic_id for t in view.available_topics] == [TOPIC_MULTI]
    assert ctx.can_access(TOPIC_MULTI, 1) is True
    assert ctx.can_access(TOPIC_RADIO, 1) is False


def test_student_radio_only_follows_active_topic(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    _, view = _build(state, fixture_curriculum, _STUDENT)
    assert view.radio_only is False

    state.selected_topic_id = TOPIC_RADIO
    _, view = _build(state, fixture_curriculum, _STUDENT)
    assert view.radio_only is True


# --- Admin ---


def test_admin_sees_all_topics_and_full_levels(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    snapshot, view = _build(state, fixture_curriculum, _ADMIN)
    ctx = snapshot.current

    assert ctx.effective_frontier.frontier_topic_id == TOPIC_RADIO
    assert ctx.effective_frontier.frontier_level == 1
    assert {int(t["topic_id"]) for t in ctx.accessible_topics} == {
        TOPIC_MULTI,
        TOPIC_RADIO,
    }
    assert [t.topic_id for t in view.available_topics] == [TOPIC_MULTI, TOPIC_RADIO]
    assert view.available_levels == [1, 2]


def test_admin_progress_bars_show_full_completion(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    snapshot, view = _build(state, fixture_curriculum, _ADMIN)
    chapter_progress = snapshot.current.chapter_progress()
    topic_progress = snapshot.current.topic_progress(
        snapshot.selected_topic_id, snapshot.selected_level
    )

    assert chapter_progress is not None
    assert chapter_progress.percentage == 100.0
    assert chapter_progress.completed == 2
    assert chapter_progress.total == 2
    assert view.chapter_completion == chapter_progress
    assert topic_progress is not None
    assert topic_progress.percentage == 100.0
    assert topic_progress.completed == 2
    assert topic_progress.total == 2
    assert view.topic_completion == topic_progress


def test_admin_has_next_unlocked_topic_is_false(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_RADIO

    snapshot, view = _build(
        state, fixture_curriculum, resolve_play_mode(state.username)
    )

    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is False
    assert view.has_next_unlocked_topic is False


def test_admin_radio_only_follows_active_topic(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.selected_topic_id = TOPIC_RADIO
    _, view = _build(state, fixture_curriculum, _ADMIN)

    assert view.radio_only is True


# --- Snapshot resolution (implicit landing) ---


def test_snapshot_implicit_chapter_landing_student(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_BETA] = ChapterFrontier(
        frontier_topic_id=TOPIC_SINGLE,
        frontier_level=1,
    )
    progress = state.chapter_frontiers[CHAPTER_BETA]
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.chapter_context(CHAPTER_BETA)

    topic_id, level = ctx.implicit_chapter_landing
    assert topic_id == progress.frontier_topic_id
    assert level == progress.frontier_level


def test_snapshot_implicit_chapter_landing_admin(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )

    snapshot, _ = _build(state, fixture_curriculum, _ADMIN)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.implicit_chapter_landing == (TOPIC_MULTI, 1)


def test_snapshot_implicit_topic_landing(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=2,
    )
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.implicit_topic_landing(TOPIC_MULTI) == 2

    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.implicit_topic_landing(TOPIC_MULTI) == 1
    assert ctx.implicit_topic_landing(TOPIC_RADIO) == 1
