import random
from backend.core.utils import build_problem_dict, fmt_dec


def dec_mult_1() -> dict | None:
    """Przez liczbę jednocyfrową (poziom 1)."""
    v1 = random.randint(2, 9) / 10
    v2 = random.randint(2, 9)

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {v2}"
    c_str = fmt_dec(round(v1 * v2, 2))

    t1 = fmt_dec(round(v1 * v2 / 100, 3))  # Trap (t1): Źle wstawiony przecinek w wyniku
    t2 = fmt_dec(round(v1 * 10 * v2, 2))  # Trap (t2): Zły wynik mnożenia
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


def dec_mult_2() -> dict | None:
    """Ułamek przez ułamek (poziom 2)."""
    v1 = random.randint(2, 9) / 10
    v2 = random.randint(2, 9) / 10

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
    c_str = fmt_dec(round(v1 * v2, 2))

    t1 = fmt_dec(round(v1 * v2 * 10, 2))  # Trap (t1): Pomyłka z przecinkiem
    t2 = fmt_dec(round(v1 * 10 * v2 * 10, 2))  # Trap (t2): Błąd w obliczeniach
    t3 = fmt_dec(round(v1 * v2 / 10, 3))  # Trap (t3): Za mało miejsc po przecinku w wyniku

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        t3=t3,
    )
    if result:
        return result


def dec_mult_3() -> dict | None:
    """Z dużą ilością zer (poziom 3)."""
    v1 = random.choice([1.5, 2.5, 3.5, 4.5])
    v2 = random.choice([0.2, 0.4, 0.6, 0.8])

    q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
    val = round(v1 * v2, 2)
    c_str = fmt_dec(val)

    t1 = fmt_dec(round(val * 10, 2))  # Trap (t1): Brak przecinka lub w złym miejscu
    t2 = fmt_dec(round(val / 10, 2))  # Trap (t2): Zgubiłeś zera po przecinku przed samą liczbą
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
