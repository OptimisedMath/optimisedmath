import random
from backend.core.utils import build_problem_dict, fmt_dec


def dec_sub_1() -> dict | None:
    """Bez pożyczania (poziom 1)."""
    v1 = random.randint(31, 99) / 10
    v2 = random.randint(11, int(v1 * 10) - 1) / 10
    if str(v1).endswith(".0") or str(v2).endswith(".0"):
        return None

    d1 = int(str(v1).split(".")[1])
    d2 = int(str(v2).split(".")[1])
    if d1 >= d2:
        return None

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 - v2, 2))

    t1 = fmt_dec(round(int(v1) - int(v2) + abs(d1 - d2) / 10, 2))  # Trap (t1): Przecinek uciekł w złe miejsce
    w1 = fmt_dec(round(v1 - v2 + 0.1, 2))
    w2 = fmt_dec(round(v1 - v2 - 0.1, 2))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        w1=w1,
        w2=w2,
    )
    if result:
        return result


def dec_sub_2() -> dict | None:
    """Z pożyczaniem (poziom 2)."""
    v1 = random.randint(311, 999) / 100
    v2 = random.randint(11, int(v1 * 10) - 1) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 - v2, 2))

    t1 = fmt_dec(round(v1 - (v2 / 10), 2))  # Trap (t1): Zapomniałeś o pożyczaniu z sąsiedniego rzędu
    t2 = fmt_dec(round(v1 - v2 + 0.09, 2))  # Trap (t2): Błędnie przepisałeś przecinek
    w1 = fmt_dec(round(v1 - v2 + 1, 2))

    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1)

    if result:
        return result


def dec_sub_3() -> dict | None:
    """Z dopisywaniem zer (np. 1 - 0.25) (poziom 3)."""
    v1 = random.randint(31, 99) / 10
    v2 = random.randint(111, int(v1 * 100) - 1) / 100
    if str(v1).endswith(".0") or str(v2).endswith(".0"):
        return None

    d1 = int(str(v1).split(".")[1])
    d2_tenths = int(str(v2).split(".")[1][0])
    if d1 >= d2_tenths:
        return None

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 - v2, 2))

    t1 = fmt_dec(round(v1 - round(v2, 1) + (int(str(v2)[-1]) / 100), 2))  # Trap (t1): Nie masz od czego odjąć liczby
    t2 = fmt_dec(round(v1 - v2 - 0.4, 2))  # Trap (t2): Błąd w rzędzie dziesiątek - gdy pożyczasz nad zerem, to zero staje się...
    t3 = fmt_dec(round(v1 - v2 + 0.1, 2))  # Trap (t3): Błąd pożyczania

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        t3=t3,
    )
    if result:
        return result
