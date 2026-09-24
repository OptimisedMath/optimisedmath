"""Ułamki Zwykłe — Mnożenie przez liczbę: generatory Problemów."""

import random
import math
from backend.core.utils import (
    format_answers,
    format_fraction_answer,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


def _multiplies_the_denominator_too(num: int, den: int, k: int) -> str:
    """The option for a Student who multiplied both parts of the fraction by `k`.

    Left un-simplified on purpose: simplifying cancels the `k` straight back out,
    landing on a fraction the question already printed, so the Student who made
    this mistake would not find their own answer among the options (#363).
    """
    return format_fraction_answer(num * k, den * k, simplify=False)


@declares_traps("multiplies_the_denominator_too", "multiplies_only_the_denominator")
def frac_mult_num_1() -> dict | None:
    """Mnożenie ułamka przez liczbę (poziom 1)."""
    d = random.randint(3, 9)
    n = random.randint(1, d - 1)
    k = random.randint(2, 5)
    if math.gcd(d, k) > 1:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \cdot {k}"

    c_str, _ = format_answers(n * k, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_the_denominator_too": _multiplies_the_denominator_too(n, d, k),
            "multiplies_only_the_denominator": format_answers(n, d * k)[0],
        },
        parameters={"n": n, "d": d, "k": k},
    )
    if result:
        return result


@declares_traps(
    "cancels_the_numerator_away",
    "multiplies_the_denominator_too",
)
def frac_mult_num_2() -> dict | None:
    """Skracanie na krzyż z liczbą (poziom 2)."""
    k = random.randint(2, 6)
    factor = random.randint(2, 4)
    d = k * factor
    n = random.randint(1, d - 1)
    if math.gcd(n, d) > 1:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \cdot {k}"

    c_str, _ = format_answers(n * k, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "cancels_the_numerator_away": format_answers(1, factor)[0],
            "multiplies_the_denominator_too": _multiplies_the_denominator_too(n, d, k),
        },
        parameters={"n": n, "d": d, "k": k, "factor": factor},
    )
    if result:
        return result


@declares_traps("multiplies_only_the_fraction_part", "multiplies_the_denominator_too")
def frac_mult_num_3() -> dict | None:
    """Mnożenie liczby mieszanej (poziom 3)."""
    w = random.randint(1, 3)
    d = random.randint(2, 5)
    n = random.randint(1, d - 1)
    k = random.randint(2, 4)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d, w)} \cdot {k}"

    total = ((w * d) + n) * k
    c_str, _ = format_answers(total, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_only_the_fraction_part": format_answers(n * k, d, w)[0],
            "multiplies_the_denominator_too": _multiplies_the_denominator_too(
                (w * d) + n, d, k
            ),
        },
        parameters={
            "whole1": w,
            "n1": n,
            "d1": d,
            "whole2": 0,
            "n2": k,
            "d2": 1,
            "operation": "*",
        },
    )
    if result:
        return result
