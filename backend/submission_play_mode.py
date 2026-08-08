"""Play-mode adapter — apply submission progression via resolved play mode."""

from __future__ import annotations

from backend.answer_grading import EvalResult
from backend.curriculum_loader import TopicMeta
from backend.play_mode import PlayMode
from backend.progression import (
    PersistenceProfile,
    SubmissionContext,
    SubmissionOutcome,
    apply_submission,
)
from backend.models import SessionState


def _persistence_profile_for(play_mode: PlayMode) -> PersistenceProfile:
    """Map play-mode policy to the progression persistence profile."""
    if play_mode.persists_profile:
        return PersistenceProfile.FULL
    return PersistenceProfile.STREAK_ONLY


def _build_submission_context(
    state: SessionState,
    chapter_id: int,
    topic_id: int,
    topics_by_id: dict[int, TopicMeta],
    *,
    profile: PersistenceProfile,
) -> SubmissionContext:
    prog = state.chapter_frontiers[chapter_id]
    topic_meta = topics_by_id[topic_id]
    next_topic_ids = tuple(
        sorted(int(tid) for tid in topics_by_id if int(tid) > topic_id)
    )
    return SubmissionContext(
        chapter_id=chapter_id,
        topic_id=topic_id,
        selected_level=state.selected_level,
        current_streak=state.streak,
        flawless_eligible=state.flawless_eligible,
        frontier_level=prog.frontier_level,
        frontier_topic_id=prog.frontier_topic_id,
        topic_max_level=int(topic_meta["max_level"]),
        next_topic_ids=next_topic_ids,
        persistence_profile=profile,
    )


def _apply_submission_outcome(
    state: SessionState, chapter_id: int, outcome: SubmissionOutcome
) -> None:
    state.streak = outcome.new_streak
    state.flawless_eligible = outcome.new_flawless_eligible
    state.xp += outcome.xp_earned
    if outcome.feedback_type is not None:
        state.feedback_type = outcome.feedback_type
    if outcome.feedback_msg is not None:
        state.feedback_msg = outcome.feedback_msg
    if outcome.level_completed:
        state.level_completed = True
    if outcome.topic_completed:
        state.topic_completed = True
    if outcome.new_selected_level is not None:
        state.selected_level = outcome.new_selected_level

    prog = state.chapter_frontiers[chapter_id]
    if outcome.new_frontier_level is not None:
        prog.frontier_level = outcome.new_frontier_level
    if outcome.unlock_topic_id is not None:
        prog.frontier_topic_id = outcome.unlock_topic_id


def apply_submission_outcome_via_play_mode(
    state: SessionState,
    eval_result: EvalResult,
    topics_by_id: dict[int, TopicMeta],
    play_mode: PlayMode,
) -> None:
    """Apply progression rules for one graded submission using play-mode policy."""
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    if chapter_id is None or topic_id is None:
        raise RuntimeError("Session missing required context for submission")

    profile = _persistence_profile_for(play_mode)
    submission_ctx = _build_submission_context(
        state, chapter_id, topic_id, topics_by_id, profile=profile
    )
    submission_outcome = apply_submission(eval_result, submission_ctx)
    _apply_submission_outcome(state, chapter_id, submission_outcome)
