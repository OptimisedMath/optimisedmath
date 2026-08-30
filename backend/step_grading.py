"""Deconstruction step grading — a simpler taxonomy than `answer_grading.grade()`.

A step needs a target answer and correct/incorrect, not the Trap / Wrong / `options_map`
taxonomy built for Problems. This path keeps the parse step and the format-mismatch check,
dropping only the Trap and `options_map` machinery those have no use for. Pure: no Session,
state, or HTTP imports.
"""

from __future__ import annotations

from typing import TypedDict

from backend.core.utils import (
    check_format_mismatch,
    check_text_answer,
    parse_to_fraction,
)


class StepEvalResult(TypedDict, total=False):
    is_correct: bool
    feedback_msg: str
    soft_error: bool


ORDERING_ANSWER_SEPARATOR = "|"


def grade_ordering_step(user_input: str, answer: str) -> StepEvalResult:
    """Grade an ordering step: exact match of the submitted order against the target.

    Both sides are `ORDERING_ANSWER_SEPARATOR`-joined item lists. There is no
    format-mismatch notion here — unlike a typed numeric answer, an ordering
    has no equivalent notation to fumble, so a mismatch is simply wrong.
    """
    student_order = [
        item.strip() for item in user_input.split(ORDERING_ANSWER_SEPARATOR)
    ]
    correct_order = [item.strip() for item in answer.split(ORDERING_ANSWER_SEPARATOR)]
    return {"is_correct": student_order == correct_order}


def grade_step(user_input: str, answer: str) -> StepEvalResult:
    """Grade one Deconstruction step answer against its fixed target.

    `soft_error=True` marks a mistyped or wrongly-notated answer — the caller must not
    count it toward the Reveal threshold, since it costs the Student nothing.
    """
    if check_text_answer(answer, user_input):
        return {"is_correct": True}

    student_val = parse_to_fraction(str(user_input))
    if student_val is None:
        return {
            "is_correct": False,
            "feedback_msg": "Niepoprawny zapis matematyczny.",
            "soft_error": True,
        }

    correct_val = parse_to_fraction(answer)
    if student_val == correct_val:
        format_warning = check_format_mismatch(user_input, answer)
        if format_warning:
            return {
                "is_correct": False,
                "feedback_msg": format_warning,
                "soft_error": True,
            }
        return {"is_correct": True}

    return {"is_correct": False}
