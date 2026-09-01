import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps(
    "shifts_the_point_the_wrong_way",
    "shifts_by_the_wrong_number_of_places",
    "appends_zeros_without_moving_the_point",
)
def dec_comma_1() -> dict | None:
    """Mnożenie przez 10, 100... (poziom 1)."""
    v = random.randint(111, 999) / 100
    zeros = random.choice([10, 100, 1000])

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v)} \cdot {zeros}"
    c_str = fmt_dec(round(v * zeros, 2))

    wrong_zeros = zeros * 10 if zeros < 1000 else 100
    num_zeros = len(str(zeros)) - 1

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "shifts_the_point_the_wrong_way": fmt_dec(round(v / zeros, 4)),
            "shifts_by_the_wrong_number_of_places": fmt_dec(round(v * wrong_zeros, 2)),
            "appends_zeros_without_moving_the_point": fmt_dec(v) + "0" * num_zeros,
        },
        parameters={"v": v, "zeros": zeros},
    )
    if problem:
        return problem


@declares_traps(
    "shifts_the_point_the_wrong_way",
    "shifts_by_the_wrong_number_of_places",
    "shifts_one_place_too_far",
)
def dec_comma_2() -> dict | None:
    """Dzielenie przez 10, 100... (poziom 2)."""
    v = random.randint(111, 999) / 10
    zeros = random.choice([10, 100, 1000])

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v)} : {zeros}"
    c_str = fmt_dec(round(v / zeros, 5))

    wrong_zeros = zeros / 10 if zeros > 10 else 100

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "shifts_the_point_the_wrong_way": fmt_dec(round(v * zeros, 2)),
            "shifts_by_the_wrong_number_of_places": fmt_dec(round(v / wrong_zeros, 4)),
            "shifts_one_place_too_far": fmt_dec(round(v / (zeros * 10), 6)),
        },
        parameters={"v": v, "zeros": zeros},
    )
    if problem:
        return problem
