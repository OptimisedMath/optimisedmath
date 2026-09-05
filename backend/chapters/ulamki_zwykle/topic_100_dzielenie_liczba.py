"""Ułamki Zwykłe — Dzielenie przez liczbę: generatory Problemów."""

import math
import random
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps(
    "divides_the_numerator_and_multiplies_the_denominator",
    "multiplies_the_numerator_instead_of_dividing",
)
def frac_div_num_1() -> dict | None:
    """Dzielenie licznika (poziom 1)."""
    # The Level is the k | n case, so n is built from k rather than drawn and
    # rejected — rejection sampling over the old ranges left 19 distinct Problems.
    k = random.randint(2, 6)
    q = random.randint(1, 6)
    n = k * q
    if n >= 15:
        return None
    d = random.randint(n + 1, 15)
    # An already-reducible question invites cancelling before dividing, which is a
    # different Topic's skill and a different Misconception.
    if math.gcd(n, d) != 1:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} : {k}"

    # Dividing the numerator and multiplying the denominator are the same operation
    # here — n/(d*k) is (n/k)/d — so the Level affords the easier method rather than
    # grading it. The Traps are what carry the contrast.
    c_str, _ = format_answers(n, d * k)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "divides_the_numerator_and_multiplies_the_denominator": format_answers(
                n, d * k * k
            )[0],
            "multiplies_the_numerator_instead_of_dividing": format_answers(n * k, d)[0],
        },
        fillers=[format_answers(n + k, d * k)[0]],
        parameters={"n": n, "d": d, "k": k},
    )
    if problem:
        return problem


@declares_traps(
    "adds_to_the_denominator_instead_of_multiplying",
    "multiplies_the_numerator_instead_of_dividing",
)
def frac_div_num_2() -> dict | None:
    """Gdy licznik się nie dzieli (poziom 2)."""
    k = random.randint(2, 6)
    n = random.randint(1, 14)
    if n % k == 0:
        return None
    d = random.randint(n + 1, 15)
    if math.gcd(n, d) != 1:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} : {k}"

    c_str, _ = format_answers(n, d * k)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "adds_to_the_denominator_instead_of_multiplying": format_answers(n, d + k)[
                0
            ],
            "multiplies_the_numerator_instead_of_dividing": format_answers(n * k, d)[0],
        },
        fillers=[format_answers(n + 1, d * k)[0]],
        parameters={"n": n, "d": d, "k": k},
    )
    if problem:
        return problem


@declares_traps(
    "divides_only_the_whole_part",
    "multiplies_the_numerator_instead_of_dividing",
)
def frac_div_num_3() -> dict | None:
    """Dzielenie liczby mieszanej (poziom 3)."""
    w = random.randint(2, 4)
    d = random.randint(2, 5)
    n = random.randint(1, d - 1)
    k = random.randint(2, 3)
    if w % k != 0:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d, w)} : {k}"

    correct_num = (w * d) + n
    c_str, _ = format_answers(correct_num, d * k)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "divides_only_the_whole_part": format_answers(n, d, w // k)[0],
            "multiplies_the_numerator_instead_of_dividing": format_answers(
                correct_num * k, d
            )[0],
        },
        fillers=[format_answers(correct_num + 1, d * k)[0]],
        parameters={
            "whole1": w,
            "n1": n,
            "d1": d,
            "whole2": 0,
            "n2": k,
            "d2": 1,
            "operation": ":",
        },
    )
    if result:
        return result
