import random
import math
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps("adds_instead_of_subtracting")
def frac_sub_1() -> dict | None:
    """Ten sam mianownik (poziom 1)."""
    d = random.randint(3, 9)
    n1 = random.randint(2, d - 1)
    n2 = random.randint(1, n1 - 1)

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d}}} - \frac{{{n2}}}{{{d}}}"

    c_str, _ = format_answers(n1 - n2, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={"adds_instead_of_subtracting": format_answers(n1 + n2, d)[0]},
        fillers=[
            format_answers(max(1, n1 - n2 - 1), d)[0],
            format_answers(n1 - n2 + 1, d)[0],
        ],
        parameters={"n1": n1, "n2": n2, "d": d},
    )
    if result:
        return result


@declares_traps("subtracts_numerators_without_expanding", "subtracts_the_denominators")
def frac_sub_2() -> dict | None:
    """Różne mianowniki - wstęp (poziom 2)."""
    d1 = random.randint(2, 5)
    factor = random.randint(2, 4)
    d2 = d1 * factor
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    if (n1 * factor) <= n2:
        return None
    if n1 == n2:
        return None

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} - \frac{{{n2}}}{{{d2}}}"

    c_str, _ = format_answers((n1 * factor) - n2, d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "subtracts_numerators_without_expanding": format_answers(abs(n1 - n2), d2)[
                0
            ],
            "subtracts_the_denominators": format_answers(abs(n1 - n2), abs(d1 - d2))[0],
        },
        fillers=[format_answers((n1 * factor) - n2 + 1, d2)[0]],
        parameters={
            "n1": n1,
            "d1": d1,
            "n2": n2,
            "d2": d2,
            "factor": factor,
            "operation": "-",
        },
    )
    if result:
        return result


@declares_traps(
    "subtracts_the_denominators",
    "uses_the_product_denominator_without_scaling_numerators",
    "adds_instead_of_subtracting",
)
def frac_sub_3() -> dict | None:
    """Różne mianowniki - zaawansowane (poziom 3)."""
    d1, d2 = random.randint(3, 7), random.randint(3, 7)
    if math.gcd(d1, d2) > 1 or d1 == d2:
        return None
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    if (n1 * d2) <= (n2 * d1):
        return None

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} - \frac{{{n2}}}{{{d2}}}"

    c_str, _ = format_answers((n1 * d2) - (n2 * d1), d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "subtracts_the_denominators": format_answers(abs(n1 - n2), abs(d1 - d2))[0],
            "uses_the_product_denominator_without_scaling_numerators": format_answers(
                abs(n1 - n2), d1 * d2
            )[0],
            "adds_instead_of_subtracting": format_answers(
                (n1 * d2) + (n2 * d1), d1 * d2
            )[0],
        },
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2, "operation": "-"},
    )
    if result:
        return result


@declares_traps("drops_the_denominator_after_subtracting", "drops_the_whole_parts")
def frac_sub_4() -> dict | None:
    """Zabieranie całości w liczbie mieszanej (poziom 4)."""
    whole1, whole2 = random.randint(2, 4), random.randint(1, 2)
    if whole1 <= whole2:
        return None
    d = random.randint(3, 7)
    n1, n2 = random.randint(2, d - 1), random.randint(1, d - 2)
    if n1 <= n2:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d, whole1)} - {format_fraction_question(n2, d, whole2)}"

    total = (whole1 * d + n1) - (whole2 * d + n2)
    c_str, _ = format_answers(total, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "drops_the_denominator_after_subtracting": format_answers(
                n1 - n2, 1, whole1 - whole2
            )[0],
            "drops_the_whole_parts": format_answers(n1 - n2, d)[0],
        },
        fillers=[format_answers(total + d, d)[0]],
        parameters={"whole1": whole1, "whole2": whole2, "n1": n1, "n2": n2, "d": d},
    )
    if result:
        return result


@declares_traps(
    "subtracts_the_fractions_in_reverse_to_avoid_borrowing",
    "borrows_ten_instead_of_the_denominator",
    "borrows_without_decrementing_the_whole",
)
def frac_sub_5() -> dict | None:
    """Różne mianowniki (poziom 5)."""
    whole1, whole2 = random.randint(2, 4), random.randint(1, 2)
    if whole1 <= whole2:
        return None
    d = random.randint(3, 7)
    n1, n2 = random.randint(1, d - 2), random.randint(2, d - 1)
    if n1 >= n2:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d, whole1)} - {format_fraction_question(n2, d, whole2)}"

    c_str, _ = format_answers((whole1 * d + n1) - (whole2 * d + n2), d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "subtracts_the_fractions_in_reverse_to_avoid_borrowing": format_answers(
                n2 - n1, d, whole1 - whole2
            )[0],
            "borrows_ten_instead_of_the_denominator": format_answers(
                (n1 + 10) - n2, d, (whole1 - 1) - whole2
            )[0],
            "borrows_without_decrementing_the_whole": format_answers(
                (d + n1) - n2, d, whole1 - whole2
            )[0],
        },
        parameters={"whole1": whole1, "whole2": whole2, "n1": n1, "n2": n2, "d": d},
    )
    if result:
        return result
