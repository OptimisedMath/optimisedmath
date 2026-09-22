"""Ułamki Dziesiętne — Potęgowanie: generatory Problemów."""

import random
from decimal import Decimal

from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


def _dec_pow_value(b: int, k: int) -> Decimal:
    """Exact `b / 10^k`, as a Decimal (#264)."""
    return Decimal(b) / (Decimal(10) ** k)


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "one_hundredth_too_large",
)
def dec_pow_1() -> dict | None:
    """Kwadrat ułamka dziesiętnego (poziom 1)."""
    v = random.randint(2, 9) / 10
    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^2"

    c_str = fmt_dec(round(v**2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_by_the_exponent": fmt_dec(round(v * 2, 1)),
            "ignores_the_point_before_powering": fmt_dec(round(v * 10) ** 2),
            "one_hundredth_too_large": fmt_dec(round(v**2 + 0.01, 2)),
        },
        parameters={"v": v},
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "one_hundredth_too_large",
)
def dec_pow_2() -> dict | None:
    """Kwadrat liczby większej od 1 (poziom 2)."""
    v = random.randint(11, 19) / 10
    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^2"

    c_str = fmt_dec(round(v**2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_by_the_exponent": fmt_dec(round(v * 2, 1)),
            "ignores_the_point_before_powering": fmt_dec(round(v * 10) ** 2),
            "one_hundredth_too_large": fmt_dec(round(v**2 + 0.01, 2)),
        },
        parameters={"v": v},
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "keeps_the_operands_decimal_places",
)
def dec_pow_3() -> dict | None:
    """Kwadrat małego ułamka dziesiętnego (poziom 3)."""
    b = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 25])
    k = random.choice([2, 3])
    v = _dec_pow_value(b, k)

    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^2"

    c_str = fmt_dec(v**2)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_by_the_exponent": fmt_dec(v * 2),
            "ignores_the_point_before_powering": fmt_dec(b**2),
            "keeps_the_operands_decimal_places": fmt_dec(_dec_pow_value(b**2, k)),
        },
        parameters={"b": b, "k": k},
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_by_the_exponent",
    "ignores_the_point_before_powering",
    "keeps_the_operands_decimal_places",
)
def dec_pow_4() -> dict | None:
    """Sześcian ułamka dziesiętnego (poziom 4)."""
    b = random.choice([2, 3, 4, 5])
    k = random.choice([1, 2])
    v = _dec_pow_value(b, k)

    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^3"

    c_str = fmt_dec(v**3)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_by_the_exponent": fmt_dec(v * 3),
            "ignores_the_point_before_powering": fmt_dec(b**3),
            "keeps_the_operands_decimal_places": fmt_dec(_dec_pow_value(b**3, k)),
        },
        parameters={"b": b, "k": k},
    )
    if problem:
        return problem
