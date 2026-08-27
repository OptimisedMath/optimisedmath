import random
from backend.core.utils import (
    format_fraction_question,
    build_problem_dict,
    declares_traps,
    format_answers,
)


@declares_traps(
    "multiplies_the_numerator_instead_of_adding",
    "adds_the_whole_without_multiplying_by_the_denominator",
    "also_multiplies_the_denominator_by_the_whole",
)
def frac_imp_1() -> dict | None:
    """Zamiana na ułamek niewłaściwy (poziom 1)."""
    w = random.randint(1, 5)
    d = random.randint(2, 9)
    n = random.randint(1, d - 1)

    q_str = (
        rf"\text{{Zamień na ułamek niewłaściwy: }} {format_fraction_question(n, d, w)}"
    )

    _, c_str = format_answers((w * d) + n, d)

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "multiplies_the_numerator_instead_of_adding": format_answers(
                (w * d) * n, d
            )[1],
            "adds_the_whole_without_multiplying_by_the_denominator": format_answers(
                w + n, d
            )[1],
            "also_multiplies_the_denominator_by_the_whole": format_answers(
                (w * d) + n, d * w
            )[1],
        },
    )
    if result:
        return result


@declares_traps(
    "gives_only_the_whole_part",
    "swaps_the_remainder_and_the_denominator",
)
def frac_imp_2() -> dict | None:
    """Wyłączanie całości (poziom 2)."""
    w = random.randint(1, 5)
    d = random.randint(2, 9)
    n = random.randint(1, d - 1)

    start_n = (w * d) + n
    q_str = rf"\text{{Wyłącz całości z ułamka: }} \frac{{{start_n}}}{{{d}}}"

    c_str, _ = format_answers(n, d, w)

    w_wrong = w + random.choice([-1, 1])
    if w_wrong < 1:
        w_wrong = w + 2

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "gives_only_the_whole_part": format_answers(w, 1)[0],
            "swaps_the_remainder_and_the_denominator": format_answers(d, n, w)[0],
        },
        fillers=[format_answers(n, d, w_wrong)[0]],
    )
    if result:
        return result
