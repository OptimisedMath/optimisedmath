"""Internal-seam tests for the Submission cycle module."""

import uuid

import pytest

import backend.config as config
import backend.navigation_snapshot as navigation_snapshot
import backend.submission_cycle as submission_cycle
from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.play_mode import PlayMode, StudentPlayMode
import backend.session_state as session_state
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    TOPIC_MULTI,
    TOPIC_RADIO,
)


def _fresh_state(fixture_curriculum: Curriculum) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = "submission-cycle-user"
    state.session_id = str(uuid.uuid4())
    return state


def _snapshot(
    state: SessionState, curriculum: Curriculum, play_mode: PlayMode
) -> navigation_snapshot.NavigationSnapshot:
    return navigation_snapshot.build_navigation_snapshot(state, curriculum, play_mode)


def test_clear_submission_cycle_fields_clears_problem_and_feedback(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.streak = 2
    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "oops"
    state.current_problem = {"problem_id": "p1"}

    session_state.clear_submission_cycle_fields(state)

    assert state.streak == 0
    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.current_problem is None
    assert state.current_input_mode == "radio"


def test_navigate_to_updates_selection_and_resets_submission_cycle(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.streak = 2
    state.problem_answered = True
    state.current_problem = {"problem_id": "p1"}

    submission_cycle.navigate_to(
        state,
        StudentPlayMode(),
        topic_id=TOPIC_RADIO,
        level=1,
        curriculum=fixture_curriculum,
    )

    assert state.selected_topic_id == TOPIC_RADIO
    assert state.selected_level == 1
    assert state.streak == 0
    assert state.problem_answered is False
    assert state.current_problem is None


def test_begin_problem_resets_submission_state_and_sets_problem(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    problem = {
        "problem_id": "p1",
        "question": "2+2",
        "correct": "4",
        "options": ["4", "5"],
    }

    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "wrong"
    state.level_completed = True
    state.topic_completed = True
    state.streak = 2

    submission_cycle.begin_problem(
        state, problem, fixture_curriculum, StudentPlayMode()
    )

    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.level_completed is False
    assert state.topic_completed is False
    assert state.current_problem is problem
    assert state.problem_start_time is not None
    assert state.streak == 2


def test_begin_problem_trims_recent_fingerprints(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    problem = {"problem_id": "p1", "question": "q", "correct": "1", "options": ["1"]}

    fingerprints = [
        f"fp-{index}" for index in range(config.RECENT_FINGERPRINT_HISTORY_SIZE + 3)
    ]
    submission_cycle.begin_problem(
        state,
        problem,
        fixture_curriculum,
        StudentPlayMode(),
        recent_fingerprints=fingerprints,
    )

    assert (
        len(state.recent_problem_fingerprints) == config.RECENT_FINGERPRINT_HISTORY_SIZE
    )
    assert (
        state.recent_problem_fingerprints
        == fingerprints[-config.RECENT_FINGERPRINT_HISTORY_SIZE :]
    )


def test_begin_problem_resolves_input_mode_from_streak(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    problem = {"problem_id": "p1", "question": "q", "correct": "1", "options": ["1"]}

    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    submission_cycle.begin_problem(
        state, problem, fixture_curriculum, StudentPlayMode()
    )

    assert state.current_input_mode == "input"


def test_resolve_next_problem_navigates_to_frontier_topic(
    fixture_curriculum: Curriculum,
    monkeypatch: pytest.MonkeyPatch,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = 2
    state.problem_answered = True
    state.topic_completed = True
    state.level_completed = True
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.current_problem = {
        "problem_id": "completed",
        "question": "q",
        "correct": "1",
        "options": ["1", "2"],
    }
    served_problem = {
        "problem_id": "served",
        "question": "q",
        "correct": "1",
        "options": ["1", "2"],
    }

    def _fake_serve_next_problem(*_args, **_kwargs):
        return served_problem

    monkeypatch.setattr(
        submission_cycle, "serve_next_problem", _fake_serve_next_problem
    )

    problem = submission_cycle.resolve_next_problem(
        state,
        fixture_curriculum,
        CHAPTER_ALPHA,
        TOPIC_MULTI,
        play_mode=StudentPlayMode(),
        nav_snapshot=_snapshot(state, fixture_curriculum, StudentPlayMode()),
    )

    assert state.selected_topic_id == TOPIC_RADIO
    assert state.selected_level == 1
    assert state.topic_completed is False
    assert state.problem_answered is False
    assert problem is served_problem


def test_resolve_next_problem_chapter_end_returns_current_problem(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    completed_problem = {
        "problem_id": "chapter-end",
        "question": "q",
        "correct": "1",
        "options": ["1", "2"],
    }
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_RADIO
    state.selected_level = 1
    state.problem_answered = True
    state.topic_completed = True
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.current_problem = completed_problem

    problem = submission_cycle.resolve_next_problem(
        state,
        fixture_curriculum,
        CHAPTER_ALPHA,
        TOPIC_RADIO,
        play_mode=StudentPlayMode(),
        nav_snapshot=_snapshot(state, fixture_curriculum, StudentPlayMode()),
    )

    assert problem is completed_problem
    assert state.selected_topic_id == TOPIC_RADIO
    assert state.selected_level == 1
    assert state.topic_completed is True
    assert state.problem_answered is True


def test_resolve_next_problem_chapter_end_raises_without_active_problem(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_RADIO
    state.selected_level = 1
    state.problem_answered = True
    state.topic_completed = True
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=1,
    )
    state.current_problem = None

    with pytest.raises(submission_cycle.NoActiveProblemError):
        submission_cycle.resolve_next_problem(
            state,
            fixture_curriculum,
            CHAPTER_ALPHA,
            TOPIC_RADIO,
            play_mode=StudentPlayMode(),
            nav_snapshot=_snapshot(state, fixture_curriculum, StudentPlayMode()),
        )
