"""Answer grading — Correct / Trap / Wrong / soft-error taxonomy behind one seam."""

from __future__ import annotations

from fractions import Fraction
from typing import TypedDict

import backend.config as config
from backend.core.units import convert, normalize_unit, split_answer
from backend.core.utils import (
    FILLER_SLUG,
    ProblemDict,
    check_format_mismatch,
    check_text_answer,
    parse_to_fraction,
)


class EvalResult(TypedDict, total=False):
    is_correct: bool
    lock_answer: bool
    feedback_type: str
    feedback_msg: str
    answer_outcome: str
    trap_slug: str
    #: Set only by a grader-synthesized Trap, which has no Level `traps:` entry
    #: for `_resolve_misconception_slug` to look its Misconception up from.
    misconception_slug: str


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
            msg_text = problem.get("messages", {}).get(
                opt_type, "Niepoprawna odpowiedź, spróbuj ponownie."
            )
            return {
                "lock_answer": True,
                "feedback_type": "warning",
                "feedback_msg": msg_text,
                "answer_outcome": "trap",
                "trap_slug": opt_type,
            }
    return None


def _unit_wrong(message: str) -> EvalResult:
    """A Unit fault with no rule behind it — missing or not a Unit at all."""
    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": message,
        "answer_outcome": "wrong",
    }


def _synthesized_unit_trap(slug: str, misconception: str, message: str) -> EvalResult:
    """A Trap the grader raises itself, carrying its own Misconception.

    Authorized for Units only (ADR-0005): the rule is mechanically detectable, so
    making 22 Geometria generators author every wrong Unit would be combinatorial
    work to state something already general.
    """
    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": message,
        "answer_outcome": "trap",
        "trap_slug": slug,
        "misconception_slug": misconception,
    }


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
        return {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "Niepoprawny zapis matematyczny.",
            "answer_outcome": "syntax_error",
        }

    if raw_unit is None:
        return _unit_wrong(config.MISSING_UNIT_MESSAGE)

    unit = normalize_unit(raw_unit)
    if unit is None:
        return _unit_wrong(config.UNKNOWN_UNIT_MESSAGE)

    correct_val = parse_to_fraction(str(problem["correct"]))
    converted = convert(student_val, unit, expected_unit)

    if converted is not None and converted == correct_val:
        return {"is_correct": True, "lock_answer": True}

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

    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": problem.get("messages", {}).get(
            FILLER_SLUG, config.DEFAULT_WRONG_MESSAGE
        ),
        "answer_outcome": "wrong",
    }


def grade(
    user_input: str, problem: ProblemDict, *, is_input_mode: bool = False
) -> EvalResult:
    """Grade a submission against a generated problem.

    Handles multiple-choice (options_map), open-text (parse + grading_policy),
    trap/wrong feedback, and format-mismatch soft errors.
    """
    options_map = problem.get("options_map", {})

    # --- 1. MULTIPLE CHOICE MODE ---
    if not is_input_mode and "options" in problem and len(problem["options"]) > 0:
        is_correct = options_map.get(user_input) == "correct"
        if is_correct:
            return {"is_correct": True, "lock_answer": True}

        msg_key = options_map.get(user_input)
        msg_text = problem.get("messages", {}).get(
            msg_key or FILLER_SLUG, "Niepoprawna odpowiedź, spróbuj ponownie."
        )
        if msg_key is None:
            outcome = "wrong"
        elif msg_key == FILLER_SLUG:
            outcome = "wrong"
        else:
            outcome = "trap"
        eval_outcome: EvalResult = {
            "lock_answer": True,
            "feedback_type": "warning",
            "feedback_msg": msg_text,
            "answer_outcome": outcome,
        }
        if outcome == "trap":
            eval_outcome["trap_slug"] = msg_key
        return eval_outcome

    # --- 2. TEXT INPUT MODE ---
    expected_unit = problem.get("expected_unit")
    if expected_unit:
        return _grade_with_unit(user_input, problem, str(expected_unit))

    policy = problem.get("grading_policy", "standard")

    if check_text_answer(problem["correct"], user_input):
        return {"is_correct": True, "lock_answer": True}

    student_val = parse_to_fraction(str(user_input))
    correct_val = parse_to_fraction(problem["correct"])

    if student_val is None:
        return {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "Niepoprawny zapis matematyczny.",
            "answer_outcome": "syntax_error",
        }

    if student_val == correct_val:
        format_warning = check_format_mismatch(user_input, problem["correct"])
        if format_warning:
            return {
                "lock_answer": False,
                "feedback_type": "info",
                "feedback_msg": format_warning,
                "answer_outcome": "format_mismatch",
            }

        if policy == "exact_match_only":
            trap_result = _match_trap_feedback(user_input, student_val, problem)
            if trap_result:
                return trap_result
            return {
                "lock_answer": True,
                "feedback_type": "warning",
                "feedback_msg": "Zapisz ułamek w dokładnie takiej postaci, o jaką prosi polecenie!",
                "answer_outcome": "exact_match_violation",
            }
        if policy == "equivalent_accepted":
            return {"is_correct": True, "lock_answer": True}
        return {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!",
            "answer_outcome": "unsimplified",
        }

    # --- 3. TEXT MODE TRAP SCANNER ---
    trap_result = _match_trap_feedback(user_input, student_val, problem)
    if trap_result:
        return trap_result

    msg_text = problem.get("messages", {}).get(
        FILLER_SLUG, "Niepoprawna odpowiedź, spróbuj ponownie."
    )
    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": msg_text,
        "answer_outcome": "wrong",
    }
