import random
from core.utils import build_problem_dict, fmt_dec


def dec_order_1():
    # Poziom 1: Podstawy (4 wariacje)
    # Loop up to 20 times to find a math combination that doesn't cause a trap collision
    for _ in range(20):
        template = random.choice(["add_mul", "mul_add", "sub_div", "div_sub"])

        if template == "add_mul":
            a, b, c = [round(random.randint(2, 6) * 0.1, 1) for _ in range(3)]
            q = f"{fmt_dec(a)} + {fmt_dec(b)} \\cdot {fmt_dec(c)}"
            ans = a + (b * c)
            t1, t2, t3 = (a + b) * c, a + b + c, (a * b) + c
        elif template == "mul_add":
            a, b, c = [round(random.randint(2, 6) * 0.1, 1) for _ in range(3)]
            q = f"{fmt_dec(a)} \\cdot {fmt_dec(b)} + {fmt_dec(c)}"
            ans = (a * b) + c
            t1, t2, t3 = a * (b + c), a + b + c, a * b * c
        elif template == "sub_div":
            c = round(random.randint(2, 5) * 0.1, 1)
            ans_div = round(random.randint(2, 5) * 0.1, 1)
            b = round(ans_div * c, 2)
            a = round(random.randint(10, 20) * 0.1, 1)
            q = f"{fmt_dec(a)} - {fmt_dec(b)} : {fmt_dec(c)}"
            ans = a - ans_div
            t1, t2, t3 = (a - b) / c if c != 0 else 0, a - b - c, a - (b * c)
        else:  # div_sub
            c = round(random.randint(2, 6) * 0.1, 1)
            ans_div = round(random.randint(2, 6) * 0.1, 1)
            a = round(ans_div * c, 2)
            upper_bound = max(1, int(round(ans_div * 10)) - 1)
            b = round(random.randint(1, upper_bound) * 0.1, 1)
            q = f"{fmt_dec(a)} : {fmt_dec(c)} - {fmt_dec(b)}"
            ans = ans_div - b
            t1, t2, t3 = a / (c - b) if c != b else a, ans_div + b, a - c - b

        problem = build_problem_dict(
            q, fmt_dec(ans), t1=fmt_dec(t1), t2=fmt_dec(t2), t3=fmt_dec(t3)
        )
        
        # If the dictionary built successfully (no collisions), return it.
        # Otherwise, the loop restarts and rolls new numbers.
        if problem is not None:
            return problem
            
    # Fallback in case of absolute mathematical gridlock
    raise RuntimeError("dec_order_1 failed to generate a valid problem without collisions after 20 attempts.")


def dec_order_2():
    # Poziom 2: Pojedyncze Nawiasy (4 wariacje)
    for _ in range(20):
        template = random.choice(["brack_mul", "mul_brack", "brack_div", "div_brack"])

        if template == "brack_mul":
            a, b, c = [round(random.randint(2, 6) * 0.1, 1) for _ in range(3)]
            q = f"({fmt_dec(a)} + {fmt_dec(b)}) \\cdot {fmt_dec(c)}"
            ans = (a + b) * c
            t1, t2, t3 = a + (b * c), (a + b) + c, a * b * c
        elif template == "mul_brack":
            a = round(random.randint(2, 6) * 0.1, 1)
            b = round(random.randint(5, 9) * 0.1, 1)
            c = round(random.randint(1, 4) * 0.1, 1)
            q = f"{fmt_dec(a)} \\cdot ({fmt_dec(b)} - {fmt_dec(c)})"
            ans = a * (b - c)
            t1, t2, t3 = (a * b) - c, a * (b + c), a + (b - c)
        elif template == "brack_div":
            c = round(random.randint(2, 5) * 0.1, 1)
            ans_div = random.randint(2, 6) 
            ab_sum = round(ans_div * c, 1)
            upper_bound = max(1, int(round(ab_sum * 10)) - 1)
            a = round(random.randint(1, upper_bound) * 0.1, 1)
            b = round(ab_sum - a, 1)
            q = f"({fmt_dec(a)} + {fmt_dec(b)}) : {fmt_dec(c)}"
            ans = ans_div
            t1, t2, t3 = a + (b / c), (a + b) * c, a + b - c
        else:  # div_brack
            ans_brack = round(random.randint(2, 5) * 0.1, 1)
            ans_div = round(random.randint(2, 5) * 0.1, 1)
            a = round(ans_div * ans_brack, 2)
            b = round(random.randint(10, 20) * 0.1, 1)
            c = round(b - ans_brack, 1)
            q = f"{fmt_dec(a)} : ({fmt_dec(b)} - {fmt_dec(c)})"
            ans = ans_div
            t1, t2, t3 = (a / b) - c, a / (b + c), a * (b - c)

        problem = build_problem_dict(
            q, fmt_dec(ans), t1=fmt_dec(t1), t2=fmt_dec(t2), t3=fmt_dec(t3)
        )
        
        if problem is not None:
            return problem
            
    raise RuntimeError("dec_order_2 failed to generate a valid problem without collisions after 20 attempts.")


def dec_order_3():
    # Poziom 3: Potęgowanie + Podstawy (4 wariacje)
    template = random.choice(["pow_add", "add_pow", "sub_pow", "pow_mul"])

    if template == "pow_add":
        a, b, c = [round(random.randint(2, 5) * 0.1, 1) for _ in range(3)]
        q = f"{fmt_dec(a)}^2 + {fmt_dec(b)} \\cdot {fmt_dec(c)}"
        ans = (a**2) + (b * c)
        t1, t2, t3 = ((a**2) + b) * c, (a * 2) + (b * c), a + (b * c)
    elif template == "add_pow":
        a, b = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)} + {fmt_dec(b)}^2"
        ans = a + (b**2)
        t1, t2, t3 = (a + b) ** 2, a + (b * 2), a * (b**2)
    elif template == "sub_pow":
        a = round(random.randint(10, 20) * 0.1, 1)
        b = round(random.randint(2, 5) * 0.1, 1)
        q = f"{fmt_dec(a)} - {fmt_dec(b)}^2"
        ans = a - (b**2)
        t1, t2, t3 = (a - b) ** 2, a - (b * 2), a + (b**2)
    else:  # pow_mul
        a, b = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)}^2 \\cdot {fmt_dec(b)}"
        ans = (a**2) * b
        t1, t2, t3 = (a * b) ** 2, (a * 2) * b, (a**2) + b

    return build_problem_dict(
        q, fmt_dec(ans), t1=fmt_dec(t1), t2=fmt_dec(t2), t3=fmt_dec(t3)
    )


def dec_order_4():
    # Poziom 4: Złożone Działania i Nawiasy (Boss 1)
    template = random.choice(["brack_mul_brack", "mul_add_mul"])

    if template == "brack_mul_brack":
        a, b = [round(random.randint(2, 6) * 0.1, 1) for _ in range(2)]
        c = round(random.randint(5, 9) * 0.1, 1)
        d = round(random.randint(1, 4) * 0.1, 1)
        q = f"({fmt_dec(a)} + {fmt_dec(b)}) \\cdot ({fmt_dec(c)} - {fmt_dec(d)})"
        ans = (a + b) * (c - d)
        t1, t2, t3 = a + b * c - d, (a + b) * c - d, a + b * (c - d)
    else:
        a, c = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        b, d = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)} \\cdot {fmt_dec(b)} + {fmt_dec(c)} \\cdot {fmt_dec(d)}"
        ans = (a * b) + (c * d)
        t1, t2, t3 = a * (b + c) * d, (a * b + c) * d, a + b + c + d

    return build_problem_dict(
        q, fmt_dec(ans), t1=fmt_dec(t1), t2=fmt_dec(t2), t3=fmt_dec(t3)
    )


def dec_order_5():
    # Poziom 5: Potęgowanie w Nawiasach
    template = random.choice(["brack_sq_sub", "sub_brack_sq"])

    if template == "brack_sq_sub":
        a, b, c = [round(random.randint(1, 4) * 0.1, 1) for _ in range(3)]
        q = f"({fmt_dec(a)} + {fmt_dec(b)})^2 - {fmt_dec(c)}"
        ans = ((a + b) ** 2) - c
        t1, t2, t3 = (a**2) + (b**2) - c, (a + b) * 2 - c, ((a + b) ** 2) + c
    else:
        a = round(random.randint(10, 20) * 0.1, 1)
        b, c = [round(random.randint(1, 4) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)} - ({fmt_dec(b)} + {fmt_dec(c)})^2"
        ans = a - ((b + c) ** 2)
        t1, t2, t3 = (a - (b + c)) ** 2, a - ((b + c) * 2), a - (b**2 + c**2)

    return build_problem_dict(
        q, fmt_dec(ans), t1=fmt_dec(t1), t2=fmt_dec(t2), t3=fmt_dec(t3)
    )


def dec_order_6():
    # Poziom 6: Ultimate Boss (Potęgi, Nawiasy i Mnożenie)
    a = round(random.randint(2, 4) * 0.1, 1)
    b, c = [round(random.randint(1, 3) * 0.1, 1) for _ in range(2)]
    d = round(random.randint(1, 5) * 0.1, 1)
    q = f"{fmt_dec(a)} \\cdot ({fmt_dec(b)} + {fmt_dec(c)})^2 - {fmt_dec(d)}"
    ans = a * ((b + c) ** 2) - d
    t1 = (a * (b + c)) ** 2 - d
    t2 = a * ((b + c) * 2) - d
    t3 = a * (b**2 + c**2) - d

    return build_problem_dict(
        q, fmt_dec(ans), t1=fmt_dec(t1), t2=fmt_dec(t2), t3=fmt_dec(t3)
    )
