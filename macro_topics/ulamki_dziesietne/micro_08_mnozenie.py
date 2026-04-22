import random
from core.utils import build_problem_dict, fmt_dec


def dec_mult_1():
    v1 = random.randint(2, 9) / 10
    v2 = random.randint(2, 9)

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {v2}"
    c_str = fmt_dec(round(v1 * v2, 2))

    t1 = fmt_dec(round(v1 * v2 / 100, 3))
    t2 = fmt_dec(round(v1 * 10 * v2, 2))
    w1 = fmt_dec(round((v1 * 10 * v2 + 1) / 10, 2))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def dec_mult_2():
    v1 = random.randint(2, 9) / 10
    v2 = random.randint(2, 9) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 * v2, 2))

    t1 = fmt_dec(round(v1 * v2 * 10, 2))
    t2 = fmt_dec(round(v1 * 10 * v2 * 10, 2))
    t3 = fmt_dec(round(v1 * v2 / 10, 3))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        t3=t3,
    )
    if result:
        return result


def dec_mult_3():
    v1 = random.choice([1.5, 2.5, 3.5, 4.5])
    v2 = random.choice([0.2, 0.4, 0.6, 0.8])

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
    val = round(v1 * v2, 2)
    c_str = fmt_dec(val)

    t1 = fmt_dec(round(val * 10, 2))
    t2 = fmt_dec(round(val / 10, 2))
    w1 = fmt_dec(round((v1 * 10 * v2 * 10) + 1, 2))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result
