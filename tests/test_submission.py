from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Any

import pytest

import backend.config as config
import backend.session_state as session_state
import backend.submission as submission
from backend.core import db
from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.play_mode import AdminPlayMode, StudentPlayMode
from backend.progression import SubmissionOutcome
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    TOPIC_MULTI,
    TOPIC_RADIO,
)

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()

_TELEMETRY_STRIP_KEYS = frozenset(
    {
        "image_html",
        "messages",
        "options",
        "options_map",
        "level",
        "level_name",
        "level_display",
    }
)


@dataclass(frozen=True)
class ExpectedSession:
    streak: int
    flawless_eligible: bool
    xp: int
    feedback_type: str | None
    feedback_msg: str
    level_completed: bool
    topic_completed: bool
    selected_level: int
    frontier_level: int
    frontier_topic_id: int
    problem_answered: bool


@dataclass(frozen=True)
class ExpectedTelemetry:
    is_correct: bool
    user_input: str
    chapter: str
    topic: str
    level_number: int
    is_input_mode: bool
    answer_outcome: str | None = None
    misconception_slug: str | None = None
    trap_slug: str | None = None


def _fresh_state(
    fixture_curriculum: Curriculum, *, username: str = "submission-user"
) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = username
    state.session_id = str(uuid.uuid4())
    return state


def _chapter_id(state: SessionState) -> int:
    assert state.selected_chapter_id is not None
    return state.selected_chapter_id


def _username(state: SessionState) -> str:
    assert state.username is not None
    return state.username


def _student_state_at(
    fixture_curriculum: Curriculum,
    *,
    selected_topic_id: int = TOPIC_MULTI,
    selected_level: int = 1,
    streak: int = 0,
    xp: int = 0,
    flawless_eligible: bool = True,
    frontier_topic_id: int = TOPIC_MULTI,
    frontier_level: int = 1,
) -> SessionState:
    state = _fresh_state(fixture_curriculum)
    chapter_id = _chapter_id(state)
    state.selected_topic_id = selected_topic_id
    state.selected_level = selected_level
    state.streak = streak
    state.xp = xp
    state.flawless_eligible = flawless_eligible
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=frontier_topic_id,
        frontier_level=frontier_level,
    )
    return state


@dataclass(frozen=True)
class AdminProfileBaseline:
    xp: int
    streak: int
    chapter_frontiers: dict[int, ChapterFrontier]


def _admin_state_at(
    fixture_curriculum: Curriculum,
    *,
    frontier_topic_id: int = TOPIC_MULTI,
    frontier_level: int = 1,
    selected_topic_id: int = TOPIC_MULTI,
    selected_level: int = 1,
    xp: int = 0,
    streak: int = 0,
    flawless_eligible: bool = True,
) -> tuple[SessionState, AdminProfileBaseline]:
    state = _fresh_state(fixture_curriculum, username="Antoni")
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
    baseline_state = state.model_copy(deep=True)
    baseline_state.streak = 0
    db.save_user(_username(state), baseline_state)
    db.save_session(state.session_id, _username(state), baseline_state)
    baseline = AdminProfileBaseline(
        xp=baseline_state.xp,
        streak=baseline_state.streak,
        chapter_frontiers=dict(baseline_state.chapter_frontiers),
    )
    return state, baseline


def _correct_problem() -> dict[str, Any]:
    return {
        "problem_id": "p-correct",
        "question": "What is 2+2?",
        "correct": "2",
        "image_html": "<svg></svg>",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
        "level": 1,
        "level_name": "Easy",
        "level_display": "Level 1",
    }


def _wrong_problem() -> dict[str, Any]:
    return {
        "problem_id": "p-wrong",
        "question": "What is 2+2?",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
    }


def _trap_problem() -> dict[str, Any]:
    return {
        "problem_id": "p-trap",
        "question": "q",
        "correct": "1/2",
        "options_map": {"1/3": "t1"},
        "messages": {"t1": "Trap feedback"},
    }


def _soft_error_problem() -> dict[str, Any]:
    return {
        "problem_id": "p-soft-error",
        "question": "q",
        "correct": "1/2",
    }


def _submit(
    state: SessionState,
    problem: dict[str, Any],
    user_input: str,
    is_input_mode: bool,
    curriculum: Curriculum,
    play_mode: StudentPlayMode | AdminPlayMode,
) -> dict[str, Any]:
    state.current_problem = problem
    state.problem_start_time = 0
    session_state.persist(state, play_mode)
    return submission.run_submission_cycle(
        state, problem, user_input, is_input_mode, curriculum, play_mode
    )


def _telemetry_count(session_id: str) -> int:
    with sqlite3.connect(db.DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM telemetry_logs WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return int(row[0])


def _latest_telemetry(session_id: str) -> tuple[Any, ...]:
    with sqlite3.connect(db.DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT problem_snapshot, is_correct, user_input, chapter, topic,
                   level_number, is_input_mode, answer_outcome, misconception_slug,
                   trap_slug
            FROM telemetry_logs
            WHERE session_id = ?
            ORDER BY log_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
    assert row is not None, "expected one telemetry row for session"
    return row


def _assert_session(state: SessionState, expected: ExpectedSession) -> None:
    chapter_id = _chapter_id(state)
    frontier = state.chapter_frontiers[chapter_id]
    assert state.streak == expected.streak
    assert state.flawless_eligible is expected.flawless_eligible
    assert state.xp == expected.xp
    assert state.feedback_type == expected.feedback_type
    assert expected.feedback_msg in state.feedback_msg
    assert state.level_completed is expected.level_completed
    assert state.topic_completed is expected.topic_completed
    assert state.selected_level == expected.selected_level
    assert frontier.frontier_level == expected.frontier_level
    assert frontier.frontier_topic_id == expected.frontier_topic_id
    assert state.problem_answered is expected.problem_answered


def _assert_telemetry(
    session_id: str,
    problem: dict[str, Any],
    expected: ExpectedTelemetry,
) -> None:
    row = _latest_telemetry(session_id)
    stored = json.loads(row[0])
    for key in _TELEMETRY_STRIP_KEYS:
        assert key not in stored
    assert stored["question"] == problem["question"]
    assert stored["correct"] == problem["correct"]
    assert row[1] == (1 if expected.is_correct else 0)
    assert row[2] == expected.user_input
    assert row[3] == expected.chapter
    assert row[4] == expected.topic
    assert row[5] == expected.level_number
    assert row[6] == (1 if expected.is_input_mode else 0)
    assert row[7] == expected.answer_outcome
    assert row[8] == expected.misconception_slug
    assert row[9] == expected.trap_slug


def _assert_admin_profile_unchanged(
    state: SessionState,
    baseline: AdminProfileBaseline,
) -> None:
    loaded = db.load_user(_username(state))
    assert loaded is not None
    assert loaded["xp"] == baseline.xp
    assert loaded["streak"] == baseline.streak
    assert loaded["chapter_frontiers"] == baseline.chapter_frontiers


# --- Feedback merge ---


def test_resolve_feedback_uses_grading_when_progression_is_silent():
    eval_result = {"feedback_type": "warning", "feedback_msg": "Try again"}
    outcome = SubmissionOutcome(new_streak=1, new_flawless_eligible=False, xp_earned=0)

    feedback_type, feedback_msg = submission._resolve_feedback(eval_result, outcome)

    assert feedback_type == "warning"
    assert feedback_msg == "Try again"


def test_resolve_feedback_prefers_progression_override():
    eval_result = {"feedback_type": "warning", "feedback_msg": "ignored"}
    outcome = SubmissionOutcome(
        new_streak=1,
        new_flawless_eligible=True,
        xp_earned=10,
        feedback_type="success",
        feedback_msg="Brawo! (+10 XP)",
    )

    feedback_type, feedback_msg = submission._resolve_feedback(eval_result, outcome)

    assert feedback_type == "success"
    assert feedback_msg == "Brawo! (+10 XP)"


# --- Correct answer ---


def test_correct_answer_updates_session_and_logs_telemetry(
    fixture_curriculum: Curriculum,
):
    state = _student_state_at(fixture_curriculum, streak=0, xp=10)
    problem = _correct_problem()
    telemetry_before = _telemetry_count(state.session_id)

    result = _submit(state, problem, "2", False, fixture_curriculum, _STUDENT)

    assert result.get("is_correct") is True
    _assert_session(
        state,
        ExpectedSession(
            streak=1,
            flawless_eligible=True,
            xp=10 + config.XP_REWARDS[1],
            feedback_type="success",
            feedback_msg=f"(+{config.XP_REWARDS[1]} XP)",
            level_completed=False,
            topic_completed=False,
            selected_level=1,
            frontier_level=1,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=True,
        ),
    )
    assert _telemetry_count(state.session_id) == telemetry_before + 1
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=True,
            user_input="2",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=1,
            is_input_mode=False,
        ),
    )
    loaded = db.load_user(_username(state))
    assert loaded is not None
    assert loaded["streak"] == 1
    assert loaded["xp"] == 10 + config.XP_REWARDS[1]


# --- Penalized mistake ---


def test_penalized_mistake_decrements_streak_and_forfeits_flawless(
    fixture_curriculum: Curriculum,
):
    state = _student_state_at(fixture_curriculum, streak=2, flawless_eligible=True)
    problem = _wrong_problem()
    telemetry_before = _telemetry_count(state.session_id)

    result = _submit(state, problem, "3", False, fixture_curriculum, _STUDENT)

    assert result.get("is_correct") is not True
    _assert_session(
        state,
        ExpectedSession(
            streak=1,
            flawless_eligible=False,
            xp=0,
            feedback_type="warning",
            feedback_msg="Try again",
            level_completed=False,
            topic_completed=False,
            selected_level=1,
            frontier_level=1,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=True,
        ),
    )
    assert _telemetry_count(state.session_id) == telemetry_before + 1
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=False,
            user_input="3",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=1,
            is_input_mode=False,
            answer_outcome="trap",
            trap_slug="w1",
        ),
    )


# --- Soft error ---


def test_soft_error_preserves_streak_and_flawless(fixture_curriculum: Curriculum):
    state = _student_state_at(fixture_curriculum, streak=2, flawless_eligible=True)
    problem = _soft_error_problem()
    telemetry_before = _telemetry_count(state.session_id)

    result = _submit(state, problem, "2/4", True, fixture_curriculum, _STUDENT)

    assert result.get("is_correct") is None
    _assert_session(
        state,
        ExpectedSession(
            streak=2,
            flawless_eligible=True,
            xp=0,
            feedback_type="info",
            feedback_msg="najprostszej postaci",
            level_completed=False,
            topic_completed=False,
            selected_level=1,
            frontier_level=1,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=False,
        ),
    )
    assert _telemetry_count(state.session_id) == telemetry_before + 1
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=False,
            user_input="2/4",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=1,
            is_input_mode=True,
            answer_outcome="unsimplified",
        ),
    )


# --- Trap ---


def test_trap_answer_sets_warning_feedback_and_logs_answer_outcome(
    fixture_curriculum: Curriculum,
):
    state = _student_state_at(fixture_curriculum, streak=2, flawless_eligible=True)
    problem = _trap_problem()
    telemetry_before = _telemetry_count(state.session_id)

    result = _submit(state, problem, "1/3", True, fixture_curriculum, _STUDENT)

    assert result.get("is_correct") is None
    _assert_session(
        state,
        ExpectedSession(
            streak=1,
            flawless_eligible=False,
            xp=0,
            feedback_type="warning",
            feedback_msg="Trap feedback",
            level_completed=False,
            topic_completed=False,
            selected_level=1,
            frontier_level=1,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=True,
        ),
    )
    assert _telemetry_count(state.session_id) == telemetry_before + 1
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=False,
            user_input="1/3",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=1,
            is_input_mode=True,
            answer_outcome="trap",
            trap_slug="t1",
        ),
    )


# --- Level completion ---


def test_level_completion_unlocks_frontier_and_awards_flawless_bonus(
    fixture_curriculum: Curriculum,
):
    state = _student_state_at(
        fixture_curriculum,
        streak=2,
        flawless_eligible=True,
        selected_level=1,
        frontier_level=1,
    )
    problem = _correct_problem()
    base_xp = config.XP_REWARDS[1]
    expected_xp = base_xp + config.FLAWLESS_LEVEL_BONUS

    result = _submit(state, problem, "2", False, fixture_curriculum, _STUDENT)

    assert result.get("is_correct") is True
    _assert_session(
        state,
        ExpectedSession(
            streak=0,
            flawless_eligible=True,
            xp=expected_xp,
            feedback_type="success",
            feedback_msg="Flawless Bonus",
            level_completed=True,
            topic_completed=False,
            selected_level=2,
            frontier_level=2,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=True,
        ),
    )
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=True,
            user_input="2",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=1,
            is_input_mode=False,
        ),
    )


# --- Topic completion ---


def test_topic_completion_moves_frontier_to_next_topic(fixture_curriculum: Curriculum):
    state = _student_state_at(
        fixture_curriculum,
        streak=2,
        flawless_eligible=True,
        selected_level=2,
        frontier_level=2,
    )
    problem = _correct_problem()

    result = _submit(state, problem, "2", False, fixture_curriculum, _STUDENT)

    assert result.get("is_correct") is True
    _assert_session(
        state,
        ExpectedSession(
            streak=0,
            flawless_eligible=True,
            xp=config.XP_REWARDS[2] + config.FLAWLESS_LEVEL_BONUS,
            feedback_type="success",
            feedback_msg="Flawless Bonus",
            level_completed=True,
            topic_completed=True,
            selected_level=2,
            frontier_level=1,
            frontier_topic_id=TOPIC_RADIO,
            problem_answered=True,
        ),
    )
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=True,
            user_input="2",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=2,
            is_input_mode=False,
        ),
    )


# --- Admin ---


@pytest.mark.parametrize(
    ("selected_topic_id", "selected_level", "initial_streak", "expect_streak"),
    [
        (TOPIC_MULTI, 2, 0, 1),
        (TOPIC_RADIO, 1, 0, 1),
        (TOPIC_MULTI, 1, 1, 2),
    ],
)
def test_admin_correct_increments_session_streak_without_profile_writes(
    fixture_curriculum: Curriculum,
    selected_topic_id: int,
    selected_level: int,
    initial_streak: int,
    expect_streak: int,
):
    state, baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=selected_topic_id,
        selected_level=selected_level,
        xp=50,
        streak=initial_streak,
    )
    problem = _correct_problem()
    telemetry_before = _telemetry_count(state.session_id)

    result = _submit(state, problem, "2", False, fixture_curriculum, _ADMIN)

    assert result.get("is_correct") is True
    assert "XP" not in (state.feedback_msg or "")
    assert _telemetry_count(state.session_id) == telemetry_before + 1
    _assert_session(
        state,
        ExpectedSession(
            streak=expect_streak,
            flawless_eligible=True,
            xp=50,
            feedback_type="success",
            feedback_msg="Brawo",
            level_completed=False,
            topic_completed=False,
            selected_level=selected_level,
            frontier_level=1,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=True,
        ),
    )
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=True,
            user_input="2",
            chapter="Chapter Alpha",
            topic=fixture_curriculum.topic_name(CHAPTER_ALPHA, selected_topic_id) or "",
            level_number=selected_level,
            is_input_mode=False,
        ),
    )
    _assert_admin_profile_unchanged(state, baseline)


def test_admin_wrong_decrements_session_streak_without_profile_writes(
    fixture_curriculum: Curriculum,
):
    state, baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        streak=2,
    )
    problem = _wrong_problem()

    _submit(state, problem, "3", False, fixture_curriculum, _ADMIN)

    _assert_session(
        state,
        ExpectedSession(
            streak=1,
            flawless_eligible=True,
            xp=0,
            feedback_type="warning",
            feedback_msg="Try again",
            level_completed=False,
            topic_completed=False,
            selected_level=2,
            frontier_level=1,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=True,
        ),
    )
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=False,
            user_input="3",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=2,
            is_input_mode=False,
            answer_outcome="trap",
            trap_slug="w1",
        ),
    )
    _assert_admin_profile_unchanged(state, baseline)


def test_admin_ahead_of_unlock_reaches_input_mode_after_streak_threshold(
    fixture_curriculum: Curriculum,
):
    state, _baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        streak=0,
    )

    _submit(state, _correct_problem(), "2", False, fixture_curriculum, _ADMIN)

    assert session_state.resolve_input_mode(state, fixture_curriculum) == "input"


def test_admin_ahead_by_topic_keeps_streak_through_unlock_threshold(
    fixture_curriculum: Curriculum,
):
    state, baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_RADIO,
        selected_level=1,
        streak=2,
    )

    _submit(state, _correct_problem(), "2", False, fixture_curriculum, _ADMIN)

    assert state.streak == 3
    _assert_admin_profile_unchanged(state, baseline)


def test_admin_trap_answer_sets_warning_feedback_type(fixture_curriculum: Curriculum):
    state, baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        streak=2,
    )

    _submit(state, _trap_problem(), "1/3", True, fixture_curriculum, _ADMIN)

    assert state.feedback_type == "warning"
    assert state.streak == 1
    _assert_admin_profile_unchanged(state, baseline)


def test_admin_soft_error_preserves_session_streak(fixture_curriculum: Curriculum):
    state, baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        streak=2,
    )

    _submit(state, _soft_error_problem(), "2/4", True, fixture_curriculum, _ADMIN)

    assert state.feedback_type == "info"
    assert state.streak == 2
    _assert_admin_profile_unchanged(state, baseline)


def test_radio_only_topic_stays_radio_through_admin_unlock_streak(
    fixture_curriculum: Curriculum,
):
    state, _baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_RADIO,
        selected_level=1,
        streak=2,
    )

    _submit(state, _correct_problem(), "2", False, fixture_curriculum, _ADMIN)

    assert state.streak == 3
    assert session_state.resolve_input_mode(state, fixture_curriculum) == "radio"


def test_admin_resets_streak_at_stored_frontier_boundary(
    fixture_curriculum: Curriculum,
):
    state, baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=1,
        streak=2,
    )
    problem = _correct_problem()

    _submit(state, problem, "2", False, fixture_curriculum, _ADMIN)

    _assert_session(
        state,
        ExpectedSession(
            streak=0,
            flawless_eligible=True,
            xp=0,
            feedback_type="success",
            feedback_msg="Brawo",
            level_completed=False,
            topic_completed=False,
            selected_level=1,
            frontier_level=1,
            frontier_topic_id=TOPIC_MULTI,
            problem_answered=True,
        ),
    )
    _assert_telemetry(
        state.session_id,
        problem,
        ExpectedTelemetry(
            is_correct=True,
            user_input="2",
            chapter="Chapter Alpha",
            topic="Multi Level Topic",
            level_number=1,
            is_input_mode=False,
        ),
    )
    _assert_admin_profile_unchanged(state, baseline)


def test_admin_level_completion_sequence_leaves_stored_frontier_unchanged(
    fixture_curriculum: Curriculum,
):
    state, baseline = _admin_state_at(
        fixture_curriculum,
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
        selected_topic_id=TOPIC_MULTI,
        selected_level=1,
        streak=0,
    )
    problem = _correct_problem()

    _submit(state, problem, "2", False, fixture_curriculum, _ADMIN)
    assert state.streak == 1
    _assert_admin_profile_unchanged(state, baseline)

    state.problem_answered = False
    _submit(state, problem, "2", False, fixture_curriculum, _ADMIN)
    assert state.streak == 2
    _assert_admin_profile_unchanged(state, baseline)

    state.problem_answered = False
    _submit(state, problem, "2", False, fixture_curriculum, _ADMIN)
    assert state.streak == 0
    assert state.level_completed is False
    assert state.selected_level == 1
    chapter_id = _chapter_id(state)
    assert state.chapter_frontiers[chapter_id].frontier_level == 1
    assert state.chapter_frontiers[chapter_id].frontier_topic_id == TOPIC_MULTI
    _assert_admin_profile_unchanged(state, baseline)
