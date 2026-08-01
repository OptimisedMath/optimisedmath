import random
from backend.core.utils import build_problem_dict, fmt_dec


def dec_div_1() -> dict | None:
    """Przez liczbę całkowitą (bez reszty) (poziom 1)."""
    c = random.randint(2, 9)
    d = random.randint(2, 5)
    v1 = (c * d) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {d}"
    c_str = fmt_dec(round(v1 / d, 2))

    t1 = fmt_dec(round((v1 * 10) / d, 2))  # Trap (t1): Zgubiłeś przecinek
    t2 = fmt_dec(round(v1 / (d * 10), 3))  # Trap (t2): Błędnie przesunąłeś przecinek w wyniku — policz miejsca po przecinku w...
    w1 = fmt_dec(round((v1 / d) + 0.1, 2))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def dec_div_2() -> dict | None:
    """Przez liczbę całkowitą (z resztą) (poziom 2)."""
    c = random.randint(2, 9)
    d = random.randint(2, 5)
    v1 = (c * d) / 100
    v2 = d / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 / v2, 2))

    t1 = fmt_dec(round(v1 / (v2 * 10), 3))  # Trap (t1): Wynik wyszedł z resztą
    t2 = fmt_dec(round((v1 / v2) * 10, 2))  # Trap (t2): Brakuje zera w wyniku przed cyframi
    # FIX: Simulate student improperly summing the decimal places (3 total places instead of 1)
    t3 = fmt_dec(round((v1 / v2) / 100, 3))  # Trap (t3): Przecinek w złym miejscu

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        t3=t3,
    )
    if result:
        return result


def dec_div_3() -> dict | None:
    """Przez ułamek dziesiętny (proste) (poziom 3)."""
    c = random.randint(2, 9)
    d = random.randint(2, 5)
    v1 = (c * d) / 10
    v2 = d / 100

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 / v2, 2))

    t1 = fmt_dec(round((v1 / 10) / v2, 2))  # Trap (t1): Nie wolno dzielić przez ułamek
    t2 = fmt_dec(round((v1 / 100) / v2, 3))  # Trap (t2): Błąd mnożenia licznika i dzielnika po przesunięciu przecinka
    w1 = fmt_dec(round((v1 / v2) + 1, 2))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def dec_div_4() -> dict | None:
    """Przez ułamek dziesiętny (zaawansowane) (poziom 4)."""
    # Generate divisions like 0.3 : 2 = 0.15 where student must append a 0
    v1 = random.choice([1, 3, 5, 7, 9]) / 10
    d = random.choice([2, 4, 5])
    if (v1 * 10) % d == 0:
        return None  # Skip if no phantom zero is needed

    q_str = rf"\text{{Oblicz (dopisz zero na końcu dzielnej): }} {fmt_dec(v1)} : {d}"
    c_str = fmt_dec(round(v1 / d, 3))

    t1 = fmt_dec(round((v1 * 10) / d, 3))  # Forgot the decimal shift
    t2 = fmt_dec(round(v1 / (d * 10), 4))  # Trap (t2): Nie masz już gdzie przesunąć? Zamiast kroku dodawaj na końcu zera (np
    w1 = fmt_dec(round((v1 / d) + 0.1, 3))

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result
