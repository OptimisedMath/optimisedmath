import random
from backend.core.utils import build_problem_dict, fmt_dec


def dec_compare_1() -> dict | None:
    """Różne cyfry, te same pozycje (poziom 1)."""
    n1 = random.randint(11, 99)
    n2 = random.randint(11, 99)
    if n1 == n2 or n1 % 10 == 0 or n2 % 10 == 0:
        return None

    v1, v2 = n1 / 100, n2 / 100
    q_str = rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
    c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")

    t2 = "="  # Trap (t2): znak równości przy nierównych liczbach

    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2)
    if result:
        return result


def dec_compare_2() -> dict | None:
    """Różna liczba miejsc po przecinku (poziom 2)."""
    if random.random() < 0.2:
        base = random.randint(1, 9)
        s1 = f"0,{base}"
        s2 = f"0,{base}0"
        if random.choice([True, False]):
            s1, s2 = s2, s1
        q_str = rf"\text{{Wybierz znak: }} {s1} \text{{ \_\_\_ }} {s2}"

        t2 = "<"  # Trap (t2): znak mniejszości przy równych liczbach
        t3 = ">"  # Trap (t3): znak większości przy równych liczbach

        result = build_problem_dict(q_str, "=", t2=t2, t3=t3)
        if result:
            return result
    else:
        v1 = random.randint(2, 9) / 10
        v2 = random.randint(11, 99) / 100
        if v1 == v2 or int(v2 * 100) % 10 == 0:
            return None

        if random.choice([True, False]):
            v1, v2 = v2, v1
        q_str = (
            rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
        )
        c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        t2 = "="  # Trap (t2): znak równości przy nierównych liczbach

        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2)
        if result:
            return result


def dec_compare_3() -> dict | None:
    """Zdradliwe zera (poziom 3)."""
    if random.random() < 0.2:
        whole = random.randint(1, 5)
        digit = random.randint(1, 9)
        s1 = f"{whole},0{digit}"
        s2 = f"{whole},0{digit}0"
        if random.choice([True, False]):
            s1, s2 = s2, s1
        q_str = rf"\text{{Wybierz znak: }} {s1} \text{{ \_\_\_ }} {s2}"

        t2 = "<"  # Trap (t2): znak mniejszości przy równych liczbach
        t3 = ">"  # Trap (t3): znak większości przy równych liczbach

        result = build_problem_dict(q_str, "=", t2=t2, t3=t3)
        if result:
            return result
    else:
        whole = random.randint(1, 5)
        digit = random.randint(1, 9)
        v1 = whole + (digit / 100)
        v2 = whole + (digit / 10)
        if random.choice([True, False]):
            v1, v2 = v2, v1

        q_str = (
            rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
        )
        c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        t2 = "="  # Trap (t2): znak równości przy nierównych liczbach

        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2)
        if result:
            return result
