import random
from backend.core.utils import (
    build_problem_dict,
    declares_traps,
    format_fraction_answer,
)


@declares_traps(
    "swaps_dividend_and_divisor",
    "sums_operands_into_the_denominator",
    "copies_the_divisor_off_by_one",
)
def frac_write_1() -> dict | None:
    """Dzielenie jako ułamek (poziom 1)."""
    n = random.randint(1, 9)
    d = random.randint(2, 9)
    if n == d:
        return None

    q_str = rf"\text{{Zapisz dzielenie jako ułamek: }} {n} : {d}"

    c_str = format_fraction_answer(n, d, simplify=False)
    w_denom = d + random.choice([-1, 1])
    if w_denom < 2:
        w_denom = d + 1

    result = build_problem_dict(
        q_str,
        c_str,
        traps={
            "swaps_dividend_and_divisor": format_fraction_answer(d, n, simplify=False),
            "sums_operands_into_the_denominator": format_fraction_answer(
                n, n + d, simplify=False
            ),
            "copies_the_divisor_off_by_one": format_fraction_answer(
                n, w_denom, simplify=False
            ),
        },
        grading_policy="equivalent_accepted",
    )
    if result:
        return result
