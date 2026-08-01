import random
import math
from backend.core.utils import format_fraction_answer, format_fraction_question, build_problem_dict


def frac_exp_1() -> dict | None:
    """Rozszerzanie przez liczbę (poziom 1)."""
    d = random.randint(2, 9)
    n = random.randint(1, d * 2)
    if n == d:
        return None
    factor = random.randint(2, 6)

    q_str = rf"\text{{Rozszerz ułamek }} {format_fraction_question(n, d)} \text{{ przez }} {factor}."

    c_str = format_fraction_answer(n * factor, d * factor, simplify=False)
    t1 = format_fraction_answer(n * factor, d, simplify=False)
    t2 = format_fraction_answer(n, d * factor, simplify=False)
    t3 = format_fraction_answer(n + factor, d + factor, simplify=False)

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, t3=t3, grading_policy="exact_match_only"
    )
    if result:
        return result


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
    t1 = format_fraction_answer(n, target_d, simplify=False)

    wrong_factor = factor + random.choice([-1, 1])
    if wrong_factor < 1:
        wrong_factor = factor + 2
    t2 = format_fraction_answer(n * wrong_factor, target_d, simplify=False)

    w1 = format_fraction_answer(
        n * factor + random.choice([-1, 1]), target_d, simplify=False
    )

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, w1=w1, grading_policy="exact_match_only"
    )
    if result:
        return result


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
    t1 = format_fraction_answer(n, start_d, simplify=False)
    t2 = format_fraction_answer(start_n, d, simplify=False)
    t3 = format_fraction_answer(
        max(1, start_n - factor), max(2, start_d - factor), simplify=False
    )

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, t3=t3, grading_policy="exact_match_only"
    )
    if result:
        return result


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
    t1 = format_fraction_answer(n * factor2, d * factor2, simplify=False)
    t2 = format_fraction_answer(n, d * factor2, simplify=False)
    t3 = format_fraction_answer(n * factor2, d, simplify=False)

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, t3=t3, grading_policy="exact_match_only"
    )
    if result:
        return result
