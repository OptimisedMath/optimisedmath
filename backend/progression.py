"""Streak, XP, and level/topic progression for one Submission.

One rule set runs for both play modes; the caller tells it whether the
Submission was At the Frontier.
"""

from __future__ import annotations

from dataclasses import dataclass

import backend.config as config
from backend.answer_grading import EvalResult, is_correct
from backend.unlock import increase_frontier_on_mastery


@dataclass(frozen=True)
class SubmissionContext:
    """Session slice needed to apply one Submission's progression rules.

    Carries no Frontier position — ``at_frontier`` is the whole of what the
    Frontier decides here, resolved by the caller's play mode (ADR-0013).
    """

    selected_level: int
    current_streak: int
    flawless_eligible: bool
    topic_max_level: int
    next_topic_ids: tuple[int, ...]
    at_frontier: bool


@dataclass(frozen=True)
class SubmissionOutcome:
    """State deltas produced by progression rules for one answered Submission."""

    new_streak: int
    new_flawless_eligible: bool
    xp_earned: int
    feedback_type: str | None = None
    feedback_msg: str | None = None
    topic_completed: bool = False
    level_completed: bool = False
    new_selected_level: int | None = None
    new_frontier_level: int | None = None
    unlock_topic_id: int | None = None


def resolve_submission_outcome(
    eval_result: EvalResult, ctx: SubmissionContext
) -> SubmissionOutcome:
    """Apply progression rules given a grading result and session context."""
    correct = is_correct(eval_result)
    feedback_type = eval_result.get("feedback_type")
    is_soft_error = feedback_type == "info"

    if not correct and not is_soft_error:
        new_flawless_eligible = False
    else:
        new_flawless_eligible = ctx.flawless_eligible

    if correct:
        return _advance_streak_and_xp(ctx, new_flawless_eligible)

    new_streak = ctx.current_streak
    if ctx.current_streak > 0 and not is_soft_error:
        new_streak = ctx.current_streak - 1

    return SubmissionOutcome(
        new_streak=new_streak,
        new_flawless_eligible=new_flawless_eligible,
        xp_earned=0,
    )


def _advance_streak_and_xp(
    ctx: SubmissionContext, flawless_eligible: bool
) -> SubmissionOutcome:
    """Award XP, and move the Frontier on Mastery At the Frontier."""
    earned_xp = config.XP_REWARDS.get(ctx.selected_level, config.DEFAULT_XP_REWARD)
    feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"

    new_streak = ctx.current_streak
    if new_streak < config.MAX_STREAK:
        new_streak += 1

    topic_completed = False
    level_completed = False
    new_selected_level: int | None = None
    new_frontier_level: int | None = None
    unlock_topic_id: int | None = None
    xp_earned = earned_xp

    if new_streak == config.MAX_STREAK and ctx.at_frontier:
        # At the Frontier, the Level just played is the Frontier Level, so it is
        # the boundary the Frontier advances from.
        frontier_update = increase_frontier_on_mastery(
            ctx.selected_level, ctx.topic_max_level, ctx.next_topic_ids
        )
        level_unlocked = frontier_update.level_unlocked
        topic_completed = frontier_update.topic_completed
        level_completed = level_unlocked or topic_completed
        new_selected_level = frontier_update.new_selected_level
        new_frontier_level = frontier_update.new_frontier_level
        unlock_topic_id = frontier_update.unlock_topic_id
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
        topic_completed=topic_completed,
        level_completed=level_completed,
        new_selected_level=new_selected_level,
        new_frontier_level=new_frontier_level,
        unlock_topic_id=unlock_topic_id,
    )
