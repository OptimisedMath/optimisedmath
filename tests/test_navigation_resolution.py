"""Unit tests for navigation intent resolution (pure rules)."""

import uuid

import pytest

from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState, SessionNavigateRequest
from backend.navigation import build_navigation_snapshot
from backend.play_mode import AdminPlayMode, StudentPlayMode
from backend.navigation import _get_level_options as get_level_options
import backend.navigation as resolution
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
    fixture_curriculum: Curriculum, *, username: str = "nav-resolution-user"
) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = username
    state.session_id = str(uuid.uuid4())
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = 1
    return state


def _snapshot(state: SessionState, fixture_curriculum: Curriculum, play_mode=_STUDENT):
    return build_navigation_snapshot(state, fixture_curriculum, play_mode)


def test_get_level_options_returns_one_through_limit():
    assert get_level_options(3) == [1, 2, 3]
    assert get_level_options(0) == [1]
    assert get_level_options(1) == [1]


def test_resolve_chapter_change_uses_unlocked_topic_and_level(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_BETA] = ChapterFrontier(
        frontier_topic_id=TOPIC_SINGLE,
        frontier_level=1,
    )

    chapter_id, topic_id, level = resolution.resolve_chapter_change(
        CHAPTER_BETA, _snapshot(state, fixture_curriculum)
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_BETA, TOPIC_SINGLE, 1)


def test_resolve_topic_change_resets_level_for_completed_topic(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )

    topic_id, level = resolution.resolve_topic_change(
        CHAPTER_ALPHA,
        TOPIC_MULTI,
        _snapshot(state, fixture_curriculum),
    )

    assert topic_id == TOPIC_MULTI
    assert level == 1


def test_clamp_selected_level_caps_stale_level(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    max_level = int(fixture_curriculum.topic(CHAPTER_ALPHA, TOPIC_MULTI)["max_level"])

    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = max_level + 10

    resolution.clamp_selected_level(state, fixture_curriculum)

    assert state.selected_level == max_level


def test_resolve_navigate_request_chapter_change(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_BETA] = ChapterFrontier(
        frontier_topic_id=TOPIC_SINGLE,
        frontier_level=1,
    )
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=CHAPTER_BETA,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, request, _snapshot(state, fixture_curriculum)
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_BETA, TOPIC_SINGLE, 1)


def test_resolve_navigate_request_topic_only(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_topic_id=TOPIC_RADIO,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, request, _snapshot(state, fixture_curriculum)
    )

    assert chapter_id == CHAPTER_ALPHA
    assert topic_id == TOPIC_RADIO
    assert level == 1


def test_resolve_navigate_request_level_only(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=2,
    )

    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_level=2,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, request, _snapshot(state, fixture_curriculum)
    )

    assert chapter_id == CHAPTER_ALPHA
    assert topic_id == TOPIC_MULTI
    assert level == 2


def test_resolve_navigate_request_none_keeps_selection(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_level = 2
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=2,
    )
    request = SessionNavigateRequest(session_id=state.session_id)

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, request, _snapshot(state, fixture_curriculum)
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_ALPHA, TOPIC_MULTI, 2)


def test_admin_chapter_change_lands_on_first_topic_at_level_one(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.selected_chapter_id = CHAPTER_BETA
    state.selected_topic_id = TOPIC_SINGLE
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )

    chapter_id, topic_id, level = resolution.resolve_chapter_change(
        CHAPTER_ALPHA, _snapshot(state, fixture_curriculum, _ADMIN)
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_ALPHA, TOPIC_MULTI, 1)


def test_admin_topic_change_lands_on_level_one(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=2,
    )

    topic_id, level = resolution.resolve_topic_change(
        CHAPTER_ALPHA,
        TOPIC_MULTI,
        _snapshot(state, fixture_curriculum, _ADMIN),
    )

    assert (topic_id, level) == (TOPIC_MULTI, 1)


def test_admin_explicit_topic_and_level_unchanged(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    explicit_level = 2

    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_topic_id=TOPIC_MULTI,
        selected_level=explicit_level,
    )

    chapter_id, topic_id, level = resolution.resolve_navigate_request(
        state, request, _snapshot(state, fixture_curriculum, _ADMIN)
    )

    assert (chapter_id, topic_id, level) == (
        CHAPTER_ALPHA,
        TOPIC_MULTI,
        explicit_level,
    )


# --- resolve_navigation_target (validate-and-resolve) ---


def test_resolve_navigation_target_returns_reachable_target(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=CHAPTER_ALPHA,
        selected_topic_id=TOPIC_MULTI,
        selected_level=1,
    )

    chapter_id, topic_id, level = resolution.resolve_navigation_target(
        state,
        request,
        _snapshot(state, fixture_curriculum),
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_ALPHA, TOPIC_MULTI, 1)


def test_resolve_navigation_target_raises_for_missing_chapter(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    request = SessionNavigateRequest(
        session_id=state.session_id, selected_chapter_id=999
    )

    with pytest.raises(resolution.NavigationChapterNotFoundError) as exc_info:
        resolution.resolve_navigation_target(
            state,
            request,
            _snapshot(state, fixture_curriculum),
        )
    assert str(exc_info.value) == "Chapter id 999 not found in curriculum"


def test_resolve_navigation_target_raises_for_missing_topic(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    request = SessionNavigateRequest(session_id=state.session_id, selected_topic_id=999)

    with pytest.raises(resolution.NavigationTopicNotFoundError) as exc_info:
        resolution.resolve_navigation_target(
            state,
            request,
            _snapshot(state, fixture_curriculum),
        )
    assert str(exc_info.value) == "Topic id 999 not found in curriculum"


def test_resolve_navigation_target_raises_for_out_of_range_level(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
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
            request,
            _snapshot(state, fixture_curriculum),
        )
    assert str(exc_info.value) == (
        f"Level 99 is not available for topic id {TOPIC_MULTI}"
    )


def test_resolve_navigation_target_raises_for_locked_topic(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
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
            request,
            _snapshot(state, fixture_curriculum),
        )
    assert str(exc_info.value) == "Topic is locked"


def test_resolve_navigation_target_raises_for_locked_level(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
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
            request,
            _snapshot(state, fixture_curriculum),
        )
    assert str(exc_info.value) == "Level is locked"


def test_resolve_navigation_target_admin_bypasses_frontier_but_not_bounds(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
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
        request,
        _snapshot(state, fixture_curriculum, _ADMIN),
    )

    assert (chapter_id, topic_id, level) == (CHAPTER_ALPHA, TOPIC_RADIO, 1)
