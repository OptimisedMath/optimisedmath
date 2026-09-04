"""Ułamki Dziesiętne — Dzielenie: generatory Problemów."""

import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps(
    "ignores_the_point_in_the_dividend",
    "puts_one_place_too_many_in_the_quotient",
)
def dec_div_1() -> dict | None:
    """Przez liczbę całkowitą (bez reszty) (poziom 1)."""
    c = random.randint(2, 9)
    d = random.randint(2, 5)
    v1 = (c * d) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {d}"
    c_str = fmt_dec(round(v1 / d, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "ignores_the_point_in_the_dividend": fmt_dec(round((v1 * 10) / d, 2)),
            "puts_one_place_too_many_in_the_quotient": fmt_dec(round(v1 / (d * 10), 3)),
        },
        fillers=[fmt_dec(round((v1 / d) + 0.1, 2))],
        parameters={"c": c, "d": d},
    )
    if problem:
        return problem


@declares_traps(
    "puts_one_place_too_many_in_the_quotient",
    "puts_one_place_too_few_in_the_quotient",
    "sums_the_decimal_places_as_in_multiplication",
)
def dec_div_2() -> dict | None:
    """Przez części dziesiąte (poziom 3)."""
    c = random.randint(2, 9)
    d = random.randint(2, 5)
    v1 = (c * d) / 100
    v2 = d / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 / v2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "puts_one_place_too_many_in_the_quotient": fmt_dec(
                round(v1 / (v2 * 10), 3)
            ),
            "puts_one_place_too_few_in_the_quotient": fmt_dec(round((v1 / v2) * 10, 2)),
            "sums_the_decimal_places_as_in_multiplication": fmt_dec(
                round((v1 / v2) / 100, 3)
            ),
        },
        parameters={"c": c, "d": d},
    )
    if problem:
        return problem


@declares_traps(
    "shifts_only_the_dividend",
    "shifts_the_dividend_two_places_the_wrong_way",
)
def dec_div_3() -> dict | None:
    """Przez części setne (poziom 4)."""
    c = random.randint(2, 9)
    d = random.randint(2, 5)
    v1 = (c * d) / 10
    v2 = d / 100

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 / v2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "shifts_only_the_dividend": fmt_dec(round((v1 / 10) / v2, 2)),
            "shifts_the_dividend_two_places_the_wrong_way": fmt_dec(
                round((v1 / 100) / v2, 3)
            ),
        },
        fillers=[fmt_dec(round((v1 / v2) + 1, 2))],
        parameters={"c": c, "d": d},
    )
    if problem:
        return problem


@declares_traps(
    "skips_the_decimal_shift",
    "shifts_the_divisor_instead_of_appending_a_zero",
)
def dec_div_4() -> dict | None:
    """Przez liczbę całkowitą (z dopisaniem zera) (poziom 2)."""
    # Generate divisions like 0.3 : 2 = 0.15 where student must append a 0
    v1 = random.choice([1, 3, 5, 7, 9]) / 10
    d = random.choice([2, 4, 5])
    if (v1 * 10) % d == 0:
        return None  # Skip if no phantom zero is needed

    q_str = rf"\text{{Oblicz (dopisz zero na końcu dzielnej): }} {fmt_dec(v1)} : {d}"
    c_str = fmt_dec(round(v1 / d, 3))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "skips_the_decimal_shift": fmt_dec(round((v1 * 10) / d, 3)),
            "shifts_the_divisor_instead_of_appending_a_zero": fmt_dec(
                round(v1 / (d * 10), 4)
            ),
        },
        fillers=[fmt_dec(round((v1 / d) + 0.1, 3))],
        parameters={"v1": v1, "d": d},
    )
    if problem:
        return problem
