import random
import math
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps("adds_the_denominators")
def frac_add_1() -> dict | None:
    """Ten sam mianownik (poziom 1)."""
    d = random.randint(3, 9)
    n1 = random.randint(1, d - 1)
    n2 = random.randint(1, d - 1)

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d}}} + \frac{{{n2}}}{{{d}}}"

    c_str, _ = format_answers(n1 + n2, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={"adds_the_denominators": format_answers(n1 + n2, d + d)[0]},
        fillers=[
            format_answers(n1 + n2 + 1, d)[0],
            format_answers(abs(n1 + n2 - 1), d)[0],
        ],
    )
    if result:
        return result


@declares_traps("adds_numerators_without_expanding", "adds_the_denominators")
def frac_add_2() -> dict | None:
    """Skracanie wyniku (poziom 2)."""
    d1 = random.randint(2, 5)
    factor = random.randint(2, 4)
    d2 = d1 * factor
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} + \frac{{{n2}}}{{{d2}}}"

    c_str, _ = format_answers((n1 * factor) + n2, d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "adds_numerators_without_expanding": format_answers(n1 + n2, d2)[0],
            "adds_the_denominators": format_answers(n1 + n2, d1 + d2)[0],
        },
        fillers=[format_answers((n1 * factor) + n2 + 1, d2)[0]],
    )
    if result:
        return result


@declares_traps(
    "adds_the_denominators",
    "uses_the_product_denominator_without_scaling_numerators",
    "multiplies_the_scaled_numerators_instead_of_adding",
)
def frac_add_3() -> dict | None:
    """Liczby mieszane z wyłączaniem (poziom 3)."""
    d1, d2 = random.randint(3, 7), random.randint(3, 7)
    if math.gcd(d1, d2) > 1 or d1 == d2:
        return None
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} + \frac{{{n2}}}{{{d2}}}"

    c_str, _ = format_answers((n1 * d2) + (n2 * d1), d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "adds_the_denominators": format_answers(n1 + n2, d1 + d2)[0],
            "uses_the_product_denominator_without_scaling_numerators": format_answers(
                n1 + n2, d1 * d2
            )[0],
            "multiplies_the_scaled_numerators_instead_of_adding": format_answers(
                n1 * d2 * n2 * d1, d1 * d2
            )[0],
        },
    )
    if result:
        return result


@declares_traps("adds_the_denominators")
def frac_add_4() -> dict | None:
    """Różne mianowniki - wstęp (poziom 4)."""
    whole1, whole2 = random.randint(1, 3), random.randint(1, 3)
    d = random.randint(3, 7)
    n1, n2 = random.randint(1, d - 1), random.randint(1, d - 1)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d, whole1)} + {format_fraction_question(n2, d, whole2)}"

    total = (whole1 * d + n1) + (whole2 * d + n2)
    c_str, _ = format_answers(total, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "adds_the_denominators": format_answers(n1 + n2, d + d, whole1 + whole2)[0]
        },
        fillers=[
            format_answers(total + d, d)[0],
            format_answers(total + 1, d)[0],
        ],
    )
    if result:
        return result


@declares_traps(
    "uses_the_product_denominator_without_scaling_numerators",
    "adds_the_denominators",
)
def frac_add_5() -> dict | None:
    """Różne mianowniki - zaawansowane (poziom 5)."""
    whole1, whole2 = random.randint(1, 2), random.randint(1, 2)
    d1, d2 = random.randint(2, 5), random.randint(2, 5)
    if math.gcd(d1, d2) > 1 or d1 == d2:
        return None
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1, whole1)} + {format_fraction_question(n2, d2, whole2)}"

    num1, num2 = (whole1 * d1) + n1, (whole2 * d2) + n2
    total = (num1 * d2) + (num2 * d1)
    c_str, _ = format_answers(total, d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "uses_the_product_denominator_without_scaling_numerators": format_answers(
                n1 + n2, d1 * d2, whole1 + whole2
            )[0],
            "adds_the_denominators": format_answers(n1 + n2, d1 + d2, whole1 + whole2)[
                0
            ],
        },
        fillers=[format_answers(total + 1, d1 * d2)[0]],
    )
    if result:
        return result
