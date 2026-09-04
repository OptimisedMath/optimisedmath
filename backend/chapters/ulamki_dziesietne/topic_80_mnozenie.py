"""Ułamki Dziesiętne — Mnożenie: generatory Problemów."""

import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps(
    "puts_two_places_too_many_in_the_product",
    "ignores_the_point_in_the_factor",
)
def dec_mult_1() -> dict | None:
    """Przez liczbę jednocyfrową (poziom 1)."""
    v1 = random.randint(2, 9) / 10
    v2 = random.randint(2, 9)

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {v2}"
    c_str = fmt_dec(round(v1 * v2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "puts_two_places_too_many_in_the_product": fmt_dec(round(v1 * v2 / 100, 3)),
            "ignores_the_point_in_the_factor": fmt_dec(round(v1 * 10 * v2, 2)),
        },
        fillers=[fmt_dec(round((v1 * 10 * v2 + 1) / 10, 2))],
        parameters={"v1": v1, "v2": v2},
    )
    if problem:
        return problem


@declares_traps(
    "puts_one_place_too_few_in_the_product",
    "ignores_both_points_in_the_factors",
    "puts_one_place_too_many_in_the_product",
)
def dec_mult_2() -> dict | None:
    """Ułamek przez ułamek (poziom 2)."""
    v1 = random.randint(2, 9) / 10
    v2 = random.randint(2, 9) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 * v2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "puts_one_place_too_few_in_the_product": fmt_dec(round(v1 * v2 * 10, 2)),
            "ignores_both_points_in_the_factors": fmt_dec(round(v1 * 10 * v2 * 10, 2)),
            "puts_one_place_too_many_in_the_product": fmt_dec(round(v1 * v2 / 10, 3)),
        },
        parameters={"v1": v1, "v2": v2},
    )
    if problem:
        return problem


@declares_traps(
    "puts_one_place_too_few_in_the_product",
    "puts_one_place_too_many_in_the_product",
)
def dec_mult_3() -> dict | None:
    """Połówki przez części dziesiąte (poziom 3)."""
    v1 = random.choice([1.5, 2.5, 3.5, 4.5])
    v2 = random.choice([0.2, 0.4, 0.6, 0.8])

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
    val = round(v1 * v2, 2)
    c_str = fmt_dec(val)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "puts_one_place_too_few_in_the_product": fmt_dec(round(val * 10, 2)),
            "puts_one_place_too_many_in_the_product": fmt_dec(round(val / 10, 2)),
        },
        fillers=[fmt_dec(round((v1 * 10 * v2 * 10) + 1, 2))],
        parameters={"v1": v1, "v2": v2},
    )
    if problem:
        return problem
