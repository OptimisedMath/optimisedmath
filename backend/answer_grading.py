"""Answer grading — Correct / Trap / Wrong / soft-error taxonomy behind one seam."""

from __future__ import annotations

from fractions import Fraction
from typing import Literal, TypedDict

import backend.config as config
from backend.core.units import convert, normalize_unit, split_answer
from backend.core.utils import (
    FILLER_SLUG,
    ProblemDict,
    check_format_mismatch,
    check_text_answer,
    parse_to_fraction,
)
from backend.models import InputMode

# The grader's own finer vocabulary on its way to a verdict (ADR-0016).
# `models.AnswerOutcome` is the four-bucket collapse of it that telemetry stores.
GradedOutcome = Literal[
    "correct",
    "trap",
    "wrong",
    "syntax_error",
    "format_mismatch",
    "unsimplified",
]

_SYNTAX_ERROR_MESSAGE = "Niepoprawny zapis matematyczny."


class EvalResult(TypedDict, total=False):
    lock_answer: bool
    feedback_type: str
    feedback_msg: str
    #: Always set — every path through `grade` names its outcome (ADR-0016).
    answer_outcome: GradedOutcome
    trap_slug: str
    #: Set only by a grader-synthesized Trap, which has no Level `traps:` entry
    #: for `_resolve_misconception_slug` to look its Misconception up from.
    misconception_slug: str


def _correct() -> EvalResult:
    """The Correct verdict — the one place every path that reaches one names it."""
    return {"lock_answer": True, "answer_outcome": "correct"}


def _trap(slug: str, message: str) -> EvalResult:
    """The Trap verdict — an anticipated wrong answer, carrying its own prose."""
    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": message,
        "answer_outcome": "trap",
        "trap_slug": slug,
    }


def _wrong(message: str) -> EvalResult:
    """The Wrong verdict — incorrect, with no anticipated rule behind it."""
    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": message,
        "answer_outcome": "wrong",
    }


def _soft_error(outcome: GradedOutcome, message: str) -> EvalResult:
    """A Soft Error verdict, in the finer flavour `outcome` names.

    The only verdict that leaves `lock_answer` False, which is what buys the
    Student a free retry — ADR-0016 relies on the two never disagreeing.
    """
    return {
        "lock_answer": False,
        "feedback_type": "info",
        "feedback_msg": message,
        "answer_outcome": outcome,
    }


def is_correct(eval_result: EvalResult) -> bool:
    """Whether a graded submission was Correct.

    The one reader of `answer_outcome` that callers outside grading need, so
    Streak, XP and the wire response never spell the comparison out themselves
    (#253 deleted the `is_correct` key they used to read).
    """
    return eval_result.get("answer_outcome") == "correct"


def _message_for(problem: ProblemDict, slug: str) -> str:
    """The prose a Problem authors for `slug`, or the generic Wrong message."""
    return problem.get("messages", {}).get(slug, config.DEFAULT_WRONG_MESSAGE)


def _match_trap_feedback(
    user_input: str, student_val: Fraction, problem: ProblemDict
) -> EvalResult | None:
    """Return trap/wrong feedback if user input matches a known distractor."""
    options_map = problem.get("options_map", {})
    for opt_str, opt_type in options_map.items():
        if opt_type == "correct":
            continue
        matched = check_text_answer(opt_str, user_input)
        if not matched:
            opt_val = parse_to_fraction(opt_str)
            matched = opt_val is not None and student_val == opt_val
        if matched:
            return _trap(opt_type, _message_for(problem, opt_type))
    return None


def _synthesized_unit_trap(slug: str, misconception: str, message: str) -> EvalResult:
    """A Trap the grader raises itself, carrying its own Misconception.

    Authorized for Units only (ADR-0005): the rule is mechanically detectable, so
    making 22 Geometria generators author every wrong Unit would be combinatorial
    work to state something already general.
    """
    result = _trap(slug, message)
    result["misconception_slug"] = misconception
    return result


def _grade_with_unit(
    user_input: str, problem: ProblemDict, expected_unit: str
) -> EvalResult:
    """Grade a typed answer that must carry a Unit.

    Ordering is the decision (ADR-0005): split, then dimension, then convert, then
    compare — so `0,0024 m²` resolves Correct for `24 cm²` before any Trap is
    considered, and Trap matching only ever sees answers already established as
    wrong. A missing Unit is Wrong, never a Soft Error: here the Unit is part of
    the answer.
    """
    number_text, raw_unit = split_answer(user_input)
    student_val = parse_to_fraction(number_text)
    if student_val is None:
        # A number that is not a number is a notation Soft Error, and stays one
        # here. Only the Unit half of the answer is exempt from Soft Errors.
        return _soft_error("syntax_error", _SYNTAX_ERROR_MESSAGE)

    if raw_unit is None:
        return _wrong(config.MISSING_UNIT_MESSAGE)

    unit = normalize_unit(raw_unit)
    if unit is None:
        return _wrong(config.UNKNOWN_UNIT_MESSAGE)

    correct_val = parse_to_fraction(str(problem["correct"]))
    converted = convert(student_val, unit, expected_unit)

    if converted is not None and converted == correct_val:
        return _correct()

    # The number decides which Trap it is (#229), and it is matched *after*
    # conversion, so a Trap number typed in a legal other Unit still names its
    # own rule rather than falling through to the generic message.
    comparable = converted if converted is not None else student_val
    trap_result = _match_trap_feedback(number_text, comparable, problem)
    if trap_result:
        return trap_result

    if student_val == correct_val:
        if converted is None:
            return _synthesized_unit_trap(
                config.UNIT_DIMENSION_TRAP_SLUG,
                config.UNIT_DIMENSION_MISCONCEPTION,
                config.WRONG_DIMENSION_UNIT_MESSAGE,
            )
        return _synthesized_unit_trap(
            config.UNIT_SCALE_TRAP_SLUG,
            config.UNIT_SCALE_MISCONCEPTION,
            config.WRONG_SCALE_UNIT_MESSAGE,
        )

    return _wrong(_message_for(problem, FILLER_SLUG))


def grade(
    user_input: str, problem: ProblemDict, *, input_mode: InputMode = "radio"
) -> EvalResult:
    """Grade a submission against a generated problem.

    Handles Radio mode (options_map), Typing mode (parse + grading_policy),
    trap/wrong feedback, and format-mismatch soft errors. Every path sets
    `answer_outcome` — it is total, never absent (ADR-0016).
    """
    options_map = problem.get("options_map", {})

    # --- 1. RADIO MODE ---
    if input_mode == "radio" and "options" in problem and len(problem["options"]) > 0:
        option_type = options_map.get(user_input)
        if option_type == "correct":
            return _correct()
        # An option absent from `options_map` is as unanticipated as a Filler, so
        # both grade as Wrong; any other option type names a Trap.
        if option_type is None or option_type == FILLER_SLUG:
            return _wrong(_message_for(problem, FILLER_SLUG))
        return _trap(option_type, _message_for(problem, option_type))

    # --- 2. TYPING MODE ---
    expected_unit = problem.get("expected_unit")
    if expected_unit:
        return _grade_with_unit(user_input, problem, str(expected_unit))

    policy = problem.get("grading_policy", "standard")

    if check_text_answer(problem["correct"], user_input):
        return _correct()

    student_val = parse_to_fraction(str(user_input))
    correct_val = parse_to_fraction(problem["correct"])

    if student_val is None:
        return _soft_error("syntax_error", _SYNTAX_ERROR_MESSAGE)

    if student_val == correct_val:
        format_warning = check_format_mismatch(user_input, problem["correct"])
        if format_warning:
            return _soft_error("format_mismatch", format_warning)

        # `exact_match_only` deliberately returns nothing here: on those Levels
        # the requested form is part of the answer, so a value-equal answer in
        # another form is Wrong and falls through to section 3 (#312).
        if policy == "equivalent_accepted":
            return _correct()
        if policy == "standard":
            return _soft_error(
                "unsimplified",
                "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!",
            )

    # --- 3. TEXT MODE TRAP SCANNER ---
    trap_result = _match_trap_feedback(user_input, student_val, problem)
    if trap_result:
        return trap_result

    return _wrong(_message_for(problem, FILLER_SLUG))
