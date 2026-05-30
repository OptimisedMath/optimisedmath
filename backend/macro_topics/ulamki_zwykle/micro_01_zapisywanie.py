import random
from backend.core.utils import build_problem_dict, format_answers


def frac_write_1() -> dict | None:
    """Dzielenie jako ułamek (poziom 1)."""
    n = random.randint(1, 9)
    d = random.randint(2, 9)
    if n == d:
        return None

    q_str = rf"\text{{Zapisz dzielenie jako ułamek: }} {n} : {d}"

    c_str, _, _ = format_answers(n, d)
    t1, _, _ = format_answers(d, n)
    t2, _, _ = format_answers(n, n + d)
    w_denom = d + random.choice([-1, 1])
    if w_denom < 2:
        w_denom = d + 1
    w1, _, _ = format_answers(n, w_denom)

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, w1=w1, grading_policy="equivalent_accepted"
    )
    if result:
        return result
