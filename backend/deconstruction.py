"""Deconstruction step registry — the pure authoring surface for walkthroughs.

A walkthrough is one registered function per Misconception, named by that
Misconception's optional `deconstruction:` key in `misconceptions.yaml`. It
takes the Problem's `parameters` and returns a fixed, ordered list of Steps —
computed once, never adaptive to the Student's prior answers. Pure: no
Session, state, or HTTP imports; nothing here reads or writes a Session.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Literal

from backend.core.utils import fmt_dec, format_answers, format_fraction_question
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


class DeconstructionContractError(Exception):
    """Raised when a Problem's `parameters` do not satisfy a walkthrough's contract.

    Distinct from a bare `KeyError` so the submission cycle can tell curriculum drift
    — a generator that stopped supplying a key its Level's Traps depend on, or a Trap
    pointed at a Misconception whose walkthrough cannot be true of the Problem — from
    a genuine defect inside a builder. Carries the Misconception slug and, where the
    violation is a missing key, the keys that were absent.
    """

    def __init__(
        self,
        misconception_slug: str,
        *,
        missing_keys: tuple[str, ...] = (),
        reason: str | None = None,
    ) -> None:
        self.misconception_slug = misconception_slug
        self.missing_keys = missing_keys
        detail = reason or f"missing parameters: {', '.join(missing_keys)}"
        super().__init__(
            f"Walkthrough '{misconception_slug}' contract violated: {detail}"
        )


@dataclass(frozen=True, slots=True)
class Declaration:
    """A registered walkthrough alongside the contract metadata it declares.

    `required_parameters` is readable without calling `builder`, which is what lets the
    curriculum-wide sweep check a generator's emitted `parameters` against every
    walkthrough its Level's Traps can reach. `answers_the_problem` states whether the
    final Step's `answer` is the Problem's own correct answer — true where the
    walkthrough carries the Student all the way there, false where it deliberately
    stops short (the expansion walkthrough ends on a numerator, not a whole fraction).
    """

    builder: StepBuilder
    required_parameters: frozenset[str]
    answers_the_problem: bool


_DECLARATIONS: dict[str, Declaration] = {}
_STEP_BUILDERS: dict[str, StepBuilder] = {}


def declares_deconstruction(
    misconception_slug: str,
    *,
    requires: tuple[str, ...],
    answers_the_problem: bool,
) -> Callable[[StepBuilder], StepBuilder]:
    """Register `func` as the walkthrough for `misconception_slug`, with its contract.

    Mirrors `declares_traps`'s decorator-registry shape: a catalogue entry naming
    an unregistered function fails at curriculum load time (`curriculum_loader.py`)
    rather than in front of a Student.

    `requires` names the `parameters` keys the walkthrough always reads; optional keys
    (the mixed-number whole parts) stay out of it. `answers_the_problem` declares
    whether the last Step lands on the Problem's answer — set it honestly, since the
    sweep asserts that invariant only where it is declared true.
    """

    def decorate(func: StepBuilder) -> StepBuilder:
        _DECLARATIONS[misconception_slug] = Declaration(
            builder=func,
            required_parameters=frozenset(requires),
            answers_the_problem=answers_the_problem,
        )
        _STEP_BUILDERS[misconception_slug] = func
        return func

    return decorate


def has_walkthrough(misconception_slug: str) -> bool:
    """Whether a walkthrough is registered for a Misconception — batch one is five of 55."""
    return misconception_slug in _DECLARATIONS


def declaration(misconception_slug: str) -> Declaration:
    """The registered walkthrough and its declared contract."""
    declared = _DECLARATIONS.get(misconception_slug)
    if declared is None:
        raise UnregisteredDeconstructionError(
            f"No walkthrough registered for misconception '{misconception_slug}'"
        )
    return declared


def _require(misconception_slug: str, parameters: StepParameters, *keys: str) -> None:
    """Raise the contract error naming every absent key, rather than the first."""
    missing = tuple(key for key in keys if key not in parameters)
    if missing:
        raise DeconstructionContractError(misconception_slug, missing_keys=missing)


def build_steps(misconception_slug: str, parameters: StepParameters) -> list[Step]:
    """Build the fixed step sequence for a Misconception from a Problem's parameters.

    Raises `DeconstructionContractError` when `parameters` omits a key the walkthrough
    declared it requires, or when the Problem's shape is one the walkthrough cannot
    truthfully address.
    """
    declared = declaration(misconception_slug)
    _require(misconception_slug, parameters, *sorted(declared.required_parameters))
    return declared.builder(parameters)


def _frac(n: int, d: int) -> str:
    return rf"\frac{{{n}}}{{{d}}}"


def _math(latex: str) -> str:
    """Delimit a LaTeX fragment for a Step `question`.

    Working lines are whole expressions the frontend hands straight to KaTeX;
    a question is Polish prose with maths embedded in it, so the maths has to be
    marked off. `$`-delimited spans are what `MathText` on the frontend renders
    (#225 — before it, `\frac{2}{5}` reached the Student as literal source).
    """
    return f"${latex}$"


# --- Batch one, walkthrough 1: operates_on_unlike_fractions_directly ---
#
# Multi-step shape (#187): fires from the Ułamki_Zwykłe addition and subtraction Traps
# whose Problem's two denominators differ. It once also carried the Ułamki_Dziesiętne
# mixed-operand Traps; #224 moved those to `mixes_fraction_and_decimal_forms_without_
# converting`, whose lesson — convert to one form first — is the one those Problems
# need. Parameters contract:
# `n1`, `d1`, `n2`, `d2` (the two fractions) and `operation` ("+" or "-"), plus the
# optional whole parts `whole1` and `whole2`, defaulting to zero.
#
# The whole parts are what let a mixed-number Level reach this walkthrough at all: each
# operand is converted to an improper fraction first (`whole * d + n`, which leaves a
# plain fraction untouched when the whole part is zero or absent), so the final step
# lands on the Problem's own answer rather than on the fractional remainder of it.
#
# The common denominator is `lcm(d1, d2)`, not the product (#225): a Student who
# reduced 5 and 10 to 10 was told 50 was the only right answer. The walkthrough ends
# on two steps rather than one — the combined numerator over the shared denominator,
# typed as a bare number, and then that fraction written in its simplest form, which
# is the Problem's own answer. The step count therefore varies: an operand whose
# denominator is already the LCD has no scaling step of its own.
#
# Equal denominators are refused. Nothing routes a like-denominator Problem here after
# #224's re-mapping, and a walkthrough whose opening line tells a Student that two
# identical denominators differ is worse than no walkthrough at all.


@declares_deconstruction(
    "operates_on_unlike_fractions_directly",
    requires=("n1", "d1", "n2", "d2", "operation"),
    answers_the_problem=True,
)
def operates_on_unlike_fractions_directly(parameters: StepParameters) -> list[Step]:
    """LCD, scale each numerator that needs it, combine numerators, simplify."""
    n1, d1 = int(parameters["n1"]), int(parameters["d1"])
    n2, d2 = int(parameters["n2"]), int(parameters["d2"])
    operation = str(parameters["operation"])
    if operation not in ("+", "-"):
        raise ValueError(f"Unsupported operation '{operation}'")
    if d1 == d2:
        raise DeconstructionContractError(
            "operates_on_unlike_fractions_directly",
            reason=(
                f"denominators are equal ({d1}); this walkthrough teaches finding a "
                "common denominator and would state a falsehood about the Problem"
            ),
        )

    whole1 = int(parameters.get("whole1", 0))
    whole2 = int(parameters.get("whole2", 0))
    is_mixed = bool(whole1 or whole2)
    opening_line = (
        f"{format_fraction_question(n1, d1, whole1)} {operation} "
        f"{format_fraction_question(n2, d2, whole2)}"
    )
    n1, n2 = whole1 * d1 + n1, whole2 * d2 + n2

    common = math.lcm(d1, d2)
    scaled_n1 = n1 * (common // d1)
    scaled_n2 = n2 * (common // d2)
    combined_numerator = (
        scaled_n1 + scaled_n2 if operation == "+" else scaled_n1 - scaled_n2
    )
    combined = _frac(combined_numerator, common)
    final_answer, _ = format_answers(combined_numerator, common)
    verb = "Dodaj" if operation == "+" else "Odejmij"

    steps = [
        Step(
            question=(
                (
                    f"Zamień liczby mieszane na ułamki niewłaściwe — to "
                    f"{_math(_frac(n1, d1))} i {_math(_frac(n2, d2))}. Mają różne "
                    "mianowniki. Jaki jest ich najmniejszy wspólny mianownik?"
                )
                if is_mixed
                else (
                    f"Ułamki {_math(_frac(n1, d1))} i {_math(_frac(n2, d2))} mają "
                    "różne mianowniki. Jaki jest ich najmniejszy wspólny mianownik?"
                )
            ),
            working_line=opening_line,
            answer=str(common),
        ),
    ]

    # With the LCD rather than the product (#225), one denominator can already be
    # the shared one — 5/10 alongside 2/5. There is no expanding to ask about, and
    # asking for a numerator that is already on screen is busywork, so that
    # operand's step is dropped rather than reworded. The two denominators differ,
    # so at most one of these can be skipped.
    if d1 != common:
        steps.append(
            Step(
                question=(
                    f"Rozszerz ułamek {_math(_frac(n1, d1))} do mianownika {common}. "
                    "Ile wynosi nowy licznik?"
                ),
                working_line=f"{_frac(n1, d1)} {operation} {_frac(n2, d2)}",
                answer=str(scaled_n1),
            )
        )
    if d2 != common:
        steps.append(
            Step(
                question=(
                    f"Rozszerz ułamek {_math(_frac(n2, d2))} do mianownika {common}. "
                    "Ile wynosi nowy licznik?"
                ),
                working_line=f"{_frac(scaled_n1, common)} {operation} {_frac(n2, d2)}",
                answer=str(scaled_n2),
            )
        )

    steps.append(
        Step(
            question=(
                f"{verb} liczniki nad wspólnym mianownikiem {common}. "
                "Ile wynosi licznik?"
            ),
            working_line=(
                f"{_frac(scaled_n1, common)} {operation} {_frac(scaled_n2, common)}"
            ),
            answer=str(combined_numerator),
        )
    )
    steps.append(
        Step(
            question=(
                f"Zostaje zapisać wynik {_math(combined)} w najprostszej postaci. "
                "Jak wygląda?"
            ),
            working_line=combined,
            answer=final_answer,
        )
    )
    return steps


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


@declares_deconstruction(
    "does_not_align_decimals_before_column_arithmetic",
    requires=("v1", "v2", "operation"),
    answers_the_problem=True,
)
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


# --- Batch one, walkthrough 3: operates_on_mixed_number_without_converting ---
#
# Precondition-conversion shape (#187): the first step is a conversion the Student
# must do before the actual operation is reachable at all, rather than going
# straight at the operation the Problem asked about. Six generators across three
# topics reference this Misconception — frac_mult_num_3, frac_mult_3, frac_mult_4,
# frac_div_num_3, frac_div_frac_3, frac_pow_3 — normalised to a shared
# `whole1`/`n1`/`d1`/`whole2`/`n2`/`d2`/`operation` contract: a whole number or plain
# fraction operand carries a zero whole part, and a power's exponent rides in `p`
# since a power has no second operand. `whole * d + n` doubles as the plain
# improper numerator when the whole part is zero, so the same formula converts a
# true mixed number or leaves a plain fraction untouched.


@declares_deconstruction(
    "operates_on_mixed_number_without_converting",
    requires=("whole1", "n1", "d1", "operation"),
    answers_the_problem=True,
)
def operates_on_mixed_number_without_converting(
    parameters: StepParameters,
) -> list[Step]:
    """2-step walkthrough: convert the mixed number, then operate on improper fractions."""
    operation = str(parameters["operation"])
    if operation not in ("*", ":", "^"):
        raise ValueError(f"Unsupported operation '{operation}'")

    whole1 = int(parameters["whole1"])
    n1, d1 = int(parameters["n1"]), int(parameters["d1"])
    improper1 = whole1 * d1 + n1
    mixed1 = format_fraction_question(n1, d1, whole1)

    if operation == "^":
        # Branch keys, so outside the declared required set: a power has no second
        # operand and a product has no exponent. Checked here so a generator that
        # omits one still raises the contract error rather than a bare `KeyError`.
        _require("operates_on_mixed_number_without_converting", parameters, "p")
        p = int(parameters["p"])
        # A power has no second operand, so the first one is the mixed number.
        target_mixed, target_improper = mixed1, improper1
        working_before = rf"\left( {mixed1} \right)^{{{p}}}"
        working_after = rf"\left( {_frac(improper1, d1)} \right)^{{{p}}}"
        result_numerator, result_denominator = improper1**p, d1**p
    else:
        _require(
            "operates_on_mixed_number_without_converting",
            parameters,
            "whole2",
            "n2",
            "d2",
        )
        whole2 = int(parameters["whole2"])
        n2, d2 = int(parameters["n2"]), int(parameters["d2"])
        improper2 = whole2 * d2 + n2
        mixed2 = format_fraction_question(n2, d2, whole2)
        # The operand carrying a whole part is the one the Student skipped
        # converting; when both carry one (frac_mult_4, frac_div_frac_3), the
        # first one stands in for the pair.
        if whole1:
            target_mixed, target_improper = mixed1, improper1
        else:
            target_mixed, target_improper = mixed2, improper2
        op_symbol = r"\cdot" if operation == "*" else ":"
        working_before = f"{mixed1} {op_symbol} {mixed2}"
        working_after = f"{_frac(improper1, d1)} {op_symbol} {_frac(improper2, d2)}"
        if operation == "*":
            result_numerator, result_denominator = improper1 * improper2, d1 * d2
        else:
            result_numerator, result_denominator = improper1 * d2, d1 * improper2

    final_answer, _ = format_answers(result_numerator, result_denominator)

    return [
        Step(
            question=(
                "Zanim wykonasz działanie, zamień liczbę mieszaną "
                f"{_math(target_mixed)} na ułamek niewłaściwy. "
                "Ile wynosi jej licznik?"
            ),
            working_line=working_before,
            answer=str(target_improper),
        ),
        Step(
            question=(
                "Teraz gdy liczba mieszana jest już ułamkiem niewłaściwym, wykonaj "
                "działanie na obu ułamkach. Ile wynosi wynik (w najprostszej postaci)?"
            ),
            working_line=working_after,
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


@declares_deconstruction(
    "expands_to_target_denominator_without_finding_factor",
    requires=("n", "d", "factor"),
    answers_the_problem=False,
)
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


def _decimal_from_display(value: str) -> Decimal:
    """Exact Decimal for a decimal string as shown on screen (Polish comma).

    Trailing zeros survive the parse, so `_decimal_places` still reports the
    place count the Student sees: `Decimal("0.50")` keeps its two places.
    """
    return Decimal(value.replace(",", "."))


@declares_deconstruction(
    "compares_decimals_by_wrong_digit_order",
    requires=("s1", "s2"),
    answers_the_problem=True,
)
def compares_decimals_by_wrong_digit_order(parameters: StepParameters) -> list[Step]:
    """2-step walkthrough: how many places to align to, then compare left to right."""
    s1, s2 = str(parameters["s1"]), str(parameters["s2"])
    v1, v2 = _decimal_from_display(s1), _decimal_from_display(s2)
    places = max(_decimal_places(v1), _decimal_places(v2))
    if v1 < v2:
        sign = "<"
    elif v1 > v2:
        sign = ">"
    else:
        sign = "="

    return [
        Step(
            question=(
                f"Uzupełnij {s1} i {s2} zerami, aby obie liczby miały tyle samo "
                "miejsc po przecinku. Ile miejsc po przecinku będą miały wtedy "
                "obie liczby?"
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
