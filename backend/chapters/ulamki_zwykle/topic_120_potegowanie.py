"""Ułamki Zwykłe — Potęgowanie: generatory Problemów."""

import random
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)

# Cube caps for the Levels that raise to the third power (#263): 7³ = 343 puts the
# answer's denominator outside this Topic's arithmetic, and a Student cubes a mixed
# number's improper numerator w*d+n, not d alone, so that base is capped too.
_MAX_CUBE_DENOMINATOR = 6
_MAX_CUBE_BASE = 8


def _draw_cubable_mixed_number(w: int) -> tuple[int, int]:
    """Draw `(d, n)` whose mixed number `w n/d` has a cube a Student can still do.

    Redraws until the improper numerator fits `_MAX_CUBE_BASE`, so `w` has to stay
    small enough that `2 * w + 1` — the smallest base any draw reaches — fits it.
    """
    while True:
        d = random.randint(2, _MAX_CUBE_DENOMINATOR)
        n = random.randint(1, d - 1)
        if w * d + n <= _MAX_CUBE_BASE:
            return d, n


@declares_traps("raises_only_the_numerator", "multiplies_by_the_exponent")
def frac_pow_1() -> dict | None:
    """Kwadrat ułamka (poziom 1)."""
    d = random.randint(2, 10)
    n = random.randint(1, d - 1)
    p = 2

    q_str = (
        rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d)} \right)^{{{p}}}"
    )

    c_str, _ = format_answers(n**p, d**p)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "raises_only_the_numerator": format_answers(n**p, d)[0],
            "multiplies_by_the_exponent": format_answers(n * p, d)[0],
        },
        parameters={"n": n, "d": d, "p": p},
    )
    if problem:
        return problem


@declares_traps(
    "raises_only_the_numerator",
    "multiplies_by_the_exponent",
    "squares_instead_of_cubing",
)
def frac_pow_2() -> dict | None:
    """Sześcian ułamka (poziom 2)."""
    d = random.randint(2, _MAX_CUBE_DENOMINATOR)
    n = random.randint(1, d - 1)
    p = 3

    q_str = (
        rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d)} \right)^{{{p}}}"
    )

    c_str, _ = format_answers(n**p, d**p)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "raises_only_the_numerator": format_answers(n**p, d)[0],
            "multiplies_by_the_exponent": format_answers(n * p, d)[0],
            "squares_instead_of_cubing": format_answers(n**2, d**2)[0],
        },
        parameters={"n": n, "d": d, "p": p},
    )
    if problem:
        return problem


@declares_traps("raises_the_parts_separately", "raises_only_the_numerator")
def frac_pow_3() -> dict | None:
    """Potęgowanie liczby mieszanej (poziom 3)."""
    w = random.randint(1, 2)
    p = random.randint(2, 3)
    if p == 3:
        d, n = _draw_cubable_mixed_number(w)
    else:
        d = random.randint(2, 10)
        n = random.randint(1, d - 1)

    q_str = (
        rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d, w)} \right)^{{{p}}}"
    )

    num = (w * d) + n
    c_str, _ = format_answers(num**p, d**p)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "raises_the_parts_separately": format_answers(n**p, d**p, w**p)[0],
            "raises_only_the_numerator": format_answers(num**p, d)[0],
        },
        parameters={"whole1": w, "n1": n, "d1": d, "p": p, "operation": "^"},
    )
    if problem:
        return problem
