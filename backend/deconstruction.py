"""Deconstruction step registry — the pure authoring surface for walkthroughs.

A walkthrough is one registered function per Misconception, named by that
Misconception's optional `deconstruction:` key in `misconceptions.yaml`. It
takes the Problem's `parameters` and returns a fixed, ordered list of Steps —
computed once, never adaptive to the Student's prior answers. Pure: no
Session, state, or HTTP imports; nothing here reads or writes a Session.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from backend.core.utils import format_answers
from backend.curriculum_loader import set_deconstruction_registry

StepParameters = dict[str, int | float | str]

StepInputType = Literal["typed", "ordering"]


@dataclass(frozen=True, slots=True)
class Step:
    """One question within a Deconstruction, derived from Problem parameters.

    `input_type` defaults to a typed answer graded against `answer`. An
    `"ordering"` step instead carries `items` — the choices the Student
    arranges — and `answer` holds their correct order, joined with
    `step_grading.ORDERING_ANSWER_SEPARATOR` (see #186's priority-ladder step).
    """

    question: str
    working_line: str | None
    answer: str
    input_type: StepInputType = "typed"
    items: tuple[str, ...] | None = None


StepBuilder = Callable[[StepParameters], list[Step]]


class UnregisteredDeconstructionError(Exception):
    """Raised when `build_steps` is asked for a Misconception with no walkthrough."""


_STEP_BUILDERS: dict[str, StepBuilder] = {}


def declares_deconstruction(
    misconception_slug: str,
) -> Callable[[StepBuilder], StepBuilder]:
    """Register `func` as the walkthrough for `misconception_slug`.

    Mirrors `declares_traps`'s decorator-registry shape: a catalogue entry naming
    an unregistered function fails at curriculum load time (`curriculum_loader.py`)
    rather than in front of a Student.
    """

    def decorate(func: StepBuilder) -> StepBuilder:
        _STEP_BUILDERS[misconception_slug] = func
        return func

    return decorate


def has_walkthrough(misconception_slug: str) -> bool:
    """Whether a walkthrough is registered for a Misconception — batch one is five of 55."""
    return misconception_slug in _STEP_BUILDERS


def build_steps(misconception_slug: str, parameters: StepParameters) -> list[Step]:
    """Build the fixed step sequence for a Misconception from a Problem's parameters."""
    builder = _STEP_BUILDERS.get(misconception_slug)
    if builder is None:
        raise UnregisteredDeconstructionError(
            f"No walkthrough registered for misconception '{misconception_slug}'"
        )
    return builder(parameters)


def _frac(n: int, d: int) -> str:
    return rf"\frac{{{n}}}{{{d}}}"


# --- Batch one, walkthrough 1: operates_on_unlike_fractions_directly ---
#
# Multi-step, cross-Chapter shape (#187): fires from both Ułamki_Zwykłe addition/
# subtraction Traps and Ułamki_Dziesiętne mixed-operand Traps, since the underlying
# error — combining unlike-denominator fractions without a common denominator — is
# the same regardless of which Chapter generated the Problem. Parameters contract:
# `n1`, `d1`, `n2`, `d2` (the two fractions) and `operation` ("+" or "-").


@declares_deconstruction("operates_on_unlike_fractions_directly")
def operates_on_unlike_fractions_directly(parameters: StepParameters) -> list[Step]:
    """4-step walkthrough: common denominator, scale each numerator, combine."""
    n1, d1 = int(parameters["n1"]), int(parameters["d1"])
    n2, d2 = int(parameters["n2"]), int(parameters["d2"])
    operation = str(parameters["operation"])
    if operation not in ("+", "-"):
        raise ValueError(f"Unsupported operation '{operation}'")

    common = d1 * d2
    scaled_n1 = n1 * d2
    scaled_n2 = n2 * d1
    combined_numerator = (
        scaled_n1 + scaled_n2 if operation == "+" else scaled_n1 - scaled_n2
    )
    final_answer, _ = format_answers(combined_numerator, common)
    verb = "Dodaj" if operation == "+" else "Odejmij"

    return [
        Step(
            question=(
                f"Ułamki {_frac(n1, d1)} i {_frac(n2, d2)} mają różne mianowniki. "
                "Jaki jest ich wspólny mianownik?"
            ),
            working_line=f"{_frac(n1, d1)} {operation} {_frac(n2, d2)}",
            answer=str(common),
        ),
        Step(
            question=(
                f"Rozszerz ułamek {_frac(n1, d1)} do mianownika {common}. "
                "Ile wynosi nowy licznik?"
            ),
            working_line=f"{_frac(n1, d1)} {operation} {_frac(n2, d2)}",
            answer=str(scaled_n1),
        ),
        Step(
            question=(
                f"Rozszerz ułamek {_frac(n2, d2)} do mianownika {common}. "
                "Ile wynosi nowy licznik?"
            ),
            working_line=f"{_frac(scaled_n1, common)} {operation} {_frac(n2, d2)}",
            answer=str(scaled_n2),
        ),
        Step(
            question=(
                f"{verb} liczniki nad wspólnym mianownikiem {common}. "
                "Ile wynosi wynik?"
            ),
            working_line=(
                f"{_frac(scaled_n1, common)} {operation} {_frac(scaled_n2, common)}"
            ),
            answer=final_answer,
        ),
    ]


# --- Batch one, walkthrough 5: expands_to_target_denominator_without_finding_factor ---
#
# Hidden-operand shape (#187): the multiplier the Student needs — how many times the
# denominator grew — is never written as its own number in the Problem's question
# text (`frac_exp_2` states only the target denominator, `d * factor`). The
# walkthrough reaches it via `parameters["factor"]` rather than deriving it from what
# is on screen, which is what proves `parameters` earns its keep. Parameters
# contract: `n`, `d`, `factor`; the target denominator is recomputed here, never passed.


@declares_deconstruction("expands_to_target_denominator_without_finding_factor")
def expands_to_target_denominator_without_finding_factor(
    parameters: StepParameters,
) -> list[Step]:
    """2-step walkthrough: find the hidden factor, then scale the numerator by it."""
    n, d = int(parameters["n"]), int(parameters["d"])
    factor = int(parameters["factor"])
    target_d = d * factor
    scaled_n = n * factor

    return [
        Step(
            question=(
                f"Mianownik ma urosnąć z {d} do {target_d}. "
                "Ile razy większy jest nowy mianownik od starego?"
            ),
            working_line=_frac(n, d),
            answer=str(factor),
        ),
        Step(
            question=(
                "Ten sam mnożnik działa na obie części ułamka. "
                f"Pomnóż licznik {n} przez {factor}. Ile wynosi nowy licznik?"
            ),
            working_line=rf"{_frac(n, d)} \times {factor}",
            answer=str(scaled_n),
        ),
    ]


set_deconstruction_registry(_STEP_BUILDERS)
