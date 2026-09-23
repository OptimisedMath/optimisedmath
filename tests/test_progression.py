"""Unit tests for submission progression rules (streak, XP, level/topic unlock)."""

import backend.config as config
from backend.progression import (
    SubmissionContext,
    resolve_submission_outcome,
)


def _ctx(
    *,
    streak: int = 0,
    flawless_eligible: bool = True,
    selected_level: int = 1,
    frontier_level: int = 1,
    topic_max_level: int = 3,
    next_topic_ids: tuple[int, ...] = (20, 30),
    at_frontier: bool = True,
) -> SubmissionContext:
    return SubmissionContext(
        selected_level=selected_level,
        current_streak=streak,
        flawless_eligible=flawless_eligible,
        frontier_level=frontier_level,
        topic_max_level=topic_max_level,
        next_topic_ids=next_topic_ids,
        at_frontier=at_frontier,
    )


def test_correct_increments_streak_without_unlock():
    outcome = resolve_submission_outcome(
        {"is_correct": True, "lock_answer": True}, _ctx(streak=1)
    )

    assert outcome.new_streak == 2
    assert outcome.xp_earned == config.XP_REWARDS[1]
    assert outcome.feedback_type == "success"
    assert outcome.topic_completed is False
    assert outcome.level_completed is False
    assert outcome.new_flawless_eligible is True


def test_correct_at_frontier_reaching_max_streak_unlocks_next_level():
    outcome = resolve_submission_outcome(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, selected_level=1, frontier_level=1, topic_max_level=3),
    )

    assert outcome.new_streak == 0
    assert outcome.new_frontier_level == 2
    assert outcome.new_selected_level == 2
    assert outcome.level_completed is True
    assert outcome.topic_completed is False
    assert outcome.new_flawless_eligible is True


def test_flawless_bonus_on_level_unlock():
    outcome = resolve_submission_outcome(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, flawless_eligible=True),
    )

    base_xp = config.XP_REWARDS[1]
    assert outcome.xp_earned == base_xp + config.FLAWLESS_LEVEL_BONUS
    assert "Flawless Bonus" in (outcome.feedback_msg or "")


def test_no_flawless_bonus_when_not_eligible():
    outcome = resolve_submission_outcome(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, flawless_eligible=False),
    )

    assert outcome.xp_earned == config.XP_REWARDS[1]
    assert "Flawless Bonus" not in (outcome.feedback_msg or "")


def test_correct_completes_topic_at_max_level():
    outcome = resolve_submission_outcome(
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
    assert outcome.unlock_topic_id == 20
    assert outcome.new_frontier_level == 1
    assert outcome.new_streak == 0
    assert outcome.level_completed is True


def test_topic_complete_without_next_topic():
    outcome = resolve_submission_outcome(
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
    outcome = resolve_submission_outcome(
        {"lock_answer": True, "feedback_type": "warning", "feedback_msg": "wrong"},
        _ctx(streak=2),
    )

    assert outcome.new_streak == 1
    assert outcome.new_flawless_eligible is False
    assert outcome.xp_earned == 0
    assert outcome.feedback_type is None


def test_soft_error_preserves_streak_and_flawless():
    outcome = resolve_submission_outcome(
        {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "syntax",
            "answer_outcome": "syntax_error",
        },
        _ctx(streak=2, flawless_eligible=True),
    )

    assert outcome.new_streak == 2
    assert outcome.new_flawless_eligible is True


def test_wrong_at_streak_zero_stays_zero():
    outcome = resolve_submission_outcome(
        {"lock_answer": True, "feedback_type": "warning"},
        _ctx(streak=0),
    )

    assert outcome.new_streak == 0
    assert outcome.new_flawless_eligible is False


def test_not_at_frontier_reaching_max_streak_caps_without_unlock():
    """Not At the Frontier: Streak still caps at Mastery, but nothing else fires —
    no Level/Topic completion and no Frontier field written."""
    outcome = resolve_submission_outcome(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, at_frontier=False),
    )

    assert outcome.new_streak == 3
    assert outcome.xp_earned == config.XP_REWARDS[1]
    assert outcome.topic_completed is False
    assert outcome.level_completed is False
    assert outcome.new_selected_level is None
    assert outcome.new_frontier_level is None
    assert outcome.unlock_topic_id is None


def test_not_at_frontier_wrong_answer_decrements_without_flawless_forfeit_exception():
    """A penalized mistake still forfeits Flawless regardless of `at_frontier` —
    the gate only decides Mastery's consequences, not the mistake's."""
    outcome = resolve_submission_outcome(
        {"lock_answer": True, "feedback_type": "warning", "feedback_msg": "wrong"},
        _ctx(streak=2, flawless_eligible=True, at_frontier=False),
    )

    assert outcome.new_streak == 1
    assert outcome.new_flawless_eligible is False
    assert outcome.xp_earned == 0
