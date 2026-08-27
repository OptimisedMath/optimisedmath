import random
import math
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


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
            "multiplies_the_denominator_too": format_answers(n * k, d * k)[0],
            "multiplies_only_the_denominator": format_answers(n, d * k)[0],
        },
        fillers=[format_answers(n * k + 1, d)[0]],
    )
    if result:
        return result


@declares_traps("stops_before_lowest_terms", "cancels_the_numerator_away")
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
            "stops_before_lowest_terms": rf"\frac{{{n * k}}}{{{d}}}",
            "cancels_the_numerator_away": format_answers(1, factor)[0],
        },
        fillers=[format_answers(n * k + 1, d)[0]],
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
            "multiplies_the_denominator_too": format_answers(total, d * k)[0],
        },
        fillers=[format_answers(total + 1, d)[0]],
    )
    if result:
        return result
