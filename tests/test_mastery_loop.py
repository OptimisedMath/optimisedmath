"""Unit tests for the Mastery Loop module (Power of 3 progression)."""

import pytest

import backend.config as config
from backend.mastery_loop import TurnContext, apply_turn


def _ctx(
    *,
    streak: int = 0,
    flawless_eligible: bool = True,
    selected_level: int = 1,
    unlocked_level: int = 1,
    topic_max_level: int = 3,
    next_topic_ids: tuple[int, ...] = (20, 30),
) -> TurnContext:
    return TurnContext(
        chapter_id=10,
        topic_id=10,
        selected_level=selected_level,
        current_streak=streak,
        flawless_eligible=flawless_eligible,
        unlocked_level=unlocked_level,
        topic_max_level=topic_max_level,
        next_topic_ids=next_topic_ids,
    )


def test_correct_increments_streak_without_unlock():
    outcome = apply_turn({"is_correct": True, "lock_answer": True}, _ctx(streak=1))

    assert outcome.new_streak == 2
    assert outcome.xp_earned == config.XP_REWARDS[1]
    assert outcome.feedback_type == "success"
    assert outcome.level_unlocked is False
    assert outcome.topic_completed is False
    assert outcome.new_flawless_eligible is True


def test_correct_at_streak_cap_unlocks_when_at_unlocked_progress():
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=3, selected_level=2, unlocked_level=2, topic_max_level=5),
    )

    assert outcome.new_streak == 0
    assert outcome.level_unlocked is True
    assert outcome.new_unlocked_level == 3


def test_correct_at_streak_cap_without_unlock_when_replaying_old_level():
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=3, selected_level=1, unlocked_level=2),
    )

    assert outcome.new_streak == 3
    assert outcome.level_unlocked is False
    assert outcome.xp_earned == config.XP_REWARDS[1]


def test_correct_unlocks_next_level_at_power_of_three():
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, selected_level=1, unlocked_level=1, topic_max_level=3),
    )

    assert outcome.new_streak == 0
    assert outcome.level_unlocked is True
    assert outcome.new_unlocked_level == 2
    assert outcome.new_selected_level == 2
    assert outcome.show_celebration is True
    assert outcome.new_flawless_eligible is True


def test_flawless_bonus_on_level_unlock():
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, flawless_eligible=True),
    )

    base_xp = config.XP_REWARDS[1]
    assert outcome.xp_earned == base_xp + config.FLAWLESS_LEVEL_BONUS
    assert "Flawless Bonus" in (outcome.feedback_msg or "")


def test_no_flawless_bonus_when_not_eligible():
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(streak=2, flawless_eligible=False),
    )

    assert outcome.xp_earned == config.XP_REWARDS[1]
    assert "Flawless Bonus" not in (outcome.feedback_msg or "")


def test_correct_completes_topic_at_max_level():
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=2,
            selected_level=3,
            unlocked_level=3,
            topic_max_level=3,
            next_topic_ids=(20, 30),
        ),
    )

    assert outcome.topic_completed is True
    assert outcome.level_unlocked is False
    assert outcome.unlock_topic_id == 20
    assert outcome.new_unlocked_level == 1
    assert outcome.new_streak == 0
    assert outcome.show_celebration is True


def test_topic_complete_without_next_topic():
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=2,
            selected_level=3,
            unlocked_level=3,
            topic_max_level=3,
            next_topic_ids=(),
        ),
    )

    assert outcome.topic_completed is True
    assert outcome.unlock_topic_id is None
    assert outcome.new_unlocked_level is None


def test_wrong_answer_decrements_streak():
    outcome = apply_turn(
        {"lock_answer": True, "feedback_type": "warning", "feedback_msg": "wrong"},
        _ctx(streak=2),
    )

    assert outcome.new_streak == 1
    assert outcome.new_flawless_eligible is False
    assert outcome.xp_earned == 0
    assert outcome.feedback_type is None


def test_soft_error_preserves_streak_and_flawless():
    outcome = apply_turn(
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
    outcome = apply_turn(
        {"lock_answer": True, "feedback_type": "warning"},
        _ctx(streak=0),
    )

    assert outcome.new_streak == 0
    assert outcome.new_flawless_eligible is False


@pytest.mark.parametrize(
    ("streak", "selected_level", "unlocked_level"),
    [
        (2, 2, 1),  # ahead of UnlockedProgress — no level unlock
        (2, 1, 2),  # behind UnlockedProgress — no level unlock
    ],
)
def test_unlock_requires_playing_at_unlocked_progress(streak, selected_level, unlocked_level):
    outcome = apply_turn(
        {"is_correct": True, "lock_answer": True},
        _ctx(
            streak=streak,
            selected_level=selected_level,
            unlocked_level=unlocked_level,
        ),
    )

    assert outcome.level_unlocked is False
    assert outcome.topic_completed is False
