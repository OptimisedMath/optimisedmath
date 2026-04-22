import random
from core.utils import build_problem_dict, fmt_dec, format_answers


def dec_mix_1():
    d = random.choice([2, 4, 5, 10])
    n = random.randint(1, d - 1)

    d2 = random.choice([2, 4, 5, 10])
    n2 = random.randint(1, d2 - 1)
    dec_val = n2 / d2

    q_str = rf"\text{{Oblicz: }} \frac{{{n}}}{{{d}}} + {fmt_dec(dec_val)}"

    c_num = (n * d2) + (n2 * d)
    c_den = d * d2
    c_str, _, _ = format_answers(c_num, c_den)

    t1, _, _ = format_answers(n + n2, d + d2)
    t2, _, _ = format_answers(n + n2, d * d2)
    w1, _, _ = format_answers(c_num + 1, c_den)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def dec_mix_2():
    # Denominators that create infinite decimals (1/3, 1/6) forcing fraction math
    d1 = random.choice([3, 6, 7, 9])
    n1 = random.randint(1, d1 - 1)

    d2 = random.choice([2, 5, 10])
    n2 = random.randint(1, d2 - 1)
    dec_val = n2 / d2

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} + {fmt_dec(dec_val)}"

    c_num = (n1 * d2) + (n2 * d1)
    c_den = d1 * d2
    c_str, _, _ = format_answers(c_num, c_den)

    t1, _, _ = format_answers(n1 + n2, d1 + 10)
    t2 = fmt_dec(round(n1 / d1 + dec_val, 2))
    w1, _, _ = format_answers(c_num + 1, c_den)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def dec_mix_3():
    d1 = random.choice([3, 4, 5, 6, 7])
    n1 = random.randint(1, d1 - 1)

    d2 = random.choice([2, 4, 5])
    n2 = random.randint(1, d2 - 1)
    dec_val = n2 / d2

    if random.choice([True, False]):
        q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} \cdot {fmt_dec(dec_val)}"
        c_num = n1 * n2
        c_den = d1 * d2
        t1, _, _ = format_answers(n1 + n2, d1 * d2)
    else:
        q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} : {fmt_dec(dec_val)}"
        c_num = n1 * d2
        c_den = d1 * n2
        t1, _, _ = format_answers(n1 * n2, d1 * d2)

    c_str, _, _ = format_answers(c_num, c_den)
    t2, _, _ = format_answers(c_num + 1, c_den)
    w1, _, _ = format_answers(c_num, c_den + 1)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result
