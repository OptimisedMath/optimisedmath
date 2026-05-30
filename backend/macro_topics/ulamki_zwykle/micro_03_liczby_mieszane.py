import random
from backend.core.utils import format_fraction_question, build_problem_dict, format_answers


def frac_imp_1() -> dict | None:
    """Zamiana na ułamek niewłaściwy (poziom 1)."""
    w = random.randint(1, 5)
    d = random.randint(2, 9)
    n = random.randint(1, d - 1)

    q_str = (
        rf"\text{{Zamień na ułamek niewłaściwy: }} {format_fraction_question(n, d, w)}"
    )

    _, c_str, _ = format_answers((w * d) + n, d)
    _, t1, _ = format_answers((w * d) * n, d)
    _, t2, _ = format_answers(w + n, d)
    _, t3, _ = format_answers((w * d) + n, d * w)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        t3=t3,
    )
    if result:
        return result


def frac_imp_2() -> dict | None:
    """Wyłączanie całości (poziom 2)."""
    w = random.randint(1, 5)
    d = random.randint(2, 9)
    n = random.randint(1, d - 1)

    start_n = (w * d) + n
    q_str = rf"\text{{Wyłącz całości z ułamka: }} \frac{{{start_n}}}{{{d}}}"

    c_str, _, _ = format_answers(n, d, w)
    t1, _, _ = format_answers(w, 1)
    t2, _, _ = format_answers(d, n, w)

    w_wrong = w + random.choice([-1, 1])
    if w_wrong < 1:
        w_wrong = w + 2
    w1, _, _ = format_answers(n, d, w_wrong)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result
