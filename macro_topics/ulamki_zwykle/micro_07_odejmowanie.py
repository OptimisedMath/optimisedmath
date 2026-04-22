import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict


def frac_sub_1():
    d = random.randint(3, 9)
    n1 = random.randint(2, d - 1)
    n2 = random.randint(1, n1 - 1)

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d}}} - \frac{{{n2}}}{{{d}}}"

    c_str, _, _ = format_answers(n1 - n2, d)
    t1 = "0"
    w1, _, _ = format_answers(max(1, n1 - n2 - 1), d)
    w2, _, _ = format_answers(n1 - n2 + 1, d)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        w1=w1,
        w2=w2,
    )
    if result:
        return result


def frac_sub_2():
    d1 = random.randint(2, 5)
    factor = random.randint(2, 4)
    d2 = d1 * factor
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    if (n1 * factor) <= n2:
        return None

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} - \frac{{{n2}}}{{{d2}}}"

    c_str, _, _ = format_answers((n1 * factor) - n2, d2)
    t1, _, _ = format_answers(abs(n1 - n2), d2)
    t2, _, _ = format_answers(abs(n1 - n2), abs(d1 - d2) if d1 != d2 else 1)
    w1, _, _ = format_answers((n1 * factor) - n2 + 1, d2)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def frac_sub_3():
    d1, d2 = random.randint(3, 7), random.randint(3, 7)
    if math.gcd(d1, d2) > 1 or d1 == d2:
        return None
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    if (n1 * d2) <= (n2 * d1):
        return None

    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} - \frac{{{n2}}}{{{d2}}}"

    c_str, _, _ = format_answers((n1 * d2) - (n2 * d1), d1 * d2)
    t1, _, _ = format_answers(abs(n1 - n2), abs(d1 - d2))
    t2, _, _ = format_answers(abs(n1 - n2), d1 * d2)
    t3, _, _ = format_answers((n1 * d2) + (n2 * d1), d1 * d2)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        t3=t3,
    )
    if result:
        return result


def frac_sub_4():
    w1, w2 = random.randint(2, 4), random.randint(1, 2)
    if w1 <= w2:
        return None
    d = random.randint(3, 7)
    n1, n2 = random.randint(2, d - 1), random.randint(1, d - 2)
    if n1 <= n2:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d, w1)} - {format_fraction_question(n2, d, w2)}"

    c_str, _, _ = format_answers((w1 * d + n1) - (w2 * d + n2), d)
    t1, _, _ = format_answers(n1 - n2, 1, w1 - w2)
    t2, _, _ = format_answers(n1 - n2, d)
    w1_str, _, _ = format_answers((w1 * d + n1) - (w2 * d + n2) + d, d)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1_str,
    )
    if result:
        return result


def frac_sub_5():
    w1, w2 = random.randint(2, 4), random.randint(1, 2)
    if w1 <= w2:
        return None
    d = random.randint(3, 7)
    n1, n2 = random.randint(1, d - 2), random.randint(2, d - 1)
    if n1 >= n2:
        return None

    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d, w1)} - {format_fraction_question(n2, d, w2)}"

    c_str, _, _ = format_answers((w1 * d + n1) - (w2 * d + n2), d)
    t1, _, _ = format_answers(n2 - n1, d, w1 - w2)
    t2, _, _ = format_answers((n1 + 10) - n2, d, (w1 - 1) - w2)
    t3, _, _ = format_answers((d + n1) - n2, d, w1 - w2)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        t3=t3,
    )
    if result:
        return result
