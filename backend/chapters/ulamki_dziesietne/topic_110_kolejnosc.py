import random
from backend.core.utils import build_problem_dict, declares_traps, fmt_dec


@declares_traps(
    "adds_before_multiplying",
    "flattens_to_all_addition",
    "multiplies_the_wrong_pair",
    "flattens_to_all_multiplication",
    "subtracts_before_dividing",
    "flattens_to_all_subtraction",
    "replaces_division_with_multiplication",
    "replaces_subtraction_with_addition",
)
def dec_order_1() -> dict | None:
    """Kolejność Podstawowa (poziom 1)."""
    # Poziom 1: Podstawy (4 wariacje)
    # Loop up to 20 times to find a math combination that doesn't cause a trap collision
    for _ in range(20):
        template = random.choice(["add_mul", "mul_add", "sub_div", "div_sub"])

        if template == "add_mul":
            a, b, c = [round(random.randint(2, 6) * 0.1, 1) for _ in range(3)]
            q = f"{fmt_dec(a)} + {fmt_dec(b)} \\cdot {fmt_dec(c)}"
            ans = a + (b * c)
            traps = {
                "adds_before_multiplying": (a + b) * c,
                "flattens_to_all_addition": a + b + c,
                "multiplies_the_wrong_pair": (a * b) + c,
            }
        elif template == "mul_add":
            a, b, c = [round(random.randint(2, 6) * 0.1, 1) for _ in range(3)]
            q = f"{fmt_dec(a)} \\cdot {fmt_dec(b)} + {fmt_dec(c)}"
            ans = (a * b) + c
            traps = {
                "adds_before_multiplying": a * (b + c),
                "flattens_to_all_addition": a + b + c,
                "flattens_to_all_multiplication": a * b * c,
            }
        elif template == "sub_div":
            c = round(random.randint(2, 5) * 0.1, 1)
            ans_div = round(random.randint(2, 5) * 0.1, 1)
            b = round(ans_div * c, 2)
            a = round(random.randint(10, 20) * 0.1, 1)
            q = f"{fmt_dec(a)} - {fmt_dec(b)} : {fmt_dec(c)}"
            ans = a - ans_div
            traps = {
                "subtracts_before_dividing": (a - b) / c,
                "flattens_to_all_subtraction": a - b - c,
                "replaces_division_with_multiplication": a - (b * c),
            }
        else:  # div_sub
            c = round(random.randint(2, 6) * 0.1, 1)
            ans_div = round(random.randint(2, 6) * 0.1, 1)
            a = round(ans_div * c, 2)
            upper_bound = max(1, int(round(ans_div * 10)) - 1)
            b = round(random.randint(1, upper_bound) * 0.1, 1)
            q = f"{fmt_dec(a)} : {fmt_dec(c)} - {fmt_dec(b)}"
            ans = ans_div - b
            traps = {
                "subtracts_before_dividing": a / (c - b) if c != b else a,
                "replaces_subtraction_with_addition": ans_div + b,
                "flattens_to_all_subtraction": a - c - b,
            }

        problem = build_problem_dict(
            q,
            fmt_dec(ans),
            traps={slug: fmt_dec(value) for slug, value in traps.items()},
            parameters={"a": a, "b": b, "c": c},
        )

        # If the dictionary built successfully (no collisions), return it.
        # Otherwise, the loop restarts and rolls new numbers.
        if problem is not None:
            return problem

    # Fallback in case of absolute mathematical gridlock
    raise RuntimeError(
        "dec_order_1 failed to generate a valid problem without collisions after 20 attempts."
    )


@declares_traps(
    "ignores_the_brackets",
    "replaces_multiplication_with_addition",
    "flattens_to_all_multiplication",
    "flips_the_sign_inside_the_bracket",
    "replaces_division_with_multiplication",
    "replaces_division_with_subtraction",
)
def dec_order_2() -> dict | None:
    """Pojedyncze Nawiasy (poziom 2)."""
    # Poziom 2: Pojedyncze Nawiasy (4 wariacje)
    for _ in range(20):
        template = random.choice(["brack_mul", "mul_brack", "brack_div", "div_brack"])

        if template == "brack_mul":
            a, b, c = [round(random.randint(2, 6) * 0.1, 1) for _ in range(3)]
            q = f"({fmt_dec(a)} + {fmt_dec(b)}) \\cdot {fmt_dec(c)}"
            ans = (a + b) * c
            traps = {
                "ignores_the_brackets": a + (b * c),
                "replaces_multiplication_with_addition": (a + b) + c,
                "flattens_to_all_multiplication": a * b * c,
            }
        elif template == "mul_brack":
            a = round(random.randint(2, 6) * 0.1, 1)
            b = round(random.randint(5, 9) * 0.1, 1)
            c = round(random.randint(1, 4) * 0.1, 1)
            q = f"{fmt_dec(a)} \\cdot ({fmt_dec(b)} - {fmt_dec(c)})"
            ans = a * (b - c)
            traps = {
                "ignores_the_brackets": (a * b) - c,
                "flips_the_sign_inside_the_bracket": a * (b + c),
                "replaces_multiplication_with_addition": a + (b - c),
            }
        elif template == "brack_div":
            c = round(random.randint(2, 5) * 0.1, 1)
            ans_div = random.randint(2, 6)
            ab_sum = round(ans_div * c, 1)
            upper_bound = max(1, int(round(ab_sum * 10)) - 1)
            a = round(random.randint(1, upper_bound) * 0.1, 1)
            b = round(ab_sum - a, 1)
            q = f"({fmt_dec(a)} + {fmt_dec(b)}) : {fmt_dec(c)}"
            ans = ans_div
            traps = {
                "ignores_the_brackets": a + (b / c),
                "replaces_division_with_multiplication": (a + b) * c,
                "replaces_division_with_subtraction": a + b - c,
            }
        else:  # div_brack
            ans_brack = round(random.randint(2, 5) * 0.1, 1)
            ans_div = round(random.randint(2, 5) * 0.1, 1)
            a = round(ans_div * ans_brack, 2)
            b = round(random.randint(10, 20) * 0.1, 1)
            c = round(b - ans_brack, 1)
            q = f"{fmt_dec(a)} : ({fmt_dec(b)} - {fmt_dec(c)})"
            ans = ans_div
            traps = {
                "ignores_the_brackets": (a / b) - c,
                "flips_the_sign_inside_the_bracket": a / (b + c),
                "replaces_division_with_multiplication": a * (b - c),
            }

        problem = build_problem_dict(
            q,
            fmt_dec(ans),
            traps={slug: fmt_dec(value) for slug, value in traps.items()},
            parameters={"a": a, "b": b, "c": c},
        )

        if problem is not None:
            return problem

    raise RuntimeError(
        "dec_order_2 failed to generate a valid problem without collisions after 20 attempts."
    )


@declares_traps(
    "adds_before_multiplying",
    "multiplies_by_the_exponent",
    "ignores_the_exponent",
    "adds_before_squaring",
    "replaces_addition_with_multiplication",
    "subtracts_before_squaring",
    "flips_the_final_sign",
    "multiplies_before_squaring",
    "replaces_multiplication_with_addition",
)
def dec_order_3() -> dict | None:
    """Potęgi i Podstawy (poziom 3)."""
    # Poziom 3: Potęgowanie + Podstawy (4 wariacje)
    template = random.choice(["pow_add", "add_pow", "sub_pow", "pow_mul"])

    parameters = {}
    if template == "pow_add":
        a, b, c = [round(random.randint(2, 5) * 0.1, 1) for _ in range(3)]
        q = f"{fmt_dec(a)}^2 + {fmt_dec(b)} \\cdot {fmt_dec(c)}"
        ans = (a**2) + (b * c)
        traps = {
            "adds_before_multiplying": ((a**2) + b) * c,
            "multiplies_by_the_exponent": (a * 2) + (b * c),
            "ignores_the_exponent": a + (b * c),
        }
        parameters = {"a": a, "b": b, "c": c}
    elif template == "add_pow":
        a, b = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)} + {fmt_dec(b)}^2"
        ans = a + (b**2)
        traps = {
            "adds_before_squaring": (a + b) ** 2,
            "multiplies_by_the_exponent": a + (b * 2),
            "replaces_addition_with_multiplication": a * (b**2),
        }
        parameters = {"a": a, "b": b}
    elif template == "sub_pow":
        a = round(random.randint(10, 20) * 0.1, 1)
        b = round(random.randint(2, 5) * 0.1, 1)
        q = f"{fmt_dec(a)} - {fmt_dec(b)}^2"
        ans = a - (b**2)
        traps = {
            "subtracts_before_squaring": (a - b) ** 2,
            "multiplies_by_the_exponent": a - (b * 2),
            "flips_the_final_sign": a + (b**2),
        }
        parameters = {"a": a, "b": b}
    else:  # pow_mul
        a, b = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)}^2 \\cdot {fmt_dec(b)}"
        ans = (a**2) * b
        traps = {
            "multiplies_before_squaring": (a * b) ** 2,
            "multiplies_by_the_exponent": (a * 2) * b,
            "replaces_multiplication_with_addition": (a**2) + b,
        }
        parameters = {"a": a, "b": b}

    problem = build_problem_dict(
        q,
        fmt_dec(ans),
        traps={slug: fmt_dec(value) for slug, value in traps.items()},
        parameters=parameters,
    )
    if problem:
        return problem


@declares_traps(
    "ignores_both_brackets",
    "ignores_the_second_bracket",
    "ignores_the_first_bracket",
    "invents_a_bracket_around_the_addition",
    "invents_a_bracket_around_the_left_side",
    "flattens_to_all_addition",
)
def dec_order_4() -> dict | None:
    """Złożone Działania (poziom 4)."""
    # Poziom 4: Złożone Działania i Nawiasy (Boss 1)
    template = random.choice(["brack_mul_brack", "mul_add_mul"])

    if template == "brack_mul_brack":
        a, b = [round(random.randint(2, 6) * 0.1, 1) for _ in range(2)]
        c = round(random.randint(5, 9) * 0.1, 1)
        d = round(random.randint(1, 4) * 0.1, 1)
        q = f"({fmt_dec(a)} + {fmt_dec(b)}) \\cdot ({fmt_dec(c)} - {fmt_dec(d)})"
        ans = (a + b) * (c - d)
        traps = {
            "ignores_both_brackets": a + b * c - d,
            "ignores_the_second_bracket": (a + b) * c - d,
            "ignores_the_first_bracket": a + b * (c - d),
        }
    else:
        a, c = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        b, d = [round(random.randint(2, 5) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)} \\cdot {fmt_dec(b)} + {fmt_dec(c)} \\cdot {fmt_dec(d)}"
        ans = (a * b) + (c * d)
        traps = {
            "invents_a_bracket_around_the_addition": a * (b + c) * d,
            "invents_a_bracket_around_the_left_side": (a * b + c) * d,
            "flattens_to_all_addition": a + b + c + d,
        }

    problem = build_problem_dict(
        q,
        fmt_dec(ans),
        traps={slug: fmt_dec(value) for slug, value in traps.items()},
        parameters={"a": a, "b": b, "c": c, "d": d},
    )
    if problem:
        return problem


@declares_traps(
    "squares_the_bracket_terms_separately",
    "multiplies_by_the_exponent",
    "flips_the_final_sign",
    "subtracts_before_squaring",
)
def dec_order_5() -> dict | None:
    """Potęgowanie Nawiasu (poziom 5)."""
    # Poziom 5: Potęgowanie w Nawiasach
    template = random.choice(["brack_sq_sub", "sub_brack_sq"])

    if template == "brack_sq_sub":
        a, b, c = [round(random.randint(1, 4) * 0.1, 1) for _ in range(3)]
        q = f"({fmt_dec(a)} + {fmt_dec(b)})^2 - {fmt_dec(c)}"
        ans = ((a + b) ** 2) - c
        traps = {
            "squares_the_bracket_terms_separately": (a**2) + (b**2) - c,
            "multiplies_by_the_exponent": (a + b) * 2 - c,
            "flips_the_final_sign": ((a + b) ** 2) + c,
        }
    else:
        a = round(random.randint(10, 20) * 0.1, 1)
        b, c = [round(random.randint(1, 4) * 0.1, 1) for _ in range(2)]
        q = f"{fmt_dec(a)} - ({fmt_dec(b)} + {fmt_dec(c)})^2"
        ans = a - ((b + c) ** 2)
        traps = {
            "subtracts_before_squaring": (a - (b + c)) ** 2,
            "multiplies_by_the_exponent": a - ((b + c) * 2),
            "squares_the_bracket_terms_separately": a - (b**2 + c**2),
        }

    problem = build_problem_dict(
        q,
        fmt_dec(ans),
        traps={slug: fmt_dec(value) for slug, value in traps.items()},
        parameters={"a": a, "b": b, "c": c},
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_before_squaring",
    "multiplies_by_the_exponent",
    "squares_the_bracket_terms_separately",
)
def dec_order_6() -> dict | None:
    """Boss Level (poziom 6)."""
    # Poziom 6: Ultimate Boss (Potęgi, Nawiasy i Mnożenie)
    a = round(random.randint(2, 4) * 0.1, 1)
    b, c = [round(random.randint(1, 3) * 0.1, 1) for _ in range(2)]
    d = round(random.randint(1, 5) * 0.1, 1)
    q = f"{fmt_dec(a)} \\cdot ({fmt_dec(b)} + {fmt_dec(c)})^2 - {fmt_dec(d)}"
    ans = a * ((b + c) ** 2) - d

    traps = {
        "multiplies_before_squaring": (a * (b + c)) ** 2 - d,
        "multiplies_by_the_exponent": a * ((b + c) * 2) - d,
        "squares_the_bracket_terms_separately": a * (b**2 + c**2) - d,
    }

    problem = build_problem_dict(
        q,
        fmt_dec(ans),
        traps={slug: fmt_dec(value) for slug, value in traps.items()},
        parameters={"a": a, "b": b, "c": c, "d": d},
    )
    if problem:
        return problem
