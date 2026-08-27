import random
from backend.core.utils import (
    format_answers,
    format_fraction_question,
    build_problem_dict,
    declares_traps,
)


@declares_traps(
    "multiplies_the_numerator_instead_of_dividing",
    "leaves_the_fraction_unchanged",
)
def frac_div_num_1() -> dict | None:
    """Dzielenie licznika (poziom 1)."""
    d = random.randint(2, 7)
    n = random.randint(1, d - 1)
    k = random.randint(2, 5)

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} : {k}"

    c_str, _ = format_answers(n, d * k)

    # Dividing the denominator by k is not a distinct wrong rule here: n/(d/k) is the
    # same value as n*k/d, so the two options always collided and the branch that
    # offered it could never build a Problem.
    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_the_numerator_instead_of_dividing": format_answers(n * k, d)[0],
            "leaves_the_fraction_unchanged": format_answers(n, d)[0],
        },
        fillers=[format_answers(n + k, d * k)[0]],
    )
    if problem:
        return problem


@declares_traps("multiplies_without_inverting", "inverts_the_wrong_way_round")
def frac_div_num_2() -> dict | None:
    """Gdy licznik się nie dzieli (poziom 2)."""
    k = random.randint(2, 5)
    d = random.randint(2, 7)
    n = random.randint(1, d - 1)

    q_str = rf"\text{{Oblicz: }} {k} : {format_fraction_question(n, d)}"

    c_str, _ = format_answers(k * d, n)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_without_inverting": format_answers(k * n, d)[0],
            "inverts_the_wrong_way_round": format_answers(n, k * d)[0],
        },
        fillers=[format_answers((k * d) + 1, n)[0]],
    )
    if result:
        return result


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
    )
    if result:
        return result
