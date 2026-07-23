import random
from backend.core.utils import build_problem_dict, format_fraction_answer


def frac_write_1() -> dict | None:
    """Dzielenie jako ułamek (poziom 1)."""
    n = random.randint(1, 9)
    d = random.randint(2, 9)
    if n == d:
        return None

    q_str = rf"\text{{Zapisz dzielenie jako ułamek: }} {n} : {d}"

    c_str = format_fraction_answer(n, d, simplify=False)
    t1 = format_fraction_answer(d, n, simplify=False)
    t2 = format_fraction_answer(n, n + d, simplify=False)
    w_denom = d + random.choice([-1, 1])
    if w_denom < 2:
        w_denom = d + 1
    w1 = format_fraction_answer(n, w_denom, simplify=False)

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, w1=w1, grading_policy="equivalent_accepted"
    )
    if result:
        return result
