import random
from backend.core.utils import build_problem_dict, fmt_dec


def _repeating_decimal_str(n: int, d: int) -> tuple[str, float]:
    val = n / d
    period = int(val * 10)
    return f"0,({period})", val


def _with_messages(result: dict, **msgs: str) -> dict:
    result["messages"] = msgs
    return result


_MSG_EQUAL_TRAILING = "Liczby są równe — zera na końcu nie zmieniają wartości!"
_MSG_EQUAL_WRONG_SIGN = "Gdy liczby są równe, nie wybieraj '<' ani '>'!"
_MSG_NOT_EQUAL = "Liczby nie są równe — nie wybieraj znaku równości!"


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
        return _with_messages(
            result,
            t1=(
                "Spójrz najpierw na najwyższy rząd (całości, potem części dziesiąte). "
                "Cyfra z przodu ma zawsze największą wagę!"
            ),
            t2=_MSG_NOT_EQUAL,
        )


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
            return _with_messages(
                result,
                t2=_MSG_EQUAL_TRAILING,
                t3=_MSG_EQUAL_WRONG_SIGN,
            )
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
            return _with_messages(
                result,
                t1=(
                    "Dopisz niewidzialne zera, aby obie liczby miały tyle samo miejsc "
                    "po przecinku (np. 0,1 to 0,10), i porównaj jeszcze raz."
                ),
                t2=_MSG_NOT_EQUAL,
            )


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
            return _with_messages(
                result,
                t2=_MSG_EQUAL_TRAILING,
                t3=_MSG_EQUAL_WRONG_SIGN,
            )
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
            return _with_messages(
                result,
                t1=(
                    "Pamiętaj, zero zaraz po przecinku jest bardzo ważne (zmniejsza ułamek), "
                    "ale zera na samym końcu można wykreślić!"
                ),
                t2=_MSG_NOT_EQUAL,
            )


def dec_compare_4() -> dict | None:
    """Rozwinięcie nieskończone (poziom 4)."""
    roll = random.random()
    if roll < 0.60:
        d = random.choice([3, 9])
        n = random.randint(1, d - 1)
        s_rep, v_rep = _repeating_decimal_str(n, d)

        cents = random.randint(10, 99)
        v_fin = cents / 100
        if abs(v_rep - v_fin) < 0.01:
            return None

        s_fin = f"0,{cents}"
        s1, s2 = (s_rep, s_fin)
        v1, v2 = (v_rep, v_fin)
        if random.choice([True, False]):
            s1, s2 = s2, s1
            v1, v2 = v2, v1

        q_str = rf"\text{{Wybierz znak: }} {s1} \text{{ \_\_\_ }} {s2}"
        c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        t2 = "="  # Trap (t2): znak równości przy nierównych liczbach

        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2)
        if result:
            return _with_messages(
                result,
                t1=(
                    "Okres rozwija się w nieskończoność — porównaj wartości dokładniej "
                    "niż tylko pierwsze cyfry po przecinku."
                ),
                t2=_MSG_NOT_EQUAL,
            )
    elif roll < 0.85:
        d1 = random.choice([3, 9])
        n1 = random.randint(1, d1 - 1)
        d2 = random.choice([3, 9])
        n2 = random.randint(1, d2 - 1)
        if n1 / d1 == n2 / d2:
            return None

        s1, v1 = _repeating_decimal_str(n1, d1)
        s2, v2 = _repeating_decimal_str(n2, d2)
        if random.choice([True, False]):
            s1, s2 = s2, s1
            v1, v2 = v2, v1

        q_str = rf"\text{{Wybierz znak: }} {s1} \text{{ \_\_\_ }} {s2}"
        c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        t2 = "="  # Trap (t2): znak równości przy nierównych liczbach

        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2)
        if result:
            return _with_messages(
                result,
                t1="Porównaj wartości ułamków — różne okresy oznaczają różne liczby.",
                t2="Gdy okresy są różne, liczby nie są równe — nie wybieraj znaku równości!",
            )
    else:
        digit = random.randint(1, 8)
        s_rep, v_rep = _repeating_decimal_str(digit, 9)
        s_fin = f"0,{digit}"
        v_fin = digit / 10

        s1, s2 = (s_fin, s_rep)
        v1, v2 = (v_fin, v_rep)
        if random.choice([True, False]):
            s1, s2 = s2, s1
            v1, v2 = v2, v1

        q_str = rf"\text{{Wybierz znak: }} {s1} \text{{ \_\_\_ }} {s2}"
        c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        t2 = "="  # Trap (t2): znak równości przy nierównych liczbach

        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2)
        if result:
            return _with_messages(
                result,
                t1=(
                    "0,(…) rozwija się dalej niż pierwsza cyfra po przecinku — "
                    "porównaj pełne wartości."
                ),
                t2=(
                    "Ułamek okresowy nie jest równy skróconemu zapisowi! "
                    f"Np. 0,({digit}) to 0,{digit}{digit}{digit}…, a nie 0,{digit}."
                ),
            )
