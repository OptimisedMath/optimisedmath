"""Ułamki Zwykłe — Potęgowanie: generatory Problemów."""

import random
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps("raises_only_the_numerator", "multiplies_by_the_exponent")
def frac_pow_1() -> dict | None:
    """Kwadrat ułamka (poziom 1)."""
    d = random.randint(3, 8)
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
            "multiplies_by_the_exponent": format_answers(n * p, d * p)[0],
        },
        fillers=[format_answers((n**p) + 1, d**p)[0]],
        parameters={"n": n, "d": d, "p": p},
    )
    if problem:
        return problem


@declares_traps("raises_only_the_numerator", "multiplies_by_the_exponent")
def frac_pow_2() -> dict | None:
    """Sześcian ułamka (poziom 2)."""
    # Keeping denominator up to 5 so cubes don't get absurdly large
    d = random.randint(2, 5)
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
            "multiplies_by_the_exponent": format_answers(n * p, d * p)[0],
        },
        fillers=[format_answers((n**p) + 1, d**p)[0]],
        parameters={"n": n, "d": d, "p": p},
    )
    if problem:
        return problem


@declares_traps("raises_the_parts_separately", "raises_only_the_numerator")
def frac_pow_3() -> dict | None:
    """Potęgowanie liczby mieszanej (poziom 3)."""
    w = random.randint(1, 2)
    p = random.randint(2, 3)
    # Cap denominator if p=3 to prevent math from becoming tedious
    d = random.randint(2, 3) if p == 3 else random.randint(2, 4)
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
        fillers=[format_answers(num**p + 1, d**p)[0]],
        parameters={"whole1": w, "n1": n, "d1": d, "p": p, "operation": "^"},
    )
    if problem:
        return problem
