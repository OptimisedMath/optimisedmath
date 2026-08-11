"""Streak, XP, and level/topic progression for one Submission."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import backend.config as config
from backend.answer_grading import EvalResult
from backend.models import SessionState
from backend.unlock import apply_frontier_on_mastery


class PersistenceProfile(Enum):
    """Which progression deltas may be applied to the session/profile."""

    FULL = "full"
    STREAK_ONLY = "streak_only"


@dataclass(frozen=True)
class SubmissionContext:
    """Session slice needed to apply one Submission's progression rules."""

    chapter_id: int
    topic_id: int
    selected_level: int
    current_streak: int
    flawless_eligible: bool
    frontier_level: int
    frontier_topic_id: int
    topic_max_level: int
    next_topic_ids: tuple[int, ...]
    persistence_profile: PersistenceProfile = PersistenceProfile.FULL


@dataclass(frozen=True)
class SubmissionOutcome:
    """State deltas produced by progression rules for one answered Submission."""

    new_streak: int
    new_flawless_eligible: bool
    xp_earned: int
    feedback_type: str | None = None
    feedback_msg: str | None = None
    level_unlocked: bool = False
    topic_completed: bool = False
    level_completed: bool = False
    new_selected_level: int | None = None
    new_frontier_level: int | None = None
    unlock_topic_id: int | None = None


def streak_meter_for(state: SessionState) -> int:
    """Streak meter display value for the Session payload."""
    if state.problem_answered and state.level_completed and state.streak == 0:
        return state.max_streak
    return state.streak


def apply_submission(eval_result: EvalResult, ctx: SubmissionContext) -> SubmissionOutcome:
    """Apply progression rules given a grading result and session context."""
    is_correct = eval_result.get("is_correct", False)
    feedback_type = eval_result.get("feedback_type")
    is_soft_error = feedback_type == "info"

    if ctx.persistence_profile == PersistenceProfile.STREAK_ONLY:
        return _apply_streak_only_submission(ctx, is_correct, is_soft_error)

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


def _is_at_streak_reset_boundary(
    *,
    selected_level: int,
    frontier_level: int,
    topic_id: int,
    frontier_topic_id: int,
    require_topic_match: bool,
) -> bool:
    """Check whether the player is at the streak-reset boundary for their profile."""
    if selected_level != frontier_level:
        return False
    if require_topic_match:
        return topic_id == frontier_topic_id
    return True


def _apply_streak_only_submission(
    ctx: SubmissionContext, is_correct: bool, is_soft_error: bool
) -> SubmissionOutcome:
    """Admin QA: in-cycle streak only — no XP, Flawless, or Frontier writes."""
    if is_correct:
        new_streak = ctx.current_streak
        if new_streak < config.MAX_STREAK:
            new_streak += 1

        at_boundary = _is_at_streak_reset_boundary(
            selected_level=ctx.selected_level,
            frontier_level=ctx.frontier_level,
            topic_id=ctx.topic_id,
            frontier_topic_id=ctx.frontier_topic_id,
            require_topic_match=True,
        )
        if new_streak == config.STARS_FOR_UNLOCK and at_boundary:
            new_streak = 0

        return SubmissionOutcome(
            new_streak=new_streak,
            new_flawless_eligible=ctx.flawless_eligible,
            xp_earned=0,
            feedback_type="success",
            feedback_msg="Brawo! To poprawna odpowiedź. 🎉",
        )

    new_streak = ctx.current_streak
    if ctx.current_streak > 0 and not is_soft_error:
        new_streak = ctx.current_streak - 1

    return SubmissionOutcome(
        new_streak=new_streak,
        new_flawless_eligible=ctx.flawless_eligible,
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
    level_completed = False
    new_selected_level: int | None = None
    new_frontier_level: int | None = None
    unlock_topic_id: int | None = None
    xp_earned = earned_xp

    at_boundary = _is_at_streak_reset_boundary(
        selected_level=ctx.selected_level,
        frontier_level=ctx.frontier_level,
        topic_id=ctx.topic_id,
        frontier_topic_id=ctx.frontier_topic_id,
        require_topic_match=False,
    )
    if new_streak == config.STARS_FOR_UNLOCK and at_boundary:
        frontier_update = apply_frontier_on_mastery(
            ctx.frontier_level, ctx.topic_max_level, ctx.next_topic_ids
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
        level_unlocked=level_unlocked,
        topic_completed=topic_completed,
        level_completed=level_completed,
        new_selected_level=new_selected_level,
        new_frontier_level=new_frontier_level,
        unlock_topic_id=unlock_topic_id,
    )
