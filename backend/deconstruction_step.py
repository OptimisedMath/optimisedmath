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
from backend.step_grading import grade_step


class DeconstructionNotRunningError(Exception):
    """Raised when a Deconstruction route is called with no step to act on."""


def _require_deconstruction_step(
    state: SessionState,
) -> tuple[DeconstructionState, DeconstructionStep]:
    deconstruction = state.deconstruction
    if deconstruction is None or deconstruction.step_index >= len(deconstruction.steps):
        raise DeconstructionNotRunningError()
    return deconstruction, deconstruction.steps[deconstruction.step_index]


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
    )


def submit_step(
    state: SessionState, user_input: str, play_mode: PlayMode
) -> DeconstructionSubmissionResponse:
    """Grade one Deconstruction step and advance on a correct answer.

    Soft errors (a parse failure or a notation mismatch) never count toward the
    Reveal — only a genuine wrong answer increments `step_attempts`. At
    `config.DECONSTRUCTION_REVEAL_THRESHOLD` the answer is revealed but the step
    does not advance; the Student still has to type it. Post-Reveal retry is
    infinite, so a correct answer always advances regardless of `step_revealed`.
    """
    deconstruction, step = _require_deconstruction_step(state)
    answered_step_index = deconstruction.step_index

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
            attempts=deconstruction.step_attempts,
            revealed=deconstruction.step_revealed,
        )

    if is_correct:
        deconstruction.step_index += 1
        deconstruction.step_attempts = 0
        deconstruction.step_revealed = False

    session_state.persist(state, play_mode)

    return DeconstructionSubmissionResponse(
        is_correct=is_correct,
        feedback_msg=eval_result.get("feedback_msg"),
    )
