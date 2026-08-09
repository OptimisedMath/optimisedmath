"""Unit tests for the session state layer."""

import sqlite3
import uuid

import pytest

import backend.config as config
import backend.session_state as session_state
from backend.core import db
from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.play_mode import AdminPlayMode, StudentPlayMode
from backend.unlock import first_topic_id
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    CHAPTER_BETA,
    TOPIC_MULTI,
    TOPIC_RADIO,
    TOPIC_SINGLE,
)

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


def _fresh_state(fixture_curriculum: Curriculum) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = "session-state-user"
    state.session_id = str(uuid.uuid4())
    return state


def _chapter_id(state: SessionState) -> int:
    assert state.selected_chapter_id is not None
    return state.selected_chapter_id


def _username(state: SessionState) -> str:
    assert state.username is not None
    return state.username


def test_init_defaults_sets_session_and_chapter_frontiers(
    fixture_curriculum: Curriculum,
):
    state = SessionState()

    session_state.init_defaults(state, fixture_curriculum)

    chapter_ids = list(fixture_curriculum.chapter_ids())
    assert state.session_id
    assert state.selected_chapter_id == CHAPTER_ALPHA
    assert state.selected_topic_id == TOPIC_MULTI
    assert state.selected_level == 1
    assert state.current_input_mode == "radio"
    for chapter_id in chapter_ids:
        assert chapter_id in state.chapter_frontiers
        assert state.chapter_frontiers[chapter_id].frontier_level == 1


def test_reset_submission_cycle_clears_problem_and_feedback(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.streak = 2
    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "oops"
    state.current_problem = {"problem_id": "p1"}

    session_state.reset_submission_cycle(state)

    assert state.streak == 0
    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.current_problem is None
    assert state.current_input_mode == "radio"


def test_resolve_input_mode_switches_to_input_after_streak_threshold(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI

    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    assert session_state.resolve_input_mode(state, fixture_curriculum) == "input"

    state.streak = 0
    assert session_state.resolve_input_mode(state, fixture_curriculum) == "radio"


def test_resolve_input_mode_stays_radio_for_radio_only_topics(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_RADIO
    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE

    assert session_state.resolve_input_mode(state, fixture_curriculum) == "radio"


def test_navigate_to_updates_selection_and_resets_submission_cycle(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.streak = 2
    state.problem_answered = True
    state.current_problem = {"problem_id": "p1"}

    session_state.navigate_to(
        state,
        topic_id=TOPIC_RADIO,
        level=1,
        curriculum=fixture_curriculum,
    )

    assert state.selected_topic_id == TOPIC_RADIO
    assert state.selected_level == 1
    assert state.streak == 0
    assert state.problem_answered is False
    assert state.current_problem is None


def test_hard_reset_wipes_progress_and_persists(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.xp = 100
    state.streak = 2
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=999,
        frontier_level=3,
    )

    session_state.hard_reset(state, fixture_curriculum)

    assert state.xp == 0
    assert state.streak == 0
    assert state.problem_answered is False
    for chapter_id in fixture_curriculum.chapter_ids():
        expected_first = first_topic_id(list(fixture_curriculum.topics(chapter_id)))
        assert state.chapter_frontiers[chapter_id].frontier_topic_id == expected_first
        assert state.chapter_frontiers[chapter_id].frontier_level == 1

    loaded = db.load_user(_username(state))
    assert loaded is not None
    assert loaded["xp"] == 0


def test_load_profile_hydrates_existing_user(fixture_curriculum: Curriculum):
    username = "existing-user"
    saved = SessionState(
        username=username,
        xp=42,
        streak=1,
        selected_chapter_id=CHAPTER_ALPHA,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        chapter_frontiers={
            CHAPTER_ALPHA: ChapterFrontier(
                frontier_topic_id=TOPIC_MULTI, frontier_level=2
            ),
            CHAPTER_BETA: ChapterFrontier(
                frontier_topic_id=TOPIC_SINGLE, frontier_level=1
            ),
        },
    )
    db.save_user(username, saved)

    state = SessionState()
    session_state.load_profile(state, username, fixture_curriculum)

    assert state.username == username
    assert state.xp == 42
    assert state.selected_level == 2
    assert state.streak == 0
    assert state.problem_answered is False


def test_load_profile_hard_resets_new_user(fixture_curriculum: Curriculum):
    state = SessionState()

    session_state.load_profile(state, "brand-new-user", fixture_curriculum)

    assert state.username == "brand-new-user"
    assert state.xp == 0
    assert state.streak == 0
    assert state.selected_chapter_id == CHAPTER_ALPHA
    assert state.selected_topic_id == TOPIC_MULTI


def test_process_submission_grades_and_persists(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    problem = {
        "problem_id": "p-correct",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
    }
    state.current_problem = problem
    session_state.sync_to_db(state)

    result = session_state.process_submission(
        state, problem, "2", False, fixture_curriculum, _STUDENT
    )

    assert result.get("is_correct") is True
    assert state.streak == 1
    assert state.problem_answered is True
    assert state.feedback_type == "success"

    loaded = db.load_user(_username(state))
    assert loaded is not None
    assert loaded["streak"] == 1


def _correct_problem() -> dict:
    return {
        "problem_id": "p-correct",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
    }


def _telemetry_count(session_id: str) -> int:
    with sqlite3.connect(db.DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM telemetry_logs WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return int(row[0])


def _admin_state_at(
    fixture_curriculum: Curriculum,
    *,
    frontier_topic_id: int,
    frontier_level: int,
    selected_topic_id: int,
    selected_level: int,
    xp: int = 0,
    streak: int = 0,
    flawless_eligible: bool = True,
) -> SessionState:
    state = _fresh_state(fixture_curriculum)
    state.username = "Antoni"
    chapter_id = _chapter_id(state)
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=frontier_topic_id,
        frontier_level=frontier_level,
    )
    state.selected_topic_id = selected_topic_id
    state.selected_level = selected_level
    state.xp = xp
    state.streak = streak
    state.flawless_eligible = flawless_eligible
    state.level_completed = False
    state.topic_completed = False
    baseline = state.model_copy(deep=True)
    baseline.streak = 0
    db.save_user(_username(state), baseline)
    db.save_session(state.session_id, _username(state), baseline)
    return state


def _wrong_problem() -> dict:
    return {
        "problem_id": "p-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
    }


def _assert_admin_profile_unchanged(
    state: SessionState,
    *,
    xp: int,
    frontier_topic_id: int,
    frontier_level: int,
) -> None:
    chapter_id = _chapter_id(state)
    assert state.xp == xp
    assert state.flawless_eligible is True
    assert state.level_completed is False
    assert state.topic_completed is False
    assert state.chapter_frontiers[chapter_id].frontier_topic_id == frontier_topic_id
    assert state.chapter_frontiers[chapter_id].frontier_level == frontier_level

    loaded = db.load_user(_username(state))
    assert loaded is not None
    assert loaded["xp"] == xp
    assert loaded["streak"] == 0
    assert loaded["chapter_frontiers"][chapter_id] == ChapterFrontier(
        frontier_topic_id=frontier_topic_id,
        frontier_level=frontier_level,
    )


@pytest.mark.parametrize(
    (
        "selected_topic_id",
        "selected_level",
        "initial_streak",
        "expect_streak",
    ),
    [
        (TOPIC_MULTI, 2, 0, 1),
        (TOPIC_RADIO, 1, 0, 1),
        (TOPIC_MULTI, 1, 1, 2),
    ],
)
def test_admin_correct_increments_session_streak_without_profile_writes(
    fixture_curriculum: Curriculum,
    selected_topic_id,
    selected_level,
    initial_streak,
    expect_streak,
):
    state = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=selected_topic_id,
        selected_level=selected_level,
        xp=50,
        streak=initial_streak,
    )
    telemetry_before = _telemetry_count(state.session_id)

    result = session_state.process_submission(
        state, _correct_problem(), "2", False, fixture_curriculum, _ADMIN
    )

    assert result.get("is_correct") is True
    assert state.feedback_type == "success"
    assert state.problem_answered is True
    assert "XP" not in state.feedback_msg
    assert _telemetry_count(state.session_id) == telemetry_before + 1
    assert state.streak == expect_streak
    _assert_admin_profile_unchanged(
        state, xp=50, frontier_topic_id=TOPIC_MULTI, frontier_level=1
    )


def test_admin_wrong_decrements_session_streak_without_profile_writes(
    fixture_curriculum: Curriculum,
):
    state = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        streak=2,
    )

    session_state.process_submission(
        state, _wrong_problem(), "3", False, fixture_curriculum, _ADMIN
    )

    assert state.streak == 1
    assert state.feedback_type == "warning"
    _assert_admin_profile_unchanged(
        state, xp=0, frontier_topic_id=TOPIC_MULTI, frontier_level=1
    )


def test_admin_ahead_of_unlock_reaches_input_mode_after_streak_threshold(
    fixture_curriculum: Curriculum,
):
    state = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        streak=0,
    )

    session_state.process_submission(
        state, _correct_problem(), "2", False, fixture_curriculum, _ADMIN
    )

    assert session_state.resolve_input_mode(state, fixture_curriculum) == "input"


def test_admin_ahead_by_topic_keeps_streak_through_unlock_threshold(
    fixture_curriculum: Curriculum,
):
    state = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_RADIO,
        selected_level=1,
        streak=2,
    )

    session_state.process_submission(
        state, _correct_problem(), "2", False, fixture_curriculum, _ADMIN
    )

    assert state.streak == 3
    _assert_admin_profile_unchanged(
        state, xp=0, frontier_topic_id=TOPIC_MULTI, frontier_level=1
    )


def test_admin_resets_streak_at_stored_frontier_boundary(
    fixture_curriculum: Curriculum,
):
    state = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=1,
        streak=2,
    )

    session_state.process_submission(
        state, _correct_problem(), "2", False, fixture_curriculum, _ADMIN
    )

    assert state.streak == 0
    _assert_admin_profile_unchanged(
        state, xp=0, frontier_topic_id=TOPIC_MULTI, frontier_level=1
    )
