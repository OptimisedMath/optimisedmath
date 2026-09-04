"""Ułamki Zwykłe — Porównywanie: generatory Problemów."""

import random
from backend.core.utils import (
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps("reverses_the_sign_with_equal_denominators")
def frac_comp_1() -> dict | None:
    """Ten sam mianownik (poziom 1)."""
    d = random.randint(3, 12)
    n1 = random.randint(1, d + 5)
    n2 = n1
    while n2 == n1:
        n2 = random.randint(1, d + 5)

    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d)} \text{{ \_\_\_ }} {format_fraction_question(n2, d)}"

    c_str, wrong_sign = ("<", ">") if n1 < n2 else (">", "<")

    result = build_problem_dict(
        q_str,
        c_str,
        traps={"reverses_the_sign_with_equal_denominators": wrong_sign},
        parameters={"n1": n1, "n2": n2, "d": d},
    )
    if result:
        return result


@declares_traps("assumes_the_bigger_denominator_is_the_bigger_fraction")
def frac_comp_2() -> dict | None:
    """Ten sam licznik (poziom 2)."""
    n = random.randint(1, 9)
    d1 = random.randint(2, 12)
    d2 = d1
    while d2 == d1:
        d2 = random.randint(2, 12)

    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n, d1)} \text{{ \_\_\_ }} {format_fraction_question(n, d2)}"

    v1, v2 = n / d1, n / d2

    c_str, wrong_sign = ("<", ">") if v1 < v2 else (">", "<")

    result = build_problem_dict(
        q_str,
        c_str,
        traps={"assumes_the_bigger_denominator_is_the_bigger_fraction": wrong_sign},
        parameters={"n": n, "d1": d1, "d2": d2},
    )
    if result:
        return result


@declares_traps(
    "reads_equal_fractions_as_less_than",
    "reads_equal_fractions_as_greater_than",
)
def frac_comp_3() -> dict | None:
    """Różne ułamki (poziom 3)."""
    if random.random() < 0.25:
        d1 = random.randint(2, 6)
        n1 = random.randint(1, d1 * 2)
        multiplier = random.randint(2, 4)
        d2, n2 = d1 * multiplier, n1 * multiplier
        if random.choice([True, False]):
            n1, n2 = n2, n1
            d1, d2 = d2, d1
    else:
        d1, d2 = random.randint(2, 9), random.randint(2, 9)
        if d1 == d2:
            return None
        n1, n2 = random.randint(1, d1 * 2), random.randint(1, d2 * 2)
        if (n1 / d1) != (n2 / d2):
            return None

    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d1)} \text{{ \_\_\_ }} {format_fraction_question(n2, d2)}"

    # Both paths above guarantee the two fractions are equal — one builds an equivalent
    # pair outright, the other rejects any pair that is not. The Level is about seeing
    # equality through unlike denominators, so "<" and ">" are the only wrong answers.
    problem = build_problem_dict(
        q_str,
        "=",
        traps={
            "reads_equal_fractions_as_less_than": "<",
            "reads_equal_fractions_as_greater_than": ">",
        },
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )
    if problem:
        return problem
