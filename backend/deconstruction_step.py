"""Deconstruction step state transitions — grade one step, maybe Reveal, advance, persist.

Sits beside `submission.py` in the layering: `deconstruction.py` stays the pure
step-registry layer (no Session/state/HTTP imports), this module owns the stateful half —
mutating `state.deconstruction` and syncing the `deconstruction_steps` DB row. `Curriculum`
is injected rather than resolved here, per `docs/import-rules.md` rule 5.
"""

from __future__ import annotations

import time

import backend.config as config
import backend.session_state as session_state
from backend.core import db
from backend.core.utils import answer_form, answer_value
from backend.curriculum import Curriculum
from backend.models import (
    DeconstructionState,
    DeconstructionStep,
    DeconstructionStepResponse,
    DeconstructionSubmissionResponse,
    SessionState,
)
from backend.play_mode import PlayMode
from backend.step_grading import StepEvalResult, grade_ordering_step, grade_step


def _attempt_outcome(eval_result: StepEvalResult) -> str:
    """The Answer Outcome one graded step is recorded under (ADR-0016, #259).

    Collapses the step grader's is_correct/soft_error pair into the same
    four-value vocabulary the Submission table uses. Trap is unreachable here —
    a step has no `options_map` — but the column keeps the full domain per
    #244's rule that no query learns two dialects.
    """
    if eval_result.get("is_correct"):
        return "correct"
    if eval_result.get("soft_error"):
        return "soft_error"
    return "wrong"


class DeconstructionNotRunningError(Exception):
    """Raised when a Deconstruction route is called with no step to act on."""


def _require_deconstruction_step(
    state: SessionState,
) -> tuple[DeconstructionState, DeconstructionStep]:
    deconstruction = state.deconstruction
    if deconstruction is None or deconstruction.step_index >= len(deconstruction.steps):
        raise DeconstructionNotRunningError()
    return deconstruction, deconstruction.steps[deconstruction.step_index]


def _disarm(state: SessionState, deconstruction: DeconstructionState) -> None:
    """Record this Misconception as deconstructed — either ending keeps it from
    firing again for the rest of the Session.

    Reads the slug straight off the active Deconstruction's own state, not off
    the Session's Selected chapter, topic and level — so nothing about the
    ending depends on navigation having left those untouched since the
    trigger armed it (ADR-0014).
    """
    if deconstruction.misconception_slug not in state.deconstructed:
        state.deconstructed.append(deconstruction.misconception_slug)


def _abandon(state: SessionState, play_mode: PlayMode, *, outcome: str) -> None:
    deconstruction = state.deconstruction
    if deconstruction is None:
        raise DeconstructionNotRunningError()
    if deconstruction.deconstruction_id is not None:
        db.set_deconstruction_outcome(deconstruction.deconstruction_id, outcome)
    _disarm(state, deconstruction)
    state.deconstruction = None
    session_state.persist(state, play_mode)


def abandon_via_control(state: SessionState, play_mode: PlayMode) -> None:
    """End a running Deconstruction via its always-present exit control.

    Available from any step — not restricted to appear only after the Reveal
    was rejected, which would price leaving at three deliberate wrong answers.
    The triggering Problem stays exactly as Abandonment leaves it: under Answer
    lock, its answer revealed, nothing earned.
    """
    _abandon(state, play_mode, outcome="abandoned_via_control")


def abandon_via_navigation(state: SessionState, play_mode: PlayMode) -> None:
    """End a running Deconstruction because toolbar Navigation moved the Session away.

    Same ending as `abandon_via_control` — differs only in the `outcome`
    recorded, the only telemetry evidence distinguishing the two doors.
    """
    _abandon(state, play_mode, outcome="abandoned_via_navigation")


def _finish(
    state: SessionState, curriculum: Curriculum, deconstruction: DeconstructionState
) -> str:
    """Reach the final step: record completion, disarm the Misconception, and
    reopen the triggering Problem for a discounted retry.

    Handback has no separate endpoint — the caller carries the returned
    question text back on the same step-submit response. Returns the
    triggering Problem's question text.
    """
    if deconstruction.deconstruction_id is not None:
        db.set_deconstruction_outcome(deconstruction.deconstruction_id, "completed")
    _disarm(state, deconstruction)
    problem = state.current_problem
    assert problem is not None
    state.discounted_problem_id = problem.get("problem_id")
    state.deconstruction = None
    session_state.lift_answer_lock(state, curriculum)
    return str(problem.get("question", ""))


def next_step_response(
    state: SessionState, curriculum: Curriculum, play_mode: PlayMode
) -> DeconstructionStepResponse:
    """Build the wire payload for the Student's Deconstruction step right now.

    Stamps `step_start_time`, mirroring `problem_start_time` — every serving of
    a step (the first one, or a re-serving after a wrong answer) starts the
    clock the next attempt row's `time_spent_ms` reads on submit.
    """
    deconstruction, step = _require_deconstruction_step(state)
    deconstruction.step_start_time = time.time()
    session_state.persist(state, play_mode)

    misconception_name = (
        curriculum.misconception_name(deconstruction.misconception_slug)
        or deconstruction.misconception_slug
    )
    return DeconstructionStepResponse(
        question=step.question,
        working_line=step.working_line,
        step_index=deconstruction.step_index,
        total_steps=len(deconstruction.steps),
        misconception_name=misconception_name,
        revealed_answer=step.answer if deconstruction.step_revealed else None,
        input_type=step.input_type,
        items=step.items,
    )


def submit_step(
    state: SessionState,
    user_input: str,
    curriculum: Curriculum,
    play_mode: PlayMode,
) -> DeconstructionSubmissionResponse:
    """Grade one Deconstruction step and advance on a correct answer.

    Soft errors (a parse failure or a notation mismatch) never count toward the
    Reveal — only a genuine wrong answer increments `step_attempts`. At
    `config.DECONSTRUCTION_REVEAL_THRESHOLD` the answer is revealed but the step
    does not advance; the Student still has to type it. Post-Reveal retry is
    infinite, so a correct answer always advances regardless of `step_revealed`.
    A correct answer on the final step ends the Deconstruction — see `_finish`.
    """
    deconstruction, step = _require_deconstruction_step(state)
    answered_step_index = deconstruction.step_index

    time_spent_ms = None
    if deconstruction.step_start_time is not None:
        time_spent_ms = int((time.time() - deconstruction.step_start_time) * 1000)

    if step.input_type == "ordering":
        eval_result = grade_ordering_step(user_input, step.answer, step.accepted_orders)
    else:
        eval_result = grade_step(user_input, step.answer)
    is_correct = bool(eval_result.get("is_correct"))

    if not is_correct and not eval_result.get("soft_error"):
        deconstruction.step_attempts += 1
        if deconstruction.step_attempts >= config.DECONSTRUCTION_REVEAL_THRESHOLD:
            deconstruction.step_revealed = True

    if deconstruction.deconstruction_id is not None:
        db.update_deconstruction_step(
            deconstruction.deconstruction_id,
            answered_step_index,
            revealed=deconstruction.step_revealed,
        )
        db.create_deconstruction_attempt(
            deconstruction.deconstruction_id,
            answered_step_index,
            user_input=user_input,
            answer_form=answer_form(user_input),
            answer_value=answer_value(user_input),
            outcome=_attempt_outcome(eval_result),
            time_spent_ms=time_spent_ms,
        )

    handback_question: str | None = None
    if is_correct:
        deconstruction.step_index += 1
        deconstruction.step_attempts = 0
        deconstruction.step_revealed = False
        if deconstruction.step_index >= len(deconstruction.steps):
            handback_question = _finish(state, curriculum, deconstruction)

    session_state.persist(state, play_mode)

    return DeconstructionSubmissionResponse(
        is_correct=is_correct,
        feedback_msg=eval_result.get("feedback_msg"),
        handback_question=handback_question,
    )
