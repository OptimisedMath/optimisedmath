"""Own one Submission end-to-end: grade → telemetry → progression → persist."""

from __future__ import annotations

import json
import time

from backend.answer_grading import EvalResult, grade
from backend.core import db
from backend.core.utils import ProblemDict
from backend.curriculum import Curriculum
from backend.models import SessionState
from backend.play_mode import DbWritePlan, PlayMode
from backend.progression import (
    SubmissionContext,
    SubmissionOutcome,
    apply_submission,
)

_TELEMETRY_STRIP_KEYS = frozenset(
    {
        "image_html",
        "messages",
        "options",
        "options_map",
        "level",
        "level_name",
        "level_display",
        "problem_id",
    }
)


def process_submission(
    state: SessionState,
    problem: ProblemDict,
    user_input: str,
    is_input_mode: bool,
    curriculum: Curriculum,
    play_mode: PlayMode,
) -> EvalResult:
    """Grade, log telemetry, apply progression, and persist one Submission."""
    if (
        state.username is None
        or state.selected_chapter_id is None
        or state.selected_topic_id is None
    ):
        raise RuntimeError("Session missing required context for submission")

    eval_result = grade(user_input, problem, is_input_mode=is_input_mode)
    state.problem_answered = eval_result.get("lock_answer", False)

    from backend.session_state import build_db_write_plan, sync_to_db

    write_plan = build_db_write_plan(state, play_mode)

    _log_submission_telemetry(
        state, problem, user_input, is_input_mode, eval_result, curriculum
    )
    _apply_progression(state, eval_result, curriculum, play_mode)

    from backend.session_state import build_db_write_plan, sync_to_db

    write_plan = build_db_write_plan(state, play_mode)
    sync_to_db(state, write_plan)
    return eval_result


def _sanitize_problem_for_telemetry(problem: ProblemDict) -> str:
    """Return JSON-safe problem state with internal/UI fields removed."""
    clean = {k: v for k, v in problem.items() if k not in _TELEMETRY_STRIP_KEYS}
    return json.dumps(clean)


def _log_submission_telemetry(
    state: SessionState,
    problem: ProblemDict,
    user_input: str,
    is_input_mode: bool,
    eval_result: EvalResult,
    curriculum: Curriculum,
) -> None:
    """Persist one submission attempt with sanitized problem state."""
    username = state.username
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    assert username is not None and chapter_id is not None and topic_id is not None

    time_spent = None
    if state.problem_start_time is not None:
        time_spent = int(time.time() - state.problem_start_time)

    chapter_name = curriculum.chapter_name(chapter_id) or str(chapter_id)
    topic_name = curriculum.topic_name(chapter_id, topic_id) or str(topic_id)

    db.log_telemetry(
        session_id=state.session_id,
        username=username,
        chapter_name=chapter_name,
        topic_name=topic_name,
        level_number=state.selected_level,
        is_input_mode=is_input_mode,
        is_correct=eval_result.get("is_correct", False),
        user_input=user_input,
        trap_id=eval_result.get("trap_id"),
        time_spent_seconds=time_spent,
        equation_state=_sanitize_problem_for_telemetry(problem),
    )


def _build_submission_context(
    state: SessionState,
    curriculum: Curriculum,
    chapter_id: int,
    topic_id: int,
    *,
    full_progression: bool,
) -> SubmissionContext:
    prog = state.chapter_frontiers[chapter_id]
    topic_meta = curriculum.topic(chapter_id, topic_id)
    if topic_meta is None:
        raise RuntimeError(f"Topic id {topic_id} not found in chapter {chapter_id}")
    next_topic_ids = tuple(
        sorted(
            int(topic_entry["topic_id"])
            for topic_entry in curriculum.topics(chapter_id)
            if int(topic_entry["topic_id"]) > topic_id
        )
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
        full_progression=full_progression,
    )


def _resolve_feedback(
    eval_result: EvalResult, outcome: SubmissionOutcome
) -> tuple[str | None, str]:
    """Merge grading feedback with progression overrides into one final pair."""
    feedback_type = eval_result.get("feedback_type")
    feedback_msg = eval_result.get("feedback_msg", "")
    if outcome.feedback_type is not None:
        feedback_type = outcome.feedback_type
    if outcome.feedback_msg is not None:
        feedback_msg = outcome.feedback_msg
    return feedback_type, feedback_msg


def _apply_submission_outcome(
    state: SessionState,
    chapter_id: int,
    outcome: SubmissionOutcome,
    eval_result: EvalResult,
) -> None:
    feedback_type, feedback_msg = _resolve_feedback(eval_result, outcome)
    state.feedback_type = feedback_type
    state.feedback_msg = feedback_msg
    state.streak = outcome.new_streak
    state.flawless_eligible = outcome.new_flawless_eligible
    state.xp += outcome.xp_earned
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


def _apply_progression(
    state: SessionState,
    eval_result: EvalResult,
    curriculum: Curriculum,
    write_plan: DbWritePlan,
) -> None:
    """Apply progression rules for one graded submission using the write plan."""
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    assert chapter_id is not None and topic_id is not None

    submission_ctx = _build_submission_context(
        state,
        curriculum,
        chapter_id,
        topic_id,
        full_progression=write_plan.full_progression,
    )
    submission_outcome = apply_submission(eval_result, submission_ctx)
    _apply_submission_outcome(state, chapter_id, submission_outcome, eval_result)
