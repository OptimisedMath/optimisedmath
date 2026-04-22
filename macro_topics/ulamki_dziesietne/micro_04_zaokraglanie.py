import random
from core.utils import build_problem_dict, fmt_dec


def dec_round_1():
    v = random.randint(11, 99) / 10
    if v % 1 == 0:
        return None
    q_str = rf"\text{{Zaokrąglij do całości: }} {fmt_dec(v)}"
    c_str = str(round(v))

    t1 = str(int(v)) if round(v) > v else str(int(v) + 1)
    t2 = fmt_dec(v)
    w1 = str(int(v) + 2) if round(v) > v else str(max(0, int(v) - 1))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def dec_round_2():
    v = random.randint(101, 999) / 100
    if (v * 10) % 1 == 0:
        return None
    q_str = rf"\text{{Zaokrąglij do części dziesiątych: }} {fmt_dec(v)}"

    rounded = round(v, 1)
    c_str = fmt_dec(rounded)

    t1 = fmt_dec(int(v * 10) / 10) if rounded > v else fmt_dec((int(v * 10) + 1) / 10)
    t2 = str(round(v))
    w1 = fmt_dec(round(v + 0.1, 1))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def dec_round_3():
    whole = random.randint(1, 8)
    # Force a number like 2.96, 2.97, 2.98
    v = whole + random.choice([95, 96, 97, 98, 99]) / 100
    q_str = rf"\text{{Zaokrąglij do części dziesiątych: }} {fmt_dec(v)}"

    c_str = f"{whole + 1},0"

    t1 = f"{whole},9"
    t2 = f"{whole + 1}"
    w1 = f"{whole},10"

    # Enforce exact match so they don't omit the trailing zero
    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, w1=w1, grading_policy="exact_match_only"
    )
    if result:
        return result
