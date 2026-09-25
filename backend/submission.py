"""Own one Submission end-to-end: grade → telemetry → progression → persist. For conventions see 'backend/docs/submission.md'"""

from __future__ import annotations

import json
import logging
import time
from typing import Literal

import backend.config as config
from backend.answer_grading import EvalResult, grade
from backend.core import db
from backend.core.utils import ProblemDict, answer_form, answer_value
from backend.curriculum import Curriculum
import backend.deconstruction as deconstruction
from backend.models import (
    DeconstructionState,
    DeconstructionStep,
    InputMode,
    SessionState,
)
from backend.play_mode import PlayMode
from backend.progression import (
    SubmissionContext,
    SubmissionOutcome,
    resolve_submission_outcome,
)
import backend.session_state as session_state
from backend.unlock import frontier_relation

logger = logging.getLogger(__name__)

# Whether a Trap came from a Level's authored `traps:` block or was raised by the
# grader itself (Units, ADR-0005). Absent from telemetry entirely when there is no
# Trap — see `_resolve_trap_source`.
TrapSource = Literal["authored", "synthesized"]

_TELEMETRY_STRIP_KEYS = frozenset(
    {
        "correct",
        "image_html",
        "messages",
        "options",
        "options_map",
        "level",
        "level_name",
        "level_display",
    }
)


def run_submission_cycle(
    state: SessionState,
    problem: ProblemDict,
    user_input: str,
    input_mode: InputMode,
    curriculum: Curriculum,
    play_mode: PlayMode,
) -> EvalResult:
    """Grade, log telemetry, apply progression, and persist one Submission.

    A discounted retry — the one case where `problem["problem_id"]` matches
    `state.discounted_problem_id`, set by a just-finished Deconstruction — is
    graded and logged exactly like any other Submission, but skips the trigger
    check and scores XP through `_apply_discounted_retry_outcome` instead of
    the normal progression rules, so it can never touch Streak, Flawless, or
    the Frontier (ADR-0004).
    """
    if (
        state.username is None
        or state.selected_chapter_id is None
        or state.selected_topic_id is None
    ):
        raise RuntimeError("Session missing required context for submission")

    is_discounted_retry = problem.get("problem_id") == state.discounted_problem_id

    eval_result = grade(user_input, problem, input_mode=input_mode)
    state.problem_answered = eval_result.get("lock_answer", False)

    misconception_slug = _resolve_misconception_slug(state, curriculum, eval_result)
    trap_source = _resolve_trap_source(eval_result)
    _log_submission_telemetry(
        state,
        problem,
        eval_result,
        curriculum,
        play_mode,
        user_input=user_input,
        input_mode=input_mode,
        misconception_slug=misconception_slug,
        trap_source=trap_source,
    )
    _record_misconception_hit(state, misconception_slug)
    if is_discounted_retry:
        _apply_discounted_retry_outcome(state, eval_result)
        is_soft_error = eval_result.get("feedback_type") == "info"
        if not is_soft_error:
            state.discounted_problem_id = None
    else:
        _maybe_trigger_deconstruction(state, problem, curriculum, misconception_slug)
        _run_progression_step(state, eval_result, curriculum, play_mode)
    session_state.persist(state, play_mode)
    return eval_result


def _apply_discounted_retry_outcome(
    state: SessionState, eval_result: EvalResult
) -> None:
    """Score a Deconstruction's discounted retry — XP only, at
    `config.DECONSTRUCTION_DISCOUNTED_XP_MULTIPLIER`. Streak, Flawless, and the
    Frontier are untouched: a Streak discount would let a Deconstruction gate
    Level completion, which would contradict ADR-0004.
    """
    feedback_type = eval_result.get("feedback_type")
    feedback_msg = eval_result.get("feedback_msg", "")
    if eval_result.get("is_correct"):
        base_xp = config.XP_REWARDS.get(state.selected_level, config.DEFAULT_XP_REWARD)
        discounted_xp = round(base_xp * config.DECONSTRUCTION_DISCOUNTED_XP_MULTIPLIER)
        state.xp += discounted_xp
        feedback_type = "success"
        feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{discounted_xp} XP)"
    state.feedback_type = feedback_type
    state.feedback_msg = feedback_msg


def _sanitize_problem_for_telemetry(problem: ProblemDict) -> str:
    """Return JSON-safe problem state with internal/UI fields removed."""
    clean = {k: v for k, v in problem.items() if k not in _TELEMETRY_STRIP_KEYS}
    return json.dumps(clean)


def _resolve_misconception_slug(
    state: SessionState, curriculum: Curriculum, eval_result: EvalResult
) -> str | None:
    """Map a graded Trap to its catalogue Misconception, if any.

    A grader-synthesized Trap (Units — ADR-0005) carries its own Misconception,
    because it has no Level `traps:` entry to be looked up from.
    """
    synthesized = eval_result.get("misconception_slug")
    if synthesized is not None:
        return synthesized
    trap_slug = eval_result.get("trap_slug")
    if trap_slug is None:
        return None
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    assert chapter_id is not None and topic_id is not None
    level_config = curriculum.level_config(chapter_id, topic_id, state.selected_level)
    if level_config is None:
        return None
    return level_config.trap_misconceptions.get(trap_slug)


def _resolve_trap_source(eval_result: EvalResult) -> TrapSource | None:
    """Classify the graded Trap, if any, as `authored` or `synthesized`.

    `EvalResult.misconception_slug` is only ever set by a grader-synthesized Trap
    (see its docstring), so its presence is what distinguishes the two — not
    whether `_resolve_misconception_slug` found a catalogue Misconception, which
    an authored Trap can legitimately miss (#188).
    """
    if eval_result.get("trap_slug") is None:
        return None
    if eval_result.get("misconception_slug") is not None:
        return "synthesized"
    return "authored"


def _log_submission_telemetry(
    state: SessionState,
    problem: ProblemDict,
    eval_result: EvalResult,
    curriculum: Curriculum,
    play_mode: PlayMode,
    *,
    user_input: str,
    input_mode: InputMode,
    misconception_slug: str | None,
    trap_source: TrapSource | None,
) -> None:
    """Persist one submission attempt with sanitized problem state.

    Runs before progression mutates `state.streak`/`state.flawless_eligible`, so
    reading them here is exactly the Session context the Student was answering
    against — the Streak and Flawless standing *before* this Submission's verdict.
    """
    username = state.username
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    assert username is not None and chapter_id is not None and topic_id is not None

    time_spent_ms = None
    if state.problem_start_time is not None:
        time_spent_ms = int((time.time() - state.problem_start_time) * 1000)

    chapter_name = curriculum.chapter_name(chapter_id) or str(chapter_id)
    topic_name = curriculum.topic_name(chapter_id, topic_id) or str(topic_id)

    frontier = play_mode.resolve_frontier(
        list(curriculum.topics(chapter_id)), state.chapter_frontiers.get(chapter_id)
    )

    correct_raw = str(problem["correct"])
    answer_num, answer_den = answer_value(user_input) or (None, None)
    correct_num, correct_den = answer_value(correct_raw) or (None, None)

    db.log_telemetry(
        session_id=state.session_id,
        username=username,
        play_mode=play_mode.name,
        chapter_id=chapter_id,
        chapter_name=chapter_name,
        topic_id=topic_id,
        topic_name=topic_name,
        level_number=state.selected_level,
        input_mode=input_mode,
        streak_before_answer=state.streak,
        flawless_eligible=state.flawless_eligible,
        frontier_relation=frontier_relation(topic_id, state.selected_level, frontier),
        is_correct=eval_result.get("is_correct", False),
        user_input=user_input,
        answer_form=answer_form(user_input),
        answer_value_num=answer_num,
        answer_value_den=answer_den,
        correct_form=answer_form(correct_raw),
        correct_value_num=correct_num,
        correct_value_den=correct_den,
        answer_outcome=eval_result.get("answer_outcome"),
        misconception_slug=misconception_slug,
        trap_slug=eval_result.get("trap_slug"),
        trap_source=trap_source,
        time_spent_ms=time_spent_ms,
        problem_snapshot=_sanitize_problem_for_telemetry(problem),
        problem_id=problem.get("problem_id"),
    )


def _record_misconception_hit(
    state: SessionState, misconception_slug: str | None
) -> None:
    """Increment the Session-wide hit count for one Misconception.

    Runs before the discounted-retry branch, so a retry's wrong answer still
    counts toward its Misconception's trigger even though the retry itself can
    never arm one (ADR-0014). A `None` slug — a correct answer, an unanticipated
    wrong answer, a Filler, or a Trap referencing no Misconception in the
    catalogue — leaves every count untouched.
    """
    if misconception_slug is None:
        return
    state.misconception_hits[misconception_slug] = (
        state.misconception_hits.get(misconception_slug, 0) + 1
    )


def _maybe_trigger_deconstruction(
    state: SessionState,
    problem: ProblemDict,
    curriculum: Curriculum,
    misconception_slug: str | None,
) -> None:
    """Arm a Deconstruction on the second hit of a Misconception within a Session.

    Generic repeated failure is deliberately not a trigger — it takes
    `config.DECONSTRUCTION_TRIGGER_COUNT` hits on one Misconception, the current
    one included, and only a Misconception with an authored walkthrough can ever
    fire one. Both the count and the already-deconstructed guard key on the
    Misconception slug alone — no Chapter, Topic or Level — so hits accumulate
    anywhere in the Curriculum and each Misconception fires at most once per
    Session (ADR-0014). The `deconstructions` header row is written here, before
    the pause, so a Student who leaves during it is still counted. The triggering
    answer itself is graded as a completely normal Submission by the rest of
    `run_submission_cycle` — this only arms the takeover.
    """
    if (
        misconception_slug is None
        or state.deconstruction is not None
        or not deconstruction.has_walkthrough(misconception_slug)
        or misconception_slug in state.deconstructed
    ):
        return
    if (
        state.misconception_hits.get(misconception_slug, 0)
        < config.DECONSTRUCTION_TRIGGER_COUNT
    ):
        return

    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    level = state.selected_level
    username = state.username
    assert chapter_id is not None and topic_id is not None and username is not None

    chapter_name = curriculum.chapter_name(chapter_id) or str(chapter_id)
    topic_name = curriculum.topic_name(chapter_id, topic_id) or str(topic_id)

    try:
        steps = deconstruction.build_steps(
            misconception_slug, problem.get("parameters") or {}
        )
    except deconstruction.DeconstructionContractError:
        # Curriculum drift: this Level's generator no longer supplies what the
        # walkthrough needs, or its Trap points at a Misconception whose walkthrough
        # cannot be true of this Problem. `tests/test_deconstruction_contracts.py`
        # exists to catch that in CI; if one reaches a Student anyway, no
        # Deconstruction is armed rather than a 500 raised. The Submission is still
        # graded normally and the Trap's own prose still fires — the Student loses
        # only help they cannot tell they were owed. This returns before
        # `create_deconstruction`, so no orphan header row is left behind for
        # telemetry to count as a Deconstruction that never happened.
        logger.exception(
            "Skipping Deconstruction for misconception '%s' at %s / %s level %s",
            misconception_slug,
            chapter_name,
            topic_name,
            level,
        )
        return

    deconstruction_id = db.create_deconstruction(
        session_id=state.session_id,
        username=username,
        problem_id=problem.get("problem_id"),
        misconception_slug=misconception_slug,
        chapter_name=chapter_name,
        topic_name=topic_name,
        level_number=level,
    )
    db.create_deconstruction_steps(deconstruction_id, len(steps))
    state.deconstruction = DeconstructionState(
        misconception_slug=misconception_slug,
        steps=[
            DeconstructionStep(
                question=step.question,
                working_line=step.working_line,
                answer=step.answer,
                input_type=step.input_type,
                items=list(step.items) if step.items is not None else None,
                accepted_orders=(
                    list(step.accepted_orders)
                    if step.accepted_orders is not None
                    else None
                ),
            )
            for step in steps
        ],
        deconstruction_id=deconstruction_id,
    )


def _build_submission_context(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode,
    chapter_id: int,
    topic_id: int,
) -> SubmissionContext:
    """Collect the Session slice the pure progression rules run on."""
    topic_meta = curriculum.topic_by_id(chapter_id, topic_id)
    if topic_meta is None:
        raise RuntimeError(f"Topic id {topic_id} not found in chapter {chapter_id}")
    chapter_topics = list(curriculum.topics(chapter_id))
    next_topic_ids = tuple(
        sorted(
            int(topic_entry["topic_id"])
            for topic_entry in chapter_topics
            if int(topic_entry["topic_id"]) > topic_id
        )
    )
    return SubmissionContext(
        selected_level=state.selected_level,
        current_streak=state.streak,
        flawless_eligible=state.flawless_eligible,
        topic_max_level=int(topic_meta["max_level"]),
        next_topic_ids=next_topic_ids,
        at_frontier=play_mode.is_at_frontier(
            topic_id,
            state.selected_level,
            chapter_topics,
            state.chapter_frontiers.get(chapter_id),
        ),
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


def _write_submission_outcome_to_state(
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
    session_state.mark_level_and_topic_completion(
        state,
        level_completed=outcome.level_completed,
        topic_completed=outcome.topic_completed,
    )
    if outcome.new_selected_level is not None:
        state.selected_level = outcome.new_selected_level

    prog = state.chapter_frontiers[chapter_id]
    if outcome.new_frontier_level is not None:
        prog.frontier_level = outcome.new_frontier_level
    if outcome.unlock_topic_id is not None:
        prog.frontier_topic_id = outcome.unlock_topic_id


def _run_progression_step(
    state: SessionState,
    eval_result: EvalResult,
    curriculum: Curriculum,
    play_mode: PlayMode,
) -> None:
    """Apply progression rules for one graded submission using the play mode."""
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    assert chapter_id is not None and topic_id is not None

    submission_ctx = _build_submission_context(
        state, curriculum, play_mode, chapter_id, topic_id
    )
    submission_outcome = resolve_submission_outcome(eval_result, submission_ctx)
    _write_submission_outcome_to_state(
        state, chapter_id, submission_outcome, eval_result
    )
