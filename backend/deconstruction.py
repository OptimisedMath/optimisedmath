"""Deconstruction step registry — the pure authoring surface for walkthroughs.

A walkthrough is one registered function per Misconception, named by that
Misconception's optional `deconstruction:` key in `misconceptions.yaml`. It
takes the Problem's `parameters` and returns a fixed, ordered list of Steps —
computed once, never adaptive to the Student's prior answers. Pure: no
Session, state, or HTTP imports; nothing here reads or writes a Session.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Literal

from backend.core.utils import fmt_dec, format_answers
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


# --- Batch one, walkthrough 2: does_not_align_decimals_before_column_arithmetic ---
#
# Column-layout shape (#187): the working line carries a vertical column arrangement
# (a LaTeX `array`) rather than a single inline expression — this is the walkthrough
# that establishes how a laid-out form survives the one-line-replacing-the-last
# pacing device. Parameters contract: `v1`, `v2` (the two decimal operands) and
# `operation` ("+" or "-"), supplied uniformly by every generator whose Traps
# reference this Misconception (dec_add_1, dec_add_3, dec_sub_2 — normalised to this
# shared shape here, regardless of how many decimal places each operand happens to
# carry on its own).


def _as_decimal(value: int | float | str) -> Decimal:
    """Exact Decimal for a Problem parameter, via `str` so 0.1 stays 0.1."""
    return Decimal(str(float(value)))


def _decimal_places(value: Decimal) -> int:
    exponent = value.as_tuple().exponent
    # NaN and infinity report a str sentinel instead of an int exponent. No
    # generator produces either; count them as whole numbers rather than crash.
    return max(0, -exponent) if isinstance(exponent, int) else 0


def _pad_to_places(value: Decimal, places: int) -> str:
    """Render `value` with exactly `places` digits after the Polish decimal comma."""
    return format(value.quantize(Decimal(1).scaleb(-places)), "f").replace(".", ",")


def _places_noun(places: int) -> str:
    """Polish declension after a numeral: 1 miejsce, 2-4 miejsca, 5+ miejsc."""
    if places == 1:
        return "miejsce"
    if places in (2, 3, 4):
        return "miejsca"
    return "miejsc"


def _column(top: str, operation: str, bottom: str, *, answer_row: bool = False) -> str:
    """A written-arithmetic column: two operands, an operator, and a rule beneath.

    `answer_row` adds a bare `?` under the rule, never the value itself. It is
    also what keeps step two's column textually distinct from step one's when
    both operands already share a decimal-place count and the padding is a no-op
    (every dec_add_1 Problem, by construction). The frontend keys its
    flash-on-change on the working line's text, so two byte-identical lines
    would silently skip the replay.
    """
    answer = "?" if answer_row else ""
    return (
        rf"\begin{{array}}{{r}} {top} \\ {operation}\ {bottom} \\ \hline "
        rf"{answer}\end{{array}}"
    )


@declares_deconstruction("does_not_align_decimals_before_column_arithmetic")
def does_not_align_decimals_before_column_arithmetic(
    parameters: StepParameters,
) -> list[Step]:
    """2-step walkthrough: find the shared decimal-place count, then compute aligned."""
    v1, v2 = _as_decimal(parameters["v1"]), _as_decimal(parameters["v2"])
    operation = str(parameters["operation"])
    if operation not in ("+", "-"):
        raise ValueError(f"Unsupported operation '{operation}'")

    places = max(_decimal_places(v1), _decimal_places(v2))
    raw_v1, raw_v2 = fmt_dec(v1), fmt_dec(v2)
    padded_v1, padded_v2 = _pad_to_places(v1, places), _pad_to_places(v2, places)
    combined = v1 + v2 if operation == "+" else v1 - v2

    return [
        Step(
            question=(
                "Żeby policzyć to w kolumnie, przecinek musi stać dokładnie pod "
                "przecinkiem. Ile miejsc po przecinku muszą mieć obie liczby — "
                f"{raw_v1} i {raw_v2} — żeby to zrobić?"
            ),
            working_line=_column(raw_v1, operation, raw_v2),
            answer=str(places),
        ),
        Step(
            question=(
                "Dopisz zera tam, gdzie trzeba, aż obie liczby będą miały "
                f"{places} {_places_noun(places)} po przecinku, i policz wynik "
                f"w kolumnie. Ile wynosi {raw_v1} {operation} {raw_v2}?"
            ),
            working_line=_column(padded_v1, operation, padded_v2, answer_row=True),
            answer=fmt_dec(combined),
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


# --- Batch one, walkthrough 4: compares_decimals_by_wrong_digit_order ---
#
# No-working-line shape (#187): there is no expression to transform when comparing
# two decimals, so every step here authors `working_line: null` — the walkthrough
# that proves the nullable working line is load-bearing rather than decorative.
# Parameters contract: `s1`, `s2`, the two decimal strings exactly as shown in the
# Problem (Polish comma, trailing zeros preserved where the generator deliberately
# carries them), normalised across dec_compare_1/2/3, the three generators whose
# Traps reference this Misconception.


def _decimal_places_in_string(value: str) -> int:
    return len(value.split(",", 1)[1]) if "," in value else 0


@declares_deconstruction("compares_decimals_by_wrong_digit_order")
def compares_decimals_by_wrong_digit_order(parameters: StepParameters) -> list[Step]:
    """2-step walkthrough: how many places to align to, then compare left to right."""
    s1, s2 = str(parameters["s1"]), str(parameters["s2"])
    v1, v2 = Decimal(s1.replace(",", ".")), Decimal(s2.replace(",", "."))
    places = max(_decimal_places_in_string(s1), _decimal_places_in_string(s2))
    sign = "<" if v1 < v2 else ">" if v1 > v2 else "="

    return [
        Step(
            question=(
                f"Uzupełnij {s1} i {s2} zerami, aby obie liczby miały tyle samo "
                "miejsc po przecinku. Ile miejsc po przecinku będą miały wtedy obie liczby?"
            ),
            working_line=None,
            answer=str(places),
        ),
        Step(
            question=(
                "Teraz porównaj cyfry po przecinku od lewej strony — pierwsza "
                f"różnica rozstrzyga. Jaki znak (<, > czy =) łączy {s1} i {s2}?"
            ),
            working_line=None,
            answer=sign,
        ),
    ]


set_deconstruction_registry(_STEP_BUILDERS)
