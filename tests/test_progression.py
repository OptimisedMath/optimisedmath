"""Unit tests for submission progression rules (streak, XP, level/topic unlock)."""

import pytest

import backend.config as config
from backend.models import SessionState
from backend.progression import SubmissionContext, apply_submission, streak_meter_for


def _ctx(
    *,
    streak: int = 0,
    flawless_eligible: bool = True,
    selected_level: int = 1,
    frontier_level: int = 1,
    frontier_topic_id: int = 10,
    topic_id: int = 10,
    topic_max_level: int = 3,
    next_topic_ids: tuple[int, ...] = (20, 30),
    full_progression: bool = True,
) -> SubmissionContext:
    return SubmissionContext(
        chapter_id=10,
        topic_id=topic_id,
        selected_level=selected_level,
        current_streak=streak,
        flawless_eligible=flawless_eligible,
        frontier_level=frontier_level,
        frontier_topic_id=frontier_topic_id,
        topic_max_level=topic_max_level,
        next_topic_ids=next_topic_ids,
        full_progression=full_progression,
    )


def test_streak_meter_equals_streak_by_default():
    state = SessionState(streak=2, max_streak=3)

    assert streak_meter_for(state) == 2


def test_streak_meter_stays_full_during_level_completion_feedback():
    state = SessionState(
        streak=0,
        max_streak=3,
        problem_answered=True,
        level_completed=True,
    )

    assert streak_meter_for(state) == 3


@pytest.mark.parametrize(
    ("problem_answered", "level_completed", "streak", "expected"),
    [
        (True, True, 1, 1),
        (True, False, 0, 0),
        (False, True, 0, 0),
        (False, False, 2, 2),
    ],
)
def test_streak_meter_exception_requires_all_three_conditions(
    problem_answered, level_completed, streak, expected
):
    state = SessionState(
        streak=streak,
        max_streak=3,
        problem_answered=problem_answered,
        level_completed=level_completed,
    )

    assert streak_meter_for(state) == expected


def test_correct_increments_streak_without_unlock():
    outcome = apply_submission({"is_correct": True, "lock_answer": True}, _ctx(streak=1))

    assert outcome.new_streak == 2
    assert outcome.xp_earned == config.XP_REWARDS[1]
    assert outcome.feedback_type == "success"
    assert outcome.level_unlocked is False
    assert outcome.topic_completed is False
    assert outcome.new_flawless_eligible is True


def test_correct_at_streak_cap_unlocks_when_at_frontier():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=3, selected_level=2, frontier_level=2, topic_max_level=5),
    )

    assert outcome.new_streak == 0
    assert outcome.level_unlocked is True
    assert outcome.new_frontier_level == 3


def test_correct_at_streak_cap_without_unlock_when_replaying_old_level():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=3, selected_level=1, frontier_level=2),
    )

    assert outcome.new_streak == 3
    assert outcome.level_unlocked is False
    assert outcome.xp_earned == config.XP_REWARDS[1]


def test_correct_unlocks_next_level_at_power_of_three():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, selected_level=1, frontier_level=1, topic_max_level=3),
    )

    assert outcome.new_streak == 0
    assert outcome.level_unlocked is True
    assert outcome.new_frontier_level == 2
    assert outcome.new_selected_level == 2
    assert outcome.level_completed is True
    assert outcome.new_flawless_eligible is True


def test_flawless_bonus_on_level_unlock():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, flawless_eligible=True),
    )

    base_xp = config.XP_REWARDS[1]
    assert outcome.xp_earned == base_xp + config.FLAWLESS_LEVEL_BONUS
    assert "Flawless Bonus" in (outcome.feedback_msg or "")


def test_no_flawless_bonus_when_not_eligible():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, flawless_eligible=False),
    )

    assert outcome.xp_earned == config.XP_REWARDS[1]
    assert "Flawless Bonus" not in (outcome.feedback_msg or "")


def test_correct_completes_topic_at_max_level():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=2,
            selected_level=3,
            frontier_level=3,
            topic_max_level=3,
            next_topic_ids=(20, 30),
        ),
    )

    assert outcome.topic_completed is True
    assert outcome.level_unlocked is False
    assert outcome.unlock_topic_id == 20
    assert outcome.new_frontier_level == 1
    assert outcome.new_streak == 0
    assert outcome.level_completed is True


def test_topic_complete_without_next_topic():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=2,
            selected_level=3,
            frontier_level=3,
            topic_max_level=3,
            next_topic_ids=(),
        ),
    )

    assert outcome.topic_completed is True
    assert outcome.unlock_topic_id is None
    assert outcome.new_frontier_level is None


def test_wrong_answer_decrements_streak():
    outcome = apply_submission(
        {"lock_answer": True, "feedback_type": "warning", "feedback_msg": "wrong"},
        _ctx(streak=2),
    )

    assert outcome.new_streak == 1
    assert outcome.new_flawless_eligible is False
    assert outcome.xp_earned == 0
    assert outcome.feedback_type is None


def test_soft_error_preserves_streak_and_flawless():
    outcome = apply_submission(
        {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "syntax",
            "trap_id": "syntax_error",
        },
        _ctx(streak=2, flawless_eligible=True),
    )

    assert outcome.new_streak == 2
    assert outcome.new_flawless_eligible is True


def test_wrong_at_streak_zero_stays_zero():
    outcome = apply_submission(
        {"lock_answer": True, "feedback_type": "warning"},
        _ctx(streak=0),
    )

    assert outcome.new_streak == 0
    assert outcome.new_flawless_eligible is False


@pytest.mark.parametrize(
    ("streak", "selected_level", "frontier_level"),
    [
        (2, 2, 1),  # beyond the Frontier — no level unlock
        (2, 1, 2),  # behind the Frontier — no level unlock
    ],
)
def test_unlock_requires_playing_at_frontier(streak, selected_level, frontier_level):
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=streak,
            selected_level=selected_level,
            frontier_level=frontier_level,
        ),
    )

    assert outcome.level_unlocked is False
    assert outcome.topic_completed is False


def test_streak_only_increments_without_xp():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=1, full_progression=False),
    )

    assert outcome.new_streak == 2
    assert outcome.xp_earned == 0
    assert outcome.feedback_type == "success"
    assert "XP" not in (outcome.feedback_msg or "")
    assert outcome.level_unlocked is False
    assert outcome.new_flawless_eligible is True


def test_streak_only_resets_at_stored_frontier_boundary():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=2,
            selected_level=1,
            frontier_level=1,
            frontier_topic_id=10,
            topic_id=10,
            full_progression=False,
        ),
    )

    assert outcome.new_streak == 0
    assert outcome.xp_earned == 0
    assert outcome.new_frontier_level is None
    assert outcome.unlock_topic_id is None


def test_streak_only_no_reset_when_ahead_by_topic():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=2,
            topic_id=20,
            frontier_topic_id=10,
            full_progression=False,
        ),
    )

    assert outcome.new_streak == 3
    assert outcome.new_frontier_level is None


def test_streak_only_no_reset_when_ahead_by_level():
    outcome = apply_submission(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=2,
            selected_level=2,
            frontier_level=1,
            full_progression=False,
        ),
    )

    assert outcome.new_streak == 3
    assert outcome.new_frontier_level is None


def test_streak_only_wrong_decrements_without_flawless_forfeit():
    outcome = apply_submission(
        {"lock_answer": True, "feedback_type": "warning", "feedback_msg": "wrong"},
        _ctx(streak=2, flawless_eligible=True, full_progression=False),
    )

    assert outcome.new_streak == 1
    assert outcome.new_flawless_eligible is True
    assert outcome.xp_earned == 0


def test_streak_only_soft_error_preserves_streak():
    outcome = apply_submission(
        {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "syntax",
            "trap_id": "syntax_error",
        },
        _ctx(streak=2, flawless_eligible=True, full_progression=False),
    )

    assert outcome.new_streak == 2
    assert outcome.new_flawless_eligible is True
