"""Unit tests for the navigation snapshot read model."""

import uuid

import pytest

from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.navigation_snapshot import build_navigation_snapshot
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
    fixture_curriculum: Curriculum, *, username: str = "nav-snapshot-user"
) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = username
    state.session_id = str(uuid.uuid4())
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = 1
    return state


def test_snapshot_is_immutable(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    with pytest.raises(AttributeError):
        snapshot.selected_level = 2  # type: ignore[misc]


def test_snapshot_exposes_chapters_from_handed_curriculum(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)

    assert [chapter.chapter_id for chapter in snapshot.chapters()] == [
        CHAPTER_ALPHA,
        CHAPTER_BETA,
    ]
    assert [chapter.name for chapter in snapshot.chapters()] == [
        "Chapter Alpha",
        "Chapter Beta",
    ]


def test_snapshot_defaults_selected_chapter_from_handed_curriculum(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = None
    state.selected_topic_id = None

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)

    assert snapshot.selected_chapter_id == CHAPTER_ALPHA
    assert snapshot.selected_topic_id == TOPIC_MULTI


def test_snapshot_includes_effective_frontier(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    stored = state.chapter_frontiers[CHAPTER_ALPHA]

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.current

    assert ctx.effective_frontier.frontier_topic_id == stored.frontier_topic_id
    assert ctx.effective_frontier.frontier_level == stored.frontier_level


def test_admin_snapshot_uses_chapter_max_frontier(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _ADMIN)
    ctx = snapshot.current

    assert ctx.effective_frontier.frontier_topic_id == TOPIC_RADIO
    assert ctx.effective_frontier.frontier_level == 1


def test_snapshot_accessible_topics_respect_locks(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    # Default frontier is first topic at level 1 — TOPIC_RADIO stays beyond.
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    accessible_ids = {int(t["topic_id"]) for t in snapshot.current.accessible_topics}

    assert accessible_ids == {TOPIC_MULTI}
    assert TOPIC_RADIO not in accessible_ids


def test_admin_snapshot_includes_all_topics(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _ADMIN)

    assert {int(t["topic_id"]) for t in snapshot.current.accessible_topics} == {
        TOPIC_MULTI,
        TOPIC_RADIO,
    }


def test_snapshot_level_limit_for_active_topic(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    frontier = state.chapter_frontiers[CHAPTER_ALPHA]

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)

    assert snapshot.current.level_limit_for(TOPIC_MULTI, 2) == min(
        frontier.frontier_level, 2
    )


def test_snapshot_implicit_chapter_landing_student(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_BETA] = ChapterFrontier(
        frontier_topic_id=TOPIC_SINGLE,
        frontier_level=1,
    )
    progress = state.chapter_frontiers[CHAPTER_BETA]
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.chapter_context(CHAPTER_BETA)

    topic_id, level = ctx.implicit_chapter_landing
    assert topic_id == progress.frontier_topic_id
    assert level == progress.frontier_level


def test_snapshot_implicit_chapter_landing_admin(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    # Non-default frontier on a multi-topic chapter — admin still lands on first/1.
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _ADMIN)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.implicit_chapter_landing == (TOPIC_MULTI, 1)


def test_snapshot_implicit_topic_landing(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=2,
    )
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.implicit_topic_landing(TOPIC_MULTI) == 2

    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.implicit_topic_landing(TOPIC_MULTI) == 1
    assert ctx.implicit_topic_landing(TOPIC_RADIO) == 1


def test_snapshot_can_access_locked_vs_reachable(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    # Frontier at TOPIC_MULTI level 1 — TOPIC_RADIO is beyond.
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.can_access(TOPIC_MULTI, 1) is True
    assert ctx.can_access(TOPIC_RADIO, 1) is False


def test_snapshot_progress_counts_student(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.selected_topic_id = TOPIC_RADIO
    state.selected_level = 1

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    chapter_progress = snapshot.current.chapter_progress()
    topic_progress = snapshot.current.topic_progress(
        snapshot.selected_topic_id, snapshot.selected_level
    )

    assert chapter_progress is not None
    assert chapter_progress.completed == 1  # TOPIC_MULTI is behind the frontier
    assert chapter_progress.total == 2
    assert topic_progress is not None
    assert topic_progress.completed == 0


def test_snapshot_progress_counts_admin(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _ADMIN)
    chapter_progress = snapshot.current.chapter_progress()
    topic_progress = snapshot.current.topic_progress(
        snapshot.selected_topic_id, snapshot.selected_level
    )

    assert chapter_progress is not None
    assert chapter_progress.percentage == 100.0
    assert chapter_progress.completed == 2
    assert topic_progress is not None
    assert topic_progress.percentage == 100.0
    assert topic_progress.completed == 2  # TOPIC_MULTI max_level


def test_snapshot_has_next_unlocked_topic(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_RADIO

    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is True

    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_MULTI
    snapshot = build_navigation_snapshot(state, fixture_curriculum, _STUDENT)
    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is False


def test_admin_has_next_unlocked_topic_is_false(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_RADIO

    snapshot = build_navigation_snapshot(
        state, fixture_curriculum, resolve_play_mode(state.username)
    )
    assert snapshot.current.has_next_unlocked_topic(state.selected_topic_id) is False
