import random
from fractions import Fraction
from backend.core.utils import build_problem_dict, fmt_dec


def dec_to_frac_1() -> dict | None:
    """Z ułamka dziesiętnego na zwykły (poziom 1)."""
    denominators = [4, 5, 20, 25, 50]
    d = random.choice(denominators)
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d:
        return None

    val = n / d
    q_str = rf"\text{{Zamień na ułamek zwykły: }} {fmt_dec(val)}"
    c_str = rf"\frac{{{n}}}{{{d}}}"

    decimals = len(str(val).split(".")[1])
    raw_d = 10**decimals
    raw_n = int(val * raw_d)

    t1 = rf"\frac{{{raw_n}}}{{{raw_d // 10}}}"  # Trap (t1): zły mianownik względem miejsc po przecinku
    t2 = rf"\frac{{{1}}}{{{raw_n}}}"  # Trap (t2): pominięcie całości
    wrong_d = d + random.choice([-1, 1])
    if wrong_d < 2:
        wrong_d = d + 2
    t3 = rf"\frac{{{n}}}{{{wrong_d}}}"  # Trap (t3): zły licznik

    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3)
    if result:
        return result


def dec_to_frac_2() -> dict | None:
    """Ze zwykłego na dziesiętny (mianowniki 10, 100) (poziom 2)."""
    d = random.choice([4, 5, 20, 25])
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d:
        return None

    q_str = rf"\text{{Zamień na ułamek dziesiętny: }} \frac{{{n}}}{{{d}}}"
    val = n / d
    c_str = fmt_dec(val)

    t1 = f"0,{n}{d}"  # Trap (t1): za mało miejsc po przecinku
    t2 = fmt_dec(val / 10)  # Trap (t2): za dużo miejsc po przecinku
    t3 = fmt_dec(n + (d / 10))  # Trap (t3): błędna cyfra z licznika

    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3)
    if result:
        return result


def dec_to_frac_3() -> dict | None:
    """Ze zwykłego na dziesiętny (rozszerzanie 2, 4, 5) (poziom 3)."""
    w = random.randint(1, 5)
    d = random.choice([2, 4, 5, 20])
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d:
        return None

    q_str = rf"\text{{Zamień na ułamek dziesiętny: }} {w}\frac{{{n}}}{{{d}}}"
    val = w + (n / d)
    c_str = fmt_dec(val)

    t1 = f"{w},{n}{d}"  # Trap (t1): brak rozszerzenia przed przecinkiem
    t2 = fmt_dec(val / 10)  # Trap (t2): pominięcie licznika przy rozszerzaniu
    t3 = f"{w},{d}"  # Trap (t3): błąd przy rozszerzaniu

    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3)
    if result:
        return result


def dec_to_frac_4() -> dict | None:
    """Ze zwykłego na dziesiętny (dzielenie) (poziom 4)."""
    d = random.choice([3, 9])
    n = random.randint(1, d - 1)

    q_str = rf"\text{{Rozwiń ułamek (zapisz w okresie): }} \frac{{{n}}}{{{d}}}"

    val = int((n / d) * 10)
    c_str = f"0,({val})"

    t1 = f"0,{val}"  # Trap (t1): brak nawiasów okresu
    t2 = f"0,0({val})"  # Trap (t2): zbędne zero przed okresem
    t3 = f"0,({val + 1})"  # Trap (t3): zła cyfra w okresie

    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3)
    if result:
        return result
