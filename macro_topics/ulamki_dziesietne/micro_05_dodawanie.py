import random
from core.utils import build_problem_dict, fmt_dec


def dec_add_1():
    w1, w2 = random.randint(1, 4), random.randint(1, 4)
    d1, d2 = random.randint(1, 8), random.randint(1, 8)
    if d1 + d2 >= 10:
        return None

    v1 = w1 + (d1 / 10)
    v2 = w2 + (d2 / 10)

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)}"
    c_str = fmt_dec(v1 + v2)

    t1 = fmt_dec((w1 + d2) + ((w2 + d1) / 10))
    w1_ans = fmt_dec(v1 + v2 + 0.1)
    w2_ans = fmt_dec(v1 + v2 + 1)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        w1=w1_ans,
        w2=w2_ans,
    )
    if result:
        return result


def dec_sub_2():
    v1 = random.randint(311, 999) / 100
    v2 = random.randint(11, int(v1 * 10) - 1) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 - v2, 2))

    t1 = fmt_dec(round(v1 - (v2 / 10), 2))
    t2 = fmt_dec(round(v1 - v2 + 0.09, 2))
    w1 = fmt_dec(round(v1 - v2 + 1, 2))

    return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1)


def dec_add_3():
    v1 = random.randint(11, 49) / 10
    v2 = random.randint(11, 99) / 100
    if v2 * 100 % 10 == 0:
        return None  # Safely skip numbers ending in 0

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 + v2, 2))

    # Force strict string formatting to prevent IndexErrors
    v1_str = f"{v1:.1f}"
    v2_str = f"{v2:.2f}"

    d1_tenth = int(v1_str.split(".")[1][0])
    d2_tenth = int(v2_str.split(".")[1][0])
    d2_hundredth = int(v2_str.split(".")[1][1])
    w1_whole = int(v1)
    w2_whole = int(v2)

    t1 = fmt_dec(
        round(
            w1_whole + w2_whole + (d1_tenth + d2_hundredth) / 100 + (d2_tenth) / 10, 2
        )
    )
    t2 = fmt_dec(round((w1_whole + w2_whole) / 10 + (d1_tenth + d2_tenth) / 100, 2))
    t3 = fmt_dec(round(v1 + int(v2 * 10) / 10, 2))

    return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3)
