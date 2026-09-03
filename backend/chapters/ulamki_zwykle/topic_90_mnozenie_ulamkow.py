import random
import math
from backend.core.utils import (
    format_answers,
    format_fraction_answer,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps(
    "multiplies_crosswise",
    "keeps_the_first_denominator",
    "adds_instead_of_multiplying",
)
def frac_mult_1() -> dict | None:
    """Proste mnożenie (poziom 1)."""
    d1, d2 = random.randint(3, 7), random.randint(3, 7)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    if math.gcd(n1, d2) > 1 or math.gcd(n2, d1) > 1:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2)}"

    c_str, _ = format_answers(n1 * n2, d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_crosswise": format_answers(n1 * d2, d1 * n2)[0],
            "keeps_the_first_denominator": format_answers(n1 * n2, d1)[0],
            "adds_instead_of_multiplying": format_answers(n1 + n2, d1 + d2)[0],
        },
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )
    if result:
        return result


@declares_traps("stops_before_lowest_terms", "cancels_the_numerators_away")
def frac_mult_2() -> dict | None:
    """Skracanie na krzyż (poziom 2)."""
    n1, d2 = random.randint(2, 8), random.randint(2, 8)
    while math.gcd(n1, d2) == 1:
        n1, d2 = random.randint(2, 8), random.randint(2, 8)
    d1, n2 = random.randint(3, 9), random.randint(1, 7)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2)}"

    c_str, _ = format_answers(n1 * n2, d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "stops_before_lowest_terms": format_fraction_answer(
                n1 * n2, d1 * d2, simplify=False
            ),
            "cancels_the_numerators_away": format_answers(1, d1 * d2)[0],
        },
        fillers=[format_answers(n1 * n2, d1 * d2 + 1)[0]],
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )
    if result:
        return result


@declares_traps(
    "multiplies_without_converting_the_mixed_number",
    "adds_instead_of_multiplying",
)
def frac_mult_3() -> dict | None:
    """Mnożenie liczb mieszanych (poziom 3)."""
    w = random.randint(1, 3)
    d1, d2 = random.randint(2, 5), random.randint(2, 5)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2, w)}"

    total = n1 * ((w * d2) + n2)
    c_str, _ = format_answers(total, d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_without_converting_the_mixed_number": format_answers(
                n1 * n2, d1 * d2, w
            )[0],
            "adds_instead_of_multiplying": format_answers(
                n1 + ((w * d2) + n2), d1 + d2
            )[0],
        },
        fillers=[format_answers(total + 1, d1 * d2)[0]],
        parameters={
            "whole1": 0,
            "n1": n1,
            "d1": d1,
            "whole2": w,
            "n2": n2,
            "d2": d2,
            "operation": "*",
        },
    )
    if result:
        return result


@declares_traps(
    "multiplies_wholes_and_fractions_separately",
    "multiplies_fractions_and_adds_the_wholes",
)
def frac_mult_4() -> dict | None:
    """Wielkie skracanie (poziom 4)."""
    whole1, whole2 = random.randint(1, 2), random.randint(1, 2)
    d1, d2 = random.randint(2, 4), random.randint(2, 4)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1, whole1)} \cdot {format_fraction_question(n2, d2, whole2)}"

    num1, num2 = (whole1 * d1) + n1, (whole2 * d2) + n2
    c_str, _ = format_answers(num1 * num2, d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_wholes_and_fractions_separately": format_answers(
                n1 * n2, d1 * d2, whole1 * whole2
            )[0],
            "multiplies_fractions_and_adds_the_wholes": format_answers(
                n1 * n2, d1 * d2, whole1 + whole2
            )[0],
        },
        fillers=[format_answers(num1 * num2 + 1, d1 * d2)[0]],
        parameters={
            "whole1": whole1,
            "whole2": whole2,
            "n1": n1,
            "d1": d1,
            "n2": n2,
            "d2": d2,
            "operation": "*",
        },
    )
    if result:
        return result
