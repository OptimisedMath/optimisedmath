import uuid

import pytest

from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.navigation_snapshot import build_navigation_snapshot, build_navigation_view
from backend.navigation_snapshot import _get_level_options as get_level_options
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


def test_get_level_options_returns_one_through_limit():
    assert get_level_options(3) == [1, 2, 3]
    assert get_level_options(0) == [1]
    assert get_level_options(1) == [1]


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


def test_chapter_context_returns_the_same_value_for_a_chapter_id_every_time(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)

    first = snapshot.chapter_context(CHAPTER_BETA)
    second = snapshot.chapter_context(CHAPTER_BETA)

    assert first is second


def test_chapter_context_is_distinct_per_chapter_id(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)

    alpha_ctx = snapshot.chapter_context(CHAPTER_ALPHA)
    beta_ctx = snapshot.chapter_context(CHAPTER_BETA)

    assert alpha_ctx is not beta_ctx
    assert alpha_ctx.chapter_id == CHAPTER_ALPHA
    assert beta_ctx.chapter_id == CHAPTER_BETA


# An unvalidated client chapter id can reach chapter_context() before the
# caller has checked it exists — this must fall back, not read live state.
def test_chapter_context_for_unknown_chapter_id_does_not_raise(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)

    ctx = snapshot.chapter_context(999999)

    assert ctx.chapter_id == 999999
    assert ctx.chapter_topics == ()


# --- Snapshot answers do not move after the Session it was built from mutates ---


def test_snapshot_selected_fields_do_not_move_after_state_mutates(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    snapshot, view = _build(state, fixture_curriculum, _STUDENT)

    state.selected_chapter_id = CHAPTER_BETA
    state.selected_topic_id = TOPIC_SINGLE
    state.selected_level = 2

    assert snapshot.selected_chapter_id == CHAPTER_ALPHA
    assert snapshot.selected_topic_id == TOPIC_MULTI
    assert snapshot.selected_level == 1
    assert view.current_topic_name == "Multi Level Topic"


# Reachability read off a chapter's context must not change because the
# Session's chapter_frontiers dict was mutated after the snapshot was built —
# the snapshot holds no live reference into it.
def test_chapter_context_answers_do_not_move_after_frontier_mutates(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )
    snapshot, _ = _build(state, fixture_curriculum, _STUDENT)
    before = snapshot.chapter_context(CHAPTER_ALPHA)
    before_accessible = {int(t["topic_id"]) for t in before.accessible_topics}

    state.chapter_frontiers[CHAPTER_ALPHA].frontier_topic_id = TOPIC_RADIO
    state.chapter_frontiers[CHAPTER_ALPHA].frontier_level = 1

    after = snapshot.chapter_context(CHAPTER_ALPHA)
    after_accessible = {int(t["topic_id"]) for t in after.accessible_topics}

    assert after is before
    assert after_accessible == before_accessible
    assert TOPIC_RADIO not in after_accessible


# The same Navigation must not depend on the order chapters are asked
# about — asking about one chapter first must not change what a later
# question about another chapter (or the same chapter again) returns.
def test_chapter_context_answers_are_the_same_regardless_of_which_chapter_is_asked_first(
    fixture_curriculum: Curriculum,
):
    state_ask_alpha_first = _fresh_state(fixture_curriculum)
    state_ask_beta_first = _fresh_state(fixture_curriculum)
    for state in (state_ask_alpha_first, state_ask_beta_first):
        state.chapter_frontiers[CHAPTER_BETA] = ChapterFrontier(
            frontier_topic_id=TOPIC_SINGLE,
            frontier_level=1,
        )

    snapshot_a, _ = _build(state_ask_alpha_first, fixture_curriculum, _STUDENT)
    snapshot_a.chapter_context(CHAPTER_ALPHA)
    beta_after_alpha = snapshot_a.chapter_context(CHAPTER_BETA)

    snapshot_b, _ = _build(state_ask_beta_first, fixture_curriculum, _STUDENT)
    beta_first = snapshot_b.chapter_context(CHAPTER_BETA)
    snapshot_b.chapter_context(CHAPTER_ALPHA)

    assert (
        beta_after_alpha.implicit_chapter_landing == beta_first.implicit_chapter_landing
    )
    assert beta_after_alpha.resolve_frontier == beta_first.resolve_frontier


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
    ctx = snapshot.selected_chapter_context
    frontier = state.chapter_frontiers[CHAPTER_ALPHA]

    assert ctx.resolve_frontier.frontier_topic_id == frontier.frontier_topic_id
    assert ctx.resolve_frontier.frontier_level == frontier.frontier_level
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

    assert (
        snapshot.selected_chapter_context.has_next_unlocked_topic(
            state.selected_topic_id
        )
        is True
    )
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
    ctx = snapshot.selected_chapter_context

    accessible_ids = {int(t["topic_id"]) for t in ctx.accessible_topics}
    assert accessible_ids == {TOPIC_MULTI, TOPIC_RADIO}
    assert [t.topic_id for t in view.available_topics] == [TOPIC_MULTI, TOPIC_RADIO]
    assert view.current_topic_name == "Multi Level Topic"
    assert view.available_levels == [1, 2]
    assert ctx.is_reachable(TOPIC_MULTI, 1) is True
    assert ctx.is_reachable(TOPIC_MULTI, 2) is True


def test_student_behind_frontier_progress(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.selected_topic_id = TOPIC_RADIO
    state.selected_level = 1

    snapshot, view = _build(state, fixture_curriculum, _STUDENT)
    chapter_progress = snapshot.selected_chapter_context.chapter_progress()
    topic_progress = snapshot.selected_chapter_context.topic_progress(
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
    ctx = snapshot.selected_chapter_context

    accessible_ids = {int(t["topic_id"]) for t in ctx.accessible_topics}
    assert accessible_ids == {TOPIC_MULTI}
    assert TOPIC_RADIO not in accessible_ids
    assert [t.topic_id for t in view.available_topics] == [TOPIC_MULTI]
    assert ctx.is_reachable(TOPIC_MULTI, 1) is True
    assert ctx.is_reachable(TOPIC_RADIO, 1) is False


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
    ctx = snapshot.selected_chapter_context

    assert ctx.resolve_frontier.frontier_topic_id == TOPIC_RADIO
    assert ctx.resolve_frontier.frontier_level == 1
    assert {int(t["topic_id"]) for t in ctx.accessible_topics} == {
        TOPIC_MULTI,
        TOPIC_RADIO,
    }
    assert [t.topic_id for t in view.available_topics] == [TOPIC_MULTI, TOPIC_RADIO]
    assert view.available_levels == [1, 2]


def test_admin_progress_bars_show_full_completion(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    snapshot, view = _build(state, fixture_curriculum, _ADMIN)
    chapter_progress = snapshot.selected_chapter_context.chapter_progress()
    topic_progress = snapshot.selected_chapter_context.topic_progress(
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

    assert (
        snapshot.selected_chapter_context.has_next_unlocked_topic(
            state.selected_topic_id
        )
        is False
    )
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


def test_snapshot_implicit_topic_landing_student(fixture_curriculum: Curriculum):
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


def test_snapshot_implicit_topic_landing_admin(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum, username="Antoni")
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=2,
    )

    snapshot, _ = _build(state, fixture_curriculum, _ADMIN)
    ctx = snapshot.chapter_context(CHAPTER_ALPHA)

    assert ctx.implicit_topic_landing(TOPIC_MULTI) == 1
    assert ctx.implicit_topic_landing(TOPIC_RADIO) == 1
