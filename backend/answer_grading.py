"""Answer grading — Correct / Trap / Wrong / soft-error taxonomy behind one seam."""

from __future__ import annotations

from fractions import Fraction
from typing import TypedDict

from backend.core.utils import ProblemDict, check_text_answer, parse_to_fraction


class EvalResult(TypedDict, total=False):
    is_correct: bool
    lock_answer: bool
    feedback_type: str
    feedback_msg: str
    trap_id: str


def _match_trap_feedback(
    user_input: str, student_val: Fraction, problem: ProblemDict
) -> EvalResult | None:
    """Return trap/wrong feedback if user input matches a known distractor."""
    options_map = problem.get("options_map", {})
    for opt_str, opt_type in options_map.items():
        if opt_type not in ("t1", "t2", "t3", "w1", "w2"):
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
                "trap_id": opt_type,
            }
    return None


def _check_format_mismatch(user_text: str, correct_latex: str) -> str | None:
    """Intercept answers that are mathematically correct but use the wrong notation."""
    user_str = str(user_text)
    if "/" in user_str and "," in correct_latex:
        return "Wynik poprawny matematycznie, ale to jest zadanie z ułamków dziesiętnych! Zapisz odpowiedź używając przecinka, a nie ułamka zwykłego."
    if ("," in user_str or "." in user_str) and "\\frac" in correct_latex:
        return "Wynik poprawny matematycznie, ale w tym zadaniu powinieneś użyć ułamka zwykłego, a nie dziesiętnego!"
    return None


def grade(
    user_input: str, problem: ProblemDict, *, is_text_mode: bool = False
) -> EvalResult:
    """Grade a submission against a generated problem.

    Handles multiple-choice (options_map), open-text (parse + grading_policy),
    trap/wrong feedback, and format-mismatch soft errors.
    """
    options_map = problem.get("options_map", {})

    # --- 1. MULTIPLE CHOICE MODE ---
    if not is_text_mode and "options" in problem and len(problem["options"]) > 0:
        is_correct = options_map.get(user_input) == "correct"
        if is_correct:
            return {"is_correct": True, "lock_answer": True}

        msg_key = options_map.get(user_input, "w1")
        msg_text = problem.get("messages", {}).get(
            msg_key, "Niepoprawna odpowiedź, spróbuj ponownie."
        )
        return {
            "lock_answer": True,
            "feedback_type": "warning",
            "feedback_msg": msg_text,
            "trap_id": msg_key,
        }

    # --- 2. TEXT INPUT MODE ---
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
            "trap_id": "syntax_error",
        }

    if student_val == correct_val:
        format_warning = _check_format_mismatch(user_input, problem["correct"])
        if format_warning:
            return {
                "lock_answer": False,
                "feedback_type": "info",
                "feedback_msg": format_warning,
                "trap_id": "format_mismatch",
            }

        if policy == "exact_match_only":
            trap_result = _match_trap_feedback(user_input, student_val, problem)
            if trap_result:
                return trap_result
            return {
                "lock_answer": True,
                "feedback_type": "warning",
                "feedback_msg": "Zapisz ułamek w dokładnie takiej postaci, o jaką prosi polecenie!",
                "trap_id": "exact_match_violation",
            }
        if policy == "equivalent_accepted":
            return {"is_correct": True, "lock_answer": True}
        return {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!",
            "trap_id": "unsimplified",
        }

    # --- 3. TEXT MODE TRAP SCANNER ---
    trap_result = _match_trap_feedback(user_input, student_val, problem)
    if trap_result:
        return trap_result

    msg_text = problem.get("messages", {}).get(
        "w1", "Niepoprawna odpowiedź, spróbuj ponownie."
    )
    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": msg_text,
        "trap_id": "w1",
    }


def evaluate_answer(
    user_input: str, problem: ProblemDict, is_text_mode: bool = False
) -> EvalResult:
    """Alias for :func:`grade` — kept for existing call sites."""
    return grade(user_input, problem, is_text_mode=is_text_mode)
