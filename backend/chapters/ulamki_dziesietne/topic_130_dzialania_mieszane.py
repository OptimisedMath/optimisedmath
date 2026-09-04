"""Ułamki Dziesiętne — Działania mieszane: generatory Problemów."""

import random
from fractions import Fraction

from backend.core.utils import (
    build_problem_dict,
    declares_traps,
    fmt_dec,
    format_answers,
)


@declares_traps(
    "adds_numerators_and_denominators",
    "adds_numerators_without_scaling",
)
def dec_mix_1() -> dict | None:
    """Zwykłe dziesiętne jako ułamek (poziom 1)."""
    d = random.choice([2, 4, 5, 10])
    n = random.randint(1, d - 1)

    d2 = random.choice([2, 4, 5, 10])
    n2 = random.randint(1, d2 - 1)
    dec_val = n2 / d2

    q_str = rf"\text{{Oblicz: }} \frac{{{n}}}{{{d}}} + {fmt_dec(dec_val)}"

    c_num = (n * d2) + (n2 * d)
    c_den = d * d2
    c_str, _ = format_answers(c_num, c_den)

    both_summed, _ = format_answers(n + n2, d + d2)
    numerators_summed, _ = format_answers(n + n2, d * d2)
    one_too_many, _ = format_answers(c_num + 1, c_den)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "adds_numerators_and_denominators": both_summed,
            "adds_numerators_without_scaling": numerators_summed,
        },
        fillers=[one_too_many],
        parameters={"n": n, "d": d, "n2": n2, "d2": d2},
    )
    if problem:
        return problem


@declares_traps(
    "adds_numerators_and_denominators",
    "rounds_to_a_decimal_instead_of_an_exact_fraction",
)
def dec_mix_2() -> dict | None:
    """Dodawanie, gdy ułamek nie ma skończonego rozwinięcia (poziom 2)."""
    # Denominators that create infinite decimals (1/3, 1/6) forcing fraction math
    d1 = random.choice([3, 6, 7, 9])
    n1 = random.randint(1, d1 - 1)
    if Fraction(n1, d1).denominator != d1:
        return None

    d2 = random.choice([2, 5, 10])
    n2 = random.randint(1, d2 - 1)
    dec_val = n2 / d2

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} + {fmt_dec(dec_val)}"

    c_num = (n1 * d2) + (n2 * d1)
    c_den = d1 * d2
    c_str, _ = format_answers(c_num, c_den)

    both_summed, _ = format_answers(n1 + n2, d1 + d2)
    one_too_many, _ = format_answers(c_num + 1, c_den)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "adds_numerators_and_denominators": both_summed,
            "rounds_to_a_decimal_instead_of_an_exact_fraction": fmt_dec(
                round(n1 / d1 + dec_val, 2)
            ),
        },
        fillers=[one_too_many],
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )
    if problem:
        return problem


@declares_traps(
    "adds_numerators_instead_of_multiplying",
    "multiplies_instead_of_dividing",
)
def dec_mix_3() -> dict | None:
    """Mnożenie i dzielenie różnych typów (poziom 3)."""
    d1 = random.choice([3, 4, 5, 6, 7])
    n1 = random.randint(1, d1 - 1)
    if Fraction(n1, d1).denominator != d1:
        return None

    d2 = random.choice([2, 4, 5])
    n2 = random.randint(1, d2 - 1)
    dec_val = n2 / d2

    if random.choice([True, False]):
        q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} \cdot {fmt_dec(dec_val)}"
        c_num = n1 * n2
        c_den = d1 * d2
        wrong_rule, _ = format_answers(n1 + n2, d1 * d2)
        traps = {"adds_numerators_instead_of_multiplying": wrong_rule}
    else:
        q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} : {fmt_dec(dec_val)}"
        c_num = n1 * d2
        c_den = d1 * n2
        wrong_rule, _ = format_answers(n1 * n2, d1 * d2)
        traps = {"multiplies_instead_of_dividing": wrong_rule}

    c_str, _ = format_answers(c_num, c_den)
    numerator_off_by_one, _ = format_answers(c_num + 1, c_den)
    denominator_off_by_one, _ = format_answers(c_num, c_den + 1)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps=traps,
        fillers=[numerator_off_by_one, denominator_off_by_one],
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )
    if problem:
        return problem
