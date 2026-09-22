"""Ułamki Dziesiętne — Potęgowanie: generatory Problemów."""

import random
from decimal import Decimal

from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


def _with_decimal_places(digits: int, places: int) -> Decimal:
    """`digits` with the decimal point moved `places` to the left, exactly.

    Decimal rather than float: `0.015 ** 2` is `0.00022500000000000002`, and
    `fmt_dec` prints whatever it is handed, so a float would leak that tail into
    an option string.
    """
    return Decimal(digits) / (Decimal(10) ** places)


def _square_of_tenths(lo: int, hi: int) -> dict | None:
    """Square a one-decimal value drawn from `lo`/10 to `hi`/10 inclusive."""
    v = random.randint(lo, hi) / 10
    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^2"

    c_str = fmt_dec(round(v**2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            # Doubles the base instead of multiplying it by itself.
            "multiplies_by_the_exponent": fmt_dec(round(v * 2, 1)),
            # Squares the digits and never puts the point back.
            "ignores_the_point_before_powering": fmt_dec(round(v * 10) ** 2),
            # Right shape, one hundredth off — a slip in the multiplication.
            "one_hundredth_too_large": fmt_dec(round(v**2 + 0.01, 2)),
        },
        parameters={"v": v},
    )
    if problem:
        return problem


def _power_of_small_decimal(
    bases: list[int], scales: list[int], exponent: int
) -> dict | None:
    """Raise `b`/10^`k` to `exponent`, with b drawn from `bases` and k from `scales`."""
    b = random.choice(bases)
    k = random.choice(scales)
    v = _with_decimal_places(b, k)

    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^{exponent}"

    c_str = fmt_dec(v**exponent)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            # Multiplies the base by the exponent instead of powering it.
            "multiplies_by_the_exponent": fmt_dec(v * exponent),
            # Powers the digits and never puts the point back.
            "ignores_the_point_before_powering": fmt_dec(b**exponent),
            # Keeps the operand's own decimal places instead of adding up the
            # places of every factor.
            "keeps_the_operands_decimal_places": fmt_dec(
                _with_decimal_places(b**exponent, k)
            ),
        },
        parameters={"b": b, "k": k},
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "one_hundredth_too_large",
)
def dec_pow_1() -> dict | None:
    """Kwadrat ułamka dziesiętnego (poziom 1)."""
    return _square_of_tenths(2, 9)


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "one_hundredth_too_large",
)
def dec_pow_2() -> dict | None:
    """Kwadrat liczby większej od 1 (poziom 2)."""
    return _square_of_tenths(11, 19)


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "keeps_the_operands_decimal_places",
)
def dec_pow_3() -> dict | None:
    """Kwadrat małego ułamka dziesiętnego (poziom 3)."""
    # At b=2 the multiplies_by_the_exponent value (2b) and the
    # keeps_the_operands_decimal_places value (b squared) are the same number, so
    # that draw serves a Filler in place of the third Trap (ADR-0008).
    return _power_of_small_decimal([2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 25], [2, 3], 2)


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "keeps_the_operands_decimal_places",
)
def dec_pow_4() -> dict | None:
    """Sześcian ułamka dziesiętnego (poziom 4)."""
    return _power_of_small_decimal([2, 3, 4, 5], [1, 2], 3)
