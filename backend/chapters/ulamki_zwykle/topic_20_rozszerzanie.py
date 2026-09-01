import random
import math
from backend.core.utils import (
    format_fraction_answer,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps(
    "scales_only_the_numerator",
    "scales_only_the_denominator",
    "adds_the_factor_instead_of_multiplying",
)
def frac_exp_1() -> dict | None:
    """Rozszerzanie przez liczbę (poziom 1)."""
    d = random.randint(2, 9)
    n = random.randint(1, d * 2)
    if n == d:
        return None
    factor = random.randint(2, 6)

    q_str = rf"\text{{Rozszerz ułamek }} {format_fraction_question(n, d)} \text{{ przez }} {factor}."

    c_str = format_fraction_answer(n * factor, d * factor, simplify=False)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "scales_only_the_numerator": format_fraction_answer(
                n * factor, d, simplify=False
            ),
            "scales_only_the_denominator": format_fraction_answer(
                n, d * factor, simplify=False
            ),
            "adds_the_factor_instead_of_multiplying": format_fraction_answer(
                n + factor, d + factor, simplify=False
            ),
        },
        grading_policy="exact_match_only",
        parameters={"n": n, "d": d, "factor": factor},
    )
    if result:
        return result


@declares_traps(
    "changes_the_denominator_leaving_the_numerator",
    "scales_the_numerator_by_the_wrong_factor",
    "copies_the_numerator_off_by_one",
)
def frac_exp_2() -> dict | None:
    """Rozszerzanie do mianownika (poziom 2)."""
    d = random.randint(2, 9)
    n = random.randint(1, d * 2)
    if n == d:
        return None
    factor = random.randint(2, 6)
    target_d = d * factor

    q_str = rf"\text{{Rozszerz ułamek }} {format_fraction_question(n, d)} \text{{ tak, aby w mianowniku było }} {target_d}."

    c_str = format_fraction_answer(n * factor, target_d, simplify=False)

    wrong_factor = factor + random.choice([-1, 1])
    if wrong_factor < 1:
        wrong_factor = factor + 2

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "changes_the_denominator_leaving_the_numerator": format_fraction_answer(
                n, target_d, simplify=False
            ),
            "scales_the_numerator_by_the_wrong_factor": format_fraction_answer(
                n * wrong_factor, target_d, simplify=False
            ),
            "copies_the_numerator_off_by_one": format_fraction_answer(
                n * factor + random.choice([-1, 1]), target_d, simplify=False
            ),
        },
        grading_policy="exact_match_only",
        parameters={"n": n, "d": d, "factor": factor},
    )
    if result:
        return result


@declares_traps(
    "divides_only_the_numerator",
    "divides_only_the_denominator",
    "subtracts_the_factor_instead_of_dividing",
)
def frac_exp_3() -> dict | None:
    """Skracanie przez liczbę (poziom 3)."""
    d = random.randint(2, 9)
    n = random.randint(1, d * 2)
    if n == d:
        return None
    factor = random.randint(2, 6)

    start_n = n * factor
    start_d = d * factor

    q_str = rf"\text{{Skróć ułamek }} {format_fraction_question(start_n, start_d)} \text{{ przez }} {factor}."

    c_str = format_fraction_answer(n, d, simplify=False)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "divides_only_the_numerator": format_fraction_answer(
                n, start_d, simplify=False
            ),
            "divides_only_the_denominator": format_fraction_answer(
                start_n, d, simplify=False
            ),
            "subtracts_the_factor_instead_of_dividing": format_fraction_answer(
                max(1, start_n - factor), max(2, start_d - factor), simplify=False
            ),
        },
        grading_policy="exact_match_only",
        parameters={"n": n, "d": d, "factor": factor},
    )
    if result:
        return result


@declares_traps(
    "stops_before_lowest_terms",
    "reduces_the_numerator_further_than_the_denominator",
    "reduces_the_denominator_further_than_the_numerator",
)
def frac_exp_4() -> dict | None:
    """Postać nieskracalna (poziom 4)."""
    d = random.randint(2, 9)
    n = random.randint(1, d * 2)
    if n == d or math.gcd(n, d) > 1:
        return None

    factor1 = random.randint(2, 4)
    factor2 = random.randint(2, 4)
    total_factor = factor1 * factor2

    start_n = n * total_factor
    start_d = d * total_factor

    q_str = rf"\text{{Skróć ułamek }} {format_fraction_question(start_n, start_d)} \text{{ do postaci nieskracalnej.}}"

    c_str = format_fraction_answer(n, d, simplify=True)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "stops_before_lowest_terms": format_fraction_answer(
                n * factor2, d * factor2, simplify=False
            ),
            "reduces_the_numerator_further_than_the_denominator": format_fraction_answer(
                n, d * factor2, simplify=False
            ),
            "reduces_the_denominator_further_than_the_numerator": format_fraction_answer(
                n * factor2, d, simplify=False
            ),
        },
        grading_policy="exact_match_only",
        parameters={"n": n, "d": d, "factor1": factor1, "factor2": factor2},
    )
    if result:
        return result
