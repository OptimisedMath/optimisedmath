"""Deconstruction step state transitions — grade one step, maybe Reveal, advance, persist.

Sits beside `submission.py` in the layering: `deconstruction.py` stays the pure
step-registry layer (no Session/state/HTTP imports), this module owns the stateful half —
mutating `state.deconstruction` and syncing the `deconstruction_steps` DB row. `Curriculum`
is injected rather than resolved here, per `docs/import-rules.md` rule 5.
"""

from __future__ import annotations

import backend.config as config
import backend.session_state as session_state
from backend.core import db
from backend.curriculum import Curriculum
from backend.models import (
    DeconstructionState,
    DeconstructionStep,
    DeconstructionStepResponse,
    DeconstructionSubmissionResponse,
    SessionState,
)
from backend.play_mode import PlayMode
from backend.step_grading import grade_ordering_step, grade_step


class DeconstructionNotRunningError(Exception):
    """Raised when a Deconstruction route is called with no step to act on."""


def _require_deconstruction_step(
    state: SessionState,
) -> tuple[DeconstructionState, DeconstructionStep]:
    deconstruction = state.deconstruction
    if deconstruction is None or deconstruction.step_index >= len(deconstruction.steps):
        raise DeconstructionNotRunningError()
    return deconstruction, deconstruction.steps[deconstruction.step_index]


def deconstruction_key(
    misconception_slug: str, chapter_id: int, topic_id: int, level: int
) -> str:
    """Stable identity for one (Misconception, Level) pair in `state.deconstructed`.

    Shared with `submission.py`'s trigger check, so an armed Deconstruction and
    its own ending agree on exactly the same key.
    """
    return f"{misconception_slug}:{chapter_id}:{topic_id}:{level}"


def _disarm(state: SessionState, deconstruction: DeconstructionState) -> None:
    """Record this (Misconception, Level) pair as deconstructed — either ending
    keeps it from firing again for the rest of the Session."""
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    assert chapter_id is not None and topic_id is not None
    key = deconstruction_key(
        deconstruction.misconception_slug, chapter_id, topic_id, state.selected_level
    )
    if key not in state.deconstructed:
        state.deconstructed.append(key)


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
    state: SessionState, curriculum: Curriculum
) -> DeconstructionStepResponse:
    """Build the wire payload for the Student's Deconstruction step right now."""
    deconstruction, step = _require_deconstruction_step(state)
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

    grade = grade_ordering_step if step.input_type == "ordering" else grade_step
    eval_result = grade(user_input, step.answer)
    is_correct = bool(eval_result.get("is_correct"))

    if not is_correct and not eval_result.get("soft_error"):
        deconstruction.step_attempts += 1
        if deconstruction.step_attempts >= config.DECONSTRUCTION_REVEAL_THRESHOLD:
            deconstruction.step_revealed = True

    if deconstruction.deconstruction_id is not None:
        db.update_deconstruction_step(
            deconstruction.deconstruction_id,
            answered_step_index,
            attempts=deconstruction.step_attempts,
            revealed=deconstruction.step_revealed,
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
