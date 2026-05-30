import random
from backend.core.utils import format_answers, format_fraction_question, build_problem_dict


def frac_frac_of_int_1() -> dict | None:
    """Całości bez reszty (poziom 1)."""
    d = random.randint(2, 8)
    n = random.randint(1, d - 1)
    k = d * random.randint(2, 6)

    q_str = (
        rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
    )

    c_str, _, _ = format_answers((k // d) * n, 1)
    t1, _, _ = format_answers(k * d + n, d)
    t2, _, _ = format_answers(k // n * d, 1)
    w1, _, _ = format_answers((k // d) * n + 1, 1)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def frac_frac_of_int_2() -> dict | None:
    """Trudniejsze liczby (poziom 2)."""
    d = random.randint(3, 9)
    n = random.randint(1, d - 1)
    k = random.randint(4, 15)
    if k % d == 0:
        return None

    q_str = (
        rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
    )

    c_str, _, _ = format_answers(n * k, d)
    t1, _, _ = format_answers(k * d, n)
    t2, _, _ = format_answers(n * k, d * k)
    w1, _, _ = format_answers(n * k + 1, d)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def frac_frac_of_int_3() -> dict | None:
    """Gdy wynik jest ułamkiem (poziom 3)."""
    d = random.randint(3, 8)
    n = random.randint(2, d - 1)
    whole = d * random.randint(2, 6)
    part = (whole // d) * n

    q_str = rf"\text{{Znajdź liczbę, której }} \frac{{{n}}}{{{d}}} \text{{ wynosi }} {part}."
    c_str = str(whole)

    t1 = str(int((part // n) * (d + 1)))  # Miscalculated the multiplier
    t2 = str(  # Trap (t2): Podałeś odwrotność
        int(part * n // d)
    )  # TRAP: Calculated the fraction OF the number instead of finding the whole
    w1 = str(whole + d)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result


def frac_frac_of_int_4() -> dict | None:
    """Ułamek z liczby mieszanej (poziom 4)."""
    d = random.randint(3, 6)
    n = random.randint(1, d - 1)
    base = d * random.randint(2, 5)

    is_increase = random.choice([True, False])
    action = "Powiększ" if is_increase else "Pomniejsz"

    q_str = rf"\text{{{action} liczbę }} {base} \text{{ o }} \frac{{{n}}}{{{d}}} \text{{ jej wartości.}}"

    change = (base // d) * n
    c_val = base + change if is_increase else base - change
    c_str = str(c_val)

    t1 = str(  # Trap (t1): Zamień ułamek na postać niewłaściwą zanim zaczniesz mnożyć
        change
    )  # TRAP: Only calculated the fraction, forgot to add/subtract it to the base!
    t2 = (
        str(base + n) if is_increase else str(base - n)
    )  # TRAP: Just added the numerator
    w1 = str(c_val + 1)

    result = build_problem_dict(
        q_str,
        c_str,
        t1=t1,
        t2=t2,
        w1=w1,
    )
    if result:
        return result
