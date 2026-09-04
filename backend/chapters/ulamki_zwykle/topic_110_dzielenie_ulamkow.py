"""Ułamki Zwykłe — Dzielenie ułamków: generatory Problemów."""

import random
import math
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps("multiplies_without_inverting", "inverts_the_whole_answer")
def frac_div_frac_1() -> dict | None:
    """Proste odwracanie (poziom 1)."""
    d1, d2 = random.randint(3, 7), random.randint(3, 7)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} : {format_fraction_question(n2, d2)}"

    c_str, _ = format_answers(n1 * d2, d1 * n2)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_without_inverting": format_answers(n1 * n2, d1 * d2)[0],
            "inverts_the_whole_answer": format_answers(d1 * n2, n1 * d2)[0],
        },
        fillers=[format_answers((n1 * d2) + 1, d1 * n2)[0]],
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )
    if problem:
        return problem


@declares_traps("cancels_before_inverting", "multiplies_without_inverting")
def frac_div_frac_2() -> dict | None:
    """Odwracanie i skracanie (poziom 2)."""
    n1, n2 = random.randint(2, 8), random.randint(2, 8)
    while math.gcd(n1, n2) == 1:
        n1, n2 = random.randint(2, 8), random.randint(2, 8)
    d1, d2 = random.randint(3, 9), random.randint(3, 9)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} : {format_fraction_question(n2, d2)}"
    c_str, _ = format_answers(n1 * d2, d1 * n2)

    g = math.gcd(n1, n2)
    trap_n1 = n1 // g

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "cancels_before_inverting": format_answers(trap_n1 * d2, d1 * n2)[0],
            "multiplies_without_inverting": format_answers(n1 * n2, d1 * d2)[0],
        },
        fillers=[format_answers((n1 * d2) + 1, d1 * n2)[0]],
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )

    if problem:
        return problem


@declares_traps("inverts_only_the_fraction_part", "multiplies_without_inverting")
def frac_div_frac_3() -> dict | None:
    """Dzielenie z liczbami mieszanymi (poziom 3)."""
    whole1, whole2 = random.randint(1, 2), random.randint(1, 2)
    d1, d2 = random.randint(2, 4), random.randint(2, 4)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1, whole1)} : {format_fraction_question(n2, d2, whole2)}"

    num1, num2 = (whole1 * d1) + n1, (whole2 * d2) + n2
    c_str, _ = format_answers(num1 * d2, d1 * num2)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "inverts_only_the_fraction_part": format_answers(num1 * n2, d1 * d2)[0],
            "multiplies_without_inverting": format_answers(num1 * num2, d1 * d2)[0],
        },
        fillers=[format_answers(num1 * d2 + 1, d1 * num2)[0]],
        parameters={
            "whole1": whole1,
            "whole2": whole2,
            "n1": n1,
            "d1": d1,
            "n2": n2,
            "d2": d2,
            "operation": ":",
        },
    )
    if problem:
        return problem
