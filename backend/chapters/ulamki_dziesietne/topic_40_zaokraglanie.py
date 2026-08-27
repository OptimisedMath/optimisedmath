import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps("rounds_the_wrong_way", "leaves_the_number_unrounded")
def dec_round_1() -> dict | None:
    """Do całości (poziom 1)."""
    v = random.randint(11, 99) / 10
    if v % 1 == 0:
        return None
    q_str = rf"\text{{Zaokrąglij do całości: }} {fmt_dec(v)}"
    c_str = str(round(v))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "rounds_the_wrong_way": (str(int(v)) if round(v) > v else str(int(v) + 1)),
            "leaves_the_number_unrounded": fmt_dec(v),
        },
        fillers=[str(int(v) + 2) if round(v) > v else str(max(0, int(v) - 1))],
    )
    if problem:
        return problem


@declares_traps("rounds_the_wrong_way", "rounds_to_the_wrong_place")
def dec_round_2() -> dict | None:
    """Do części dziesiątych (poziom 2)."""
    v = random.randint(101, 999) / 100
    if (v * 10) % 1 == 0:
        return None
    q_str = rf"\text{{Zaokrąglij do części dziesiątych: }} {fmt_dec(v)}"

    rounded = round(v, 1)
    c_str = fmt_dec(rounded)

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "rounds_the_wrong_way": (
                fmt_dec(int(v * 10) / 10)
                if rounded > v
                else fmt_dec((int(v * 10) + 1) / 10)
            ),
            "rounds_to_the_wrong_place": str(round(v)),
        },
        fillers=[fmt_dec(round(v + 0.1, 1))],
    )
    if problem:
        return problem


@declares_traps(
    "truncates_instead_of_carrying",
    "drops_the_trailing_zero_after_carrying",
    "writes_ten_in_the_tenths_place",
)
def dec_round_3() -> dict | None:
    """Zdradliwa dziewiątka (poziom 3)."""
    whole = random.randint(1, 8)
    # Force a number like 2.96, 2.97, 2.98
    v = whole + random.choice([95, 96, 97, 98, 99]) / 100
    q_str = rf"\text{{Zaokrąglij do części dziesiątych: }} {fmt_dec(v)}"

    c_str = f"{whole + 1},0"

    # Enforce exact match so they don't omit the trailing zero
    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "truncates_instead_of_carrying": f"{whole},9",
            "drops_the_trailing_zero_after_carrying": f"{whole + 1}",
            "writes_ten_in_the_tenths_place": f"{whole},10",
        },
        grading_policy="exact_match_only",
    )
    if problem:
        return problem
