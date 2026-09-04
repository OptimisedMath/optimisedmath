"""Ułamki Dziesiętne — Zamiana ułamków: generatory Problemów."""

import random
from decimal import Decimal
from fractions import Fraction
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps(
    "uses_one_fewer_place_for_the_denominator",
    "inverts_into_a_unit_fraction",
    "shifts_the_denominator_by_one",
)
def dec_to_frac_1() -> dict | None:
    """Z ułamka dziesiętnego na zwykły (poziom 1)."""
    denominators = [4, 5, 20, 25, 50]
    d = random.choice(denominators)
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d:
        return None

    val = n / d
    q_str = rf"\text{{Zamień na ułamek zwykły: }} {fmt_dec(val)}"
    c_str = rf"\frac{{{n}}}{{{d}}}"

    decimals = len(str(val).split(".")[1])
    raw_d = 10**decimals
    raw_n = int(val * raw_d)

    wrong_d = d + random.choice([-1, 1])
    if wrong_d < 2:
        wrong_d = d + 2

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "uses_one_fewer_place_for_the_denominator": rf"\frac{{{raw_n}}}{{{raw_d // 10}}}",
            "inverts_into_a_unit_fraction": rf"\frac{{{1}}}{{{raw_n}}}",
            "shifts_the_denominator_by_one": rf"\frac{{{n}}}{{{wrong_d}}}",
        },
        parameters={"n": n, "d": d},
    )
    if problem:
        return problem


@declares_traps(
    "writes_the_digits_side_by_side",
    "shifts_the_point_one_place_too_far",
    "writes_the_denominator_after_the_point",
)
def dec_to_frac_2() -> dict | None:
    """Ze zwykłego na dziesiętny (ułamek właściwy) (poziom 2)."""
    d = random.choice([4, 5, 20, 25])
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d:
        return None

    q_str = rf"\text{{Zamień na ułamek dziesiętny: }} \frac{{{n}}}{{{d}}}"
    val = Decimal(n) / Decimal(d)
    c_str = fmt_dec(val)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "writes_the_digits_side_by_side": f"0,{n}{d}",
            "shifts_the_point_one_place_too_far": fmt_dec(val / 10),
            "writes_the_denominator_after_the_point": fmt_dec(
                Decimal(n) + (Decimal(d) / 10)
            ),
        },
        parameters={"n": n, "d": d},
    )
    if problem:
        return problem


@declares_traps(
    "writes_the_digits_side_by_side",
    "shifts_the_point_one_place_too_far",
    "writes_the_denominator_after_the_point",
)
def dec_to_frac_3() -> dict | None:
    """Ze zwykłego na dziesiętny (liczba mieszana) (poziom 3)."""
    w = random.randint(1, 5)
    d = random.choice([2, 4, 5, 20])
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d:
        return None

    q_str = rf"\text{{Zamień na ułamek dziesiętny: }} {w}\frac{{{n}}}{{{d}}}"
    val = Decimal(w) + (Decimal(n) / Decimal(d))
    c_str = fmt_dec(val)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "writes_the_digits_side_by_side": f"{w},{n}{d}",
            "shifts_the_point_one_place_too_far": fmt_dec(val / 10),
            "writes_the_denominator_after_the_point": f"{w},{d}",
        },
        parameters={"w": w, "n": n, "d": d},
    )
    if problem:
        return problem


@declares_traps(
    "omits_the_period_brackets",
    "adds_a_leading_zero_before_the_period",
    "gets_the_period_digit_wrong",
)
def dec_to_frac_4() -> dict | None:
    """Ze zwykłego na dziesiętny (dzielenie) (poziom 4)."""
    d = random.choice([3, 9])
    n = random.randint(1, d - 1)

    q_str = rf"\text{{Rozwiń ułamek (zapisz w okresie): }} \frac{{{n}}}{{{d}}}"

    val = int((n / d) * 10)
    c_str = f"0,({val})"

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "omits_the_period_brackets": f"0,{val}",
            "adds_a_leading_zero_before_the_period": f"0,0({val})",
            "gets_the_period_digit_wrong": f"0,({val + 1})",
        },
        parameters={"n": n, "d": d},
    )
    if problem:
        return problem
