import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps("adds_instead_of_subtracting")
def dec_sub_1() -> dict | None:
    """Bez pożyczania (poziom 1)."""
    v1 = random.randint(31, 99) / 10
    v2 = random.randint(11, int(v1 * 10) - 1) / 10
    if str(v1).endswith(".0") or str(v2).endswith(".0"):
        return None

    d1 = int(str(v1).split(".")[1])
    d2 = int(str(v2).split(".")[1])
    if d1 <= d2:
        return None

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 - v2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={"adds_instead_of_subtracting": fmt_dec(round(v1 + v2, 2))},
        fillers=[
            fmt_dec(round(v1 - v2 + 0.1, 2)),
            fmt_dec(round(v1 - v2 - 0.1, 2)),
        ],
        parameters={"v1": v1, "v2": v2},
    )
    if problem:
        return problem


@declares_traps(
    "misaligns_the_second_number_by_one_place",
    "borrows_but_leaves_nine_in_the_hundredths",
)
def dec_sub_2() -> dict | None:
    """Z pożyczaniem (poziom 2)."""
    v1 = random.randint(311, 999) / 100
    v2 = random.randint(11, int(v1 * 10) - 1) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 - v2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "misaligns_the_second_number_by_one_place": fmt_dec(
                round(v1 - (v2 / 10), 2)
            ),
            "borrows_but_leaves_nine_in_the_hundredths": fmt_dec(
                round(v1 - v2 + 0.09, 2)
            ),
        },
        fillers=[fmt_dec(round(v1 - v2 + 1, 2))],
        parameters={"v1": v1, "v2": v2, "operation": "-"},
    )

    if problem:
        return problem


@declares_traps(
    "mishandles_the_hundredths_when_borrowing",
    "borrows_over_zero_incorrectly",
    "off_by_one_tenth_when_borrowing",
)
def dec_sub_3() -> dict | None:
    """Z dopisywaniem zer (np. 1 - 0.25) (poziom 3)."""
    v1 = random.randint(31, 99) / 10
    v2 = random.randint(111, int(v1 * 100) - 1) / 100
    if str(v1).endswith(".0") or str(v2).endswith(".0"):
        return None

    d1 = int(str(v1).split(".")[1])
    d2_tenths = int(str(v2).split(".")[1][0])
    if d1 >= d2_tenths:
        return None

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 - v2, 2))

    problem = build_problem_dict(
        q_str,
        c_str,
        traps={
            "mishandles_the_hundredths_when_borrowing": fmt_dec(
                round(v1 - round(v2, 1) + (int(str(v2)[-1]) / 100), 2)
            ),
            "borrows_over_zero_incorrectly": fmt_dec(round(v1 - v2 - 0.4, 2)),
            "off_by_one_tenth_when_borrowing": fmt_dec(round(v1 - v2 + 0.1, 2)),
        },
        parameters={"v1": v1, "v2": v2},
    )
    if problem:
        return problem
