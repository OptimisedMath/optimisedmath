"""Ułamki Dziesiętne — Dodawanie: generatory Problemów."""

import random
from decimal import Decimal

from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


def _as_decimal(value: int | float) -> Decimal:
    """Exact Decimal for a tenths-built operand, via `str` so 1.3 stays 1.3."""
    return Decimal(str(value))


@declares_traps("adds_digits_across_the_point")
def dec_add_1() -> dict | None:
    """Bez przekroczenia rzędu (poziom 1)."""
    whole1, whole2 = random.randint(1, 4), random.randint(1, 4)
    d1, d2 = random.randint(1, 8), random.randint(1, 8)
    if d1 + d2 >= 10:
        return None

    v1 = whole1 + (d1 / 10)
    v2 = whole2 + (d2 / 10)
    dv1, dv2 = _as_decimal(v1), _as_decimal(v2)

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)}"
    c_str = fmt_dec(dv1 + dv2)

    trap_value = _as_decimal(whole1 + d2) + _as_decimal((whole2 + d1) / 10)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={"adds_digits_across_the_point": fmt_dec(trap_value)},
        fillers=[
            fmt_dec(dv1 + dv2 + Decimal("0.1")),
            fmt_dec(dv1 + dv2 + 1),
        ],
        parameters={"v1": v1, "v2": v2, "operation": "+"},
    )
    if problem:
        return problem


@declares_traps(
    "forgets_the_carry",
    "concatenates_the_two_sums",
    "applies_the_multiplication_point_rule",
)
def dec_add_2() -> dict | None:
    """Z przekroczeniem rzędu (poziom 2)."""
    d = random.choice([1, 2])

    int_a = random.randint(0, 20)
    int_b = random.randint(0, 20)

    if d == 1:
        dec_a = random.randint(1, 9)
        dec_b = random.randint(10 - dec_a, 9)
        a = round(int_a + dec_a / 10, 1)
        b = round(int_b + dec_b / 10, 1)
        correct_answer = round(a + b, 1)
    else:  # d == 2
        dec_a = random.randint(11, 99)
        dec_b = random.randint(100 - dec_a, 99)
        a = round(int_a + dec_a / 100, 2)
        b = round(int_b + dec_b / 100, 2)
        correct_answer = round(a + b, 2)

    q_str = rf"\text{{Oblicz: }} {fmt_dec(a)} + {fmt_dec(b)}"
    c_str = fmt_dec(correct_answer)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "forgets_the_carry": fmt_dec(round(correct_answer - 1.0, d)),
            "concatenates_the_two_sums": f"{int_a + int_b},{dec_a + dec_b}",
            "applies_the_multiplication_point_rule": fmt_dec(
                round(correct_answer * (10**-d), d * 2)
            ),
        },
        parameters={
            "d": d,
            "int_a": int_a,
            "int_b": int_b,
            "dec_a": dec_a,
            "dec_b": dec_b,
        },
    )
    if problem:
        return problem


@declares_traps(
    "aligns_the_last_digits_instead_of_the_point",
    "shifts_the_point_when_adding",
    "drops_the_hundredths_digit",
)
def dec_add_3() -> dict | None:
    """Różna liczba miejsc (np. 1.2 + 0.05) (poziom 3)."""
    v1 = random.randint(11, 49) / 10
    v2 = random.randint(11, 99) / 100
    if v2 * 100 % 10 == 0:
        return None  # Safely skip numbers ending in 0

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 + v2, 2))

    # Force strict string formatting to prevent IndexErrors
    v1_str = f"{v1:.1f}"
    v2_str = f"{v2:.2f}"

    d1_tenth = int(v1_str.split(".")[1][0])
    d2_tenth = int(v2_str.split(".")[1][0])
    d2_hundredth = int(v2_str.split(".")[1][1])
    whole1 = int(v1)
    whole2 = int(v2)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "aligns_the_last_digits_instead_of_the_point": fmt_dec(
                round(
                    whole1 + whole2 + (d1_tenth + d2_hundredth) / 100 + (d2_tenth) / 10,
                    2,
                )
            ),
            "shifts_the_point_when_adding": fmt_dec(
                round((whole1 + whole2) / 10 + (d1_tenth + d2_tenth) / 100, 2)
            ),
            "drops_the_hundredths_digit": fmt_dec(round(v1 + int(v2 * 10) / 10, 2)),
        },
        parameters={"v1": v1, "v2": v2, "operation": "+"},
    )
    if problem:
        return problem
