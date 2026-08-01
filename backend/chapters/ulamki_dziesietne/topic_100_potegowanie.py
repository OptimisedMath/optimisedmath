import random
from backend.core.utils import build_problem_dict, fmt_dec


def dec_pow_1() -> dict | None:
    """Kwadrat ułamka dziesiętnego (poziom 1)."""
    v = random.randint(2, 9) / 10
    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^2"

    c_str = fmt_dec(round(v**2, 2))

    t1 = fmt_dec(round(v * 2, 1))  # Trap (t1): Mnożysz to przez 2, a to jest kwadrat (do potęgi drugiej)

    t2 = fmt_dec(round(v * 10) ** 2)  # Trap (t2): Błąd w stawianiu przecinka
    t3 = fmt_dec(round(v**2 + 0.01, 2))  # Trap (t3): Zapomniałeś zera z przodu

    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3)
    if result:
        return result
