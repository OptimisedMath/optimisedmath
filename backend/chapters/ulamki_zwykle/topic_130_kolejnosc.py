import random
from fractions import Fraction
from backend.core.utils import build_problem_dict, declares_traps


def _frac(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


@declares_traps(
    "adds_before_multiplying",
    "flattens_to_all_addition",
    "flattens_to_all_multiplication",
    "subtracts_before_multiplying",
    "flattens_to_all_subtraction",
    "replaces_multiplication_with_addition",
)
def frac_ord_1() -> dict | None:
    """Kolejność Podstawowa (poziom 1)."""
    # Poziom 1: Podstawy bez nawiasów
    template = random.choice(["add_mul", "mul_add", "sub_mul"])
    dens = [2, 3, 4, 5]

    if template == "add_mul":
        a, b, c = [
            Fraction(random.randint(1, 3), random.choice(dens)) for _ in range(3)
        ]
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = a + (b * c)
        traps = {
            "adds_before_multiplying": (a + b) * c,
            "flattens_to_all_addition": a + b + c,
            "flattens_to_all_multiplication": a * b * c,
        }
    elif template == "mul_add":
        a, b, c = [
            Fraction(random.randint(1, 3), random.choice(dens)) for _ in range(3)
        ]
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot \\frac{{{b.numerator}}}{{{b.denominator}}} + \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a * b) + c
        traps = {
            "adds_before_multiplying": a * (b + c),
            "flattens_to_all_addition": a + b + c,
            "flattens_to_all_multiplication": a * b * c,
        }
    else:  # sub_mul
        b, c = [
            Fraction(random.randint(1, 3), random.choice([2, 3, 4])) for _ in range(2)
        ]
        a = (b * c) + Fraction(random.randint(1, 2), random.choice([2, 3]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} - \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = a - (b * c)
        traps = {
            "subtracts_before_multiplying": (a - b) * c,
            "flattens_to_all_subtraction": a - b - c,
            "replaces_multiplication_with_addition": a - b + c,
        }

    problem = build_problem_dict(
        q,
        _frac(ans),
        traps={slug: _frac(value) for slug, value in traps.items()},
        parameters={"a": _frac(a), "b": _frac(b), "c": _frac(c)},
    )
    if problem:
        return problem


@declares_traps(
    "ignores_the_brackets",
    "replaces_multiplication_with_addition",
    "flattens_to_all_multiplication",
    "flips_the_sign_inside_the_bracket",
    "replaces_division_with_multiplication",
)
def frac_ord_2() -> dict | None:
    """Siła Nawiasów (poziom 2)."""
    # Poziom 2: Nawiasy
    template = random.choice(["brack_mul", "mul_brack", "div_brack"])

    if template == "brack_mul":
        a, b = [Fraction(1, random.choice([2, 3, 4])) for _ in range(2)]
        c = Fraction(random.randint(1, 3), random.choice([2, 3, 5]))
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}}) \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a + b) * c
        traps = {
            "ignores_the_brackets": a + (b * c),
            "replaces_multiplication_with_addition": (a + b) + c,
            "flattens_to_all_multiplication": a * b * c,
        }
    elif template == "mul_brack":
        a = Fraction(random.randint(1, 3), random.choice([2, 3]))
        b = Fraction(random.randint(3, 5), random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot (\\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}})"
        ans = a * (b - c)
        traps = {
            "ignores_the_brackets": (a * b) - c,
            "flips_the_sign_inside_the_bracket": a * (b + c),
            "replaces_multiplication_with_addition": a + (b - c),
        }
    else:  # div_brack
        a = Fraction(random.randint(2, 5), random.choice([2, 3]))
        b = Fraction(random.randint(3, 5), random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} : (\\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}})"
        ans = a / (b - c)
        traps = {
            "ignores_the_brackets": (a / b) - c,
            "flips_the_sign_inside_the_bracket": a / (b + c),
            "replaces_division_with_multiplication": a * (b - c),
        }

    problem = build_problem_dict(
        q,
        _frac(ans),
        traps={slug: _frac(value) for slug, value in traps.items()},
        parameters={"a": _frac(a), "b": _frac(b), "c": _frac(c)},
    )
    if problem:
        return problem


@declares_traps(
    "ignores_the_brackets",
    "replaces_division_with_multiplication",
    "ignores_the_second_bracket",
    "invents_brackets_around_both_additions",
    "replaces_addition_with_multiplication",
    "invents_a_bracket_around_the_first_addition",
)
def frac_ord_3() -> dict | None:
    """Dwa Zestawy (poziom 3)."""
    # Poziom 3: Dwa zestawy działań
    template = random.choice(["brack_div_brack", "add_div_add"])

    if template == "brack_div_brack":
        a = Fraction(1, random.choice([2, 3, 4]))
        b = Fraction(1, random.choice([2, 3, 4]))
        c = Fraction(random.randint(2, 4), random.choice([4, 5, 6]))
        d = Fraction(1, random.choice([3, 4, 5]))
        if c <= d:
            return None
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}}) : (\\frac{{{c.numerator}}}{{{c.denominator}}} - \\frac{{{d.numerator}}}{{{d.denominator}}})"
        ans = (a + b) / (c - d)
        traps = {
            "ignores_the_brackets": a + (b / c) - d,
            "replaces_division_with_multiplication": (a + b) * (c - d),
            "ignores_the_second_bracket": (a + b) / c - d,
        }
    else:
        a = Fraction(1, random.choice([2, 3, 4]))
        b = Fraction(random.randint(2, 3), random.choice([4, 5]))
        c = Fraction(1, random.choice([3, 4, 5]))
        d = Fraction(1, random.choice([2, 3, 4]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}} : \\frac{{{c.numerator}}}{{{c.denominator}}} + \\frac{{{d.numerator}}}{{{d.denominator}}}"
        ans = a + (b / c) + d
        traps = {
            "invents_brackets_around_both_additions": (a + b) / (c + d),
            "replaces_addition_with_multiplication": a + (b / c) * d,
            "invents_a_bracket_around_the_first_addition": (a + b) / c + d,
        }

    problem = build_problem_dict(
        q,
        _frac(ans),
        traps={slug: _frac(value) for slug, value in traps.items()},
        parameters={"a": _frac(a), "b": _frac(b), "c": _frac(c), "d": _frac(d)},
    )

    if problem:
        return problem


@declares_traps(
    "adds_before_multiplying",
    "ignores_the_exponent",
    "multiplies_by_the_exponent",
    "subtracts_before_squaring",
)
def frac_ord_4() -> dict | None:
    """Potęgi i Ułamki (poziom 4)."""
    # Poziom 4: Potęgi
    template = random.choice(["pow_add", "sub_pow"])

    if template == "pow_add":
        a = Fraction(1, random.choice([2, 3, 4]))
        b, c = [Fraction(random.randint(1, 3), random.choice([2, 3])) for _ in range(2)]
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}})^2 + \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a**2) + (b * c)
        traps = {
            "adds_before_multiplying": ((a**2) + b) * c,
            "ignores_the_exponent": a + (b * c),
            "multiplies_by_the_exponent": (a * 2) + (b * c),
        }
        instance_parameters = {"a": _frac(a), "b": _frac(b), "c": _frac(c)}
    else:
        b = Fraction(1, random.choice([2, 3, 4]))
        a = (b**2) + Fraction(random.randint(1, 2), random.choice([2, 3]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} - (\\frac{{{b.numerator}}}{{{b.denominator}}})^2"
        ans = a - (b**2)
        traps = {
            "subtracts_before_squaring": (a - b) ** 2,
            "ignores_the_exponent": a - b,
            "multiplies_by_the_exponent": a - (b * 2),
        }
        instance_parameters = {"a": _frac(a), "b": _frac(b)}

    problem = build_problem_dict(
        q,
        _frac(ans),
        traps={slug: _frac(value) for slug, value in traps.items()},
        parameters=instance_parameters,
    )
    if problem:
        return problem


@declares_traps(
    "squares_the_bracket_terms_separately",
    "multiplies_by_the_exponent",
    "flips_the_final_sign",
    "multiplies_before_squaring",
)
def frac_ord_5() -> dict | None:
    """Potęgowanie Nawiasu (poziom 5)."""
    # Poziom 5: Potęga Nawiasu
    template = random.choice(["brack_sq_sub", "mul_brack_sq"])

    if template == "brack_sq_sub":
        a, b = [Fraction(1, random.choice([2, 3])) for _ in range(2)]
        c = Fraction(1, random.choice([2, 3, 4]))
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}})^2 - \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = ((a + b) ** 2) - c
        if ans < 0:
            return None
        traps = {
            "squares_the_bracket_terms_separately": (a**2 + b**2) - c,
            "multiplies_by_the_exponent": ((a + b) * 2) - c,
            "flips_the_final_sign": ((a + b) ** 2) + c,
        }
    else:
        a = Fraction(1, random.choice([2, 3]))
        b = Fraction(3, random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot (\\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}})^2"
        ans = a * ((b - c) ** 2)
        traps = {
            "multiplies_before_squaring": (a * (b - c)) ** 2,
            "multiplies_by_the_exponent": a * ((b - c) * 2),
            "squares_the_bracket_terms_separately": a * (b**2 - c**2),
        }

    problem = build_problem_dict(
        q,
        _frac(ans),
        traps={slug: _frac(value) for slug, value in traps.items()},
        parameters={"a": _frac(a), "b": _frac(b), "c": _frac(c)},
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_before_squaring",
    "multiplies_by_the_exponent",
    "squares_the_bracket_terms_separately",
)
def frac_ord_6() -> dict | None:
    """Boss Level (poziom 6)."""
    # Poziom 6: Ultimate Boss
    a, b = [Fraction(1, random.choice([2, 3])) for _ in range(2)]
    c = Fraction(1, random.choice([2, 3]))
    d = Fraction(1, random.choice([4, 5]))

    q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot (\\frac{{{b.numerator}}}{{{b.denominator}}} + \\frac{{{c.numerator}}}{{{c.denominator}}})^2 - \\frac{{{d.numerator}}}{{{d.denominator}}}"
    ans = a * ((b + c) ** 2) - d
    if ans < 0:
        return None

    problem = build_problem_dict(
        q,
        _frac(ans),
        traps={
            "multiplies_before_squaring": _frac((a * (b + c)) ** 2 - d),
            "multiplies_by_the_exponent": _frac(a * ((b + c) * 2) - d),
            "squares_the_bracket_terms_separately": _frac(a * (b**2 + c**2) - d),
        },
        parameters={"a": _frac(a), "b": _frac(b), "c": _frac(c), "d": _frac(d)},
    )
    if problem:
        return problem
