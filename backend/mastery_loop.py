"""Dynamic Mastery Loop — streak, XP, and Level/Topic progression for one Submission."""

from __future__ import annotations

from dataclasses import dataclass

import backend.config as config
from backend.answer_grading import EvalResult
from backend.unlock import advance_on_mastery


@dataclass(frozen=True)
class SubmissionContext:
    """Session slice needed to apply one Mastery Loop submission."""

    chapter_id: int
    topic_id: int
    selected_level: int
    current_streak: int
    flawless_eligible: bool
    unlocked_level: int
    topic_max_level: int
    next_topic_ids: tuple[int, ...]


@dataclass(frozen=True)
class SubmissionOutcome:
    """State deltas produced by the Mastery Loop for one answered Submission."""

    new_streak: int
    new_flawless_eligible: bool
    xp_earned: int
    feedback_type: str | None = None
    feedback_msg: str | None = None
    level_unlocked: bool = False
    topic_completed: bool = False
    show_celebration: bool = False
    new_selected_level: int | None = None
    new_unlocked_level: int | None = None
    unlock_topic_id: int | None = None


def apply_submission(eval_result: EvalResult, ctx: SubmissionContext) -> SubmissionOutcome:
    """Apply Power of 3 rules given a grading result and session context."""
    is_correct = eval_result.get("is_correct", False)
    feedback_type = eval_result.get("feedback_type")
    is_soft_error = feedback_type == "info"

    if not is_correct and not is_soft_error:
        new_flawless_eligible = False
    else:
        new_flawless_eligible = ctx.flawless_eligible

    if is_correct:
        return _apply_correct_submission(ctx, new_flawless_eligible)

    new_streak = ctx.current_streak
    if ctx.current_streak > 0 and not is_soft_error:
        new_streak = ctx.current_streak - 1

    return SubmissionOutcome(
        new_streak=new_streak,
        new_flawless_eligible=new_flawless_eligible,
        xp_earned=0,
    )


def _apply_correct_submission(
    ctx: SubmissionContext, flawless_eligible: bool
) -> SubmissionOutcome:
    earned_xp = config.XP_REWARDS.get(ctx.selected_level, config.DEFAULT_XP_REWARD)
    feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"

    new_streak = ctx.current_streak
    if new_streak < config.MAX_STREAK:
        new_streak += 1

    level_unlocked = False
    topic_completed = False
    show_celebration = False
    new_selected_level: int | None = None
    new_unlocked_level: int | None = None
    unlock_topic_id: int | None = None
    xp_earned = earned_xp

    if (
        new_streak == config.STARS_FOR_UNLOCK
        and ctx.selected_level == ctx.unlocked_level
    ):
        advance = advance_on_mastery(
            ctx.unlocked_level, ctx.topic_max_level, ctx.next_topic_ids
        )
        level_unlocked = advance.level_unlocked
        topic_completed = advance.topic_completed
        show_celebration = True
        new_selected_level = advance.new_selected_level
        new_unlocked_level = advance.new_unlocked_level
        unlock_topic_id = advance.unlock_topic_id
        new_streak = 0

        if flawless_eligible and (level_unlocked or topic_completed):
            flawless_bonus = config.FLAWLESS_LEVEL_BONUS
            xp_earned += flawless_bonus
            feedback_msg += f" ✨ +{flawless_bonus} Flawless Bonus!"

        flawless_eligible = True

    return SubmissionOutcome(
        new_streak=new_streak,
        new_flawless_eligible=flawless_eligible,
        xp_earned=xp_earned,
        feedback_type="success",
        feedback_msg=feedback_msg,
        level_unlocked=level_unlocked,
        topic_completed=topic_completed,
        show_celebration=show_celebration,
        new_selected_level=new_selected_level,
        new_unlocked_level=new_unlocked_level,
        unlock_topic_id=unlock_topic_id,
    )
