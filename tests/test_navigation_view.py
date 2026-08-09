"""Unit tests for read-only navigation view building."""

import uuid

import pytest

from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.navigation_snapshot import build_navigation_snapshot
from backend import navigation_view as view
from backend.play_mode import AdminPlayMode, StudentPlayMode
import backend.session_state as session_state
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    CHAPTER_BETA,
    TOPIC_MULTI,
    TOPIC_RADIO,
)

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


def _fresh_state(
    fixture_curriculum: Curriculum, *, username: str = "nav-view-user"
) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = username
    state.session_id = str(uuid.uuid4())
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = 1
    return state


def _build_view(state: SessionState, fixture_curriculum: Curriculum, play_mode):
    snapshot = build_navigation_snapshot(state, fixture_curriculum, play_mode)
    return view.build_navigation_view(snapshot)


def test_view_chapters_come_from_snapshot_curriculum(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    nav = _build_view(state, fixture_curriculum, _STUDENT)

    assert [(c.chapter_id, c.name) for c in nav.available_chapters] == [
        (CHAPTER_ALPHA, "Chapter Alpha"),
        (CHAPTER_BETA, "Chapter Beta"),
    ]


def test_student_available_topics_respect_locks(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    # Default frontier is TOPIC_MULTI — TOPIC_RADIO stays locked.
    nav = _build_view(state, fixture_curriculum, _STUDENT)

    assert [t.topic_id for t in nav.available_topics] == [TOPIC_MULTI]
    assert nav.current_topic_name == "Multi Level Topic"


def test_admin_sees_all_topics(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    nav = _build_view(state, fixture_curriculum, _ADMIN)

    assert [t.topic_id for t in nav.available_topics] == [TOPIC_MULTI, TOPIC_RADIO]


def test_student_available_levels_respect_frontier(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )
    nav = _build_view(state, fixture_curriculum, _STUDENT)

    assert nav.available_levels == [1]


def test_admin_available_levels_are_full_topic_max(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    nav = _build_view(state, fixture_curriculum, _ADMIN)

    assert nav.available_levels == [1, 2]


def test_student_radio_only_flag_follows_active_topic(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    nav = _build_view(state, fixture_curriculum, _STUDENT)
    assert nav.radio_only is False

    state.selected_topic_id = TOPIC_RADIO
    nav = _build_view(state, fixture_curriculum, _STUDENT)
    assert nav.radio_only is True


def test_admin_radio_only_flag_follows_active_topic(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.selected_topic_id = TOPIC_RADIO
    nav = _build_view(state, fixture_curriculum, _ADMIN)

    assert nav.radio_only is True


def test_student_progress_bars(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.selected_topic_id = TOPIC_RADIO
    state.selected_level = 1

    nav = _build_view(state, fixture_curriculum, _STUDENT)

    assert nav.chapter_completion is not None
    assert nav.chapter_completion.completed == 1
    assert nav.chapter_completion.total == 2
    assert nav.chapter_completion.percentage == pytest.approx(50.0)
    assert nav.topic_completion is not None
    assert nav.topic_completion.completed == 0
    assert nav.topic_completion.total == 1
    assert nav.topic_completion.percentage == pytest.approx(0.0)


def test_admin_progress_bars_show_full_completion(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    nav = _build_view(state, fixture_curriculum, _ADMIN)

    assert nav.chapter_completion is not None
    assert nav.chapter_completion.percentage == 100.0
    assert nav.chapter_completion.completed == 2
    assert nav.chapter_completion.total == 2
    assert nav.topic_completion is not None
    assert nav.topic_completion.percentage == 100.0
    assert nav.topic_completion.completed == 2
    assert nav.topic_completion.total == 2


def test_student_has_next_unlocked_topic(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_RADIO

    nav = _build_view(state, fixture_curriculum, _STUDENT)
    assert nav.has_next_unlocked_topic is True

    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_MULTI
    nav = _build_view(state, fixture_curriculum, _STUDENT)
    assert nav.has_next_unlocked_topic is False


def test_admin_has_next_unlocked_topic_is_false(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.selected_topic_id = TOPIC_MULTI
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_RADIO

    nav = _build_view(state, fixture_curriculum, _ADMIN)
    assert nav.has_next_unlocked_topic is False
