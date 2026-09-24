"""Ułamki Zwykłe — Kolejność wykonywania działań: generatory Problemów."""

import random
from fractions import Fraction
from backend.core.utils import build_problem_dict, declares_traps
from backend.expression import parse, render, render_value


def _frac(value: Fraction) -> str:
    """Format a Fraction as the improper `n/d` string the ASCII `expression` and
    the named operand parameters carry."""
    return f"{value.numerator}/{value.denominator}"


def _option(value: Fraction) -> str:
    """Format a Fraction as an option: a LaTeX `\\frac{n}{d}`, or a bare integer
    when it's whole, per ADR-0017 — the same rule `render` draws every leaf in."""
    return render_value(value, "fraction")


def _params(expr: str, **operands: Fraction) -> dict[str, int | float | str]:
    """The Problem's `parameters`: every operand as `n/d`, plus the ASCII `expr`
    itself as `expression`."""
    parameters: dict[str, int | float | str] = {
        name: _frac(value) for name, value in operands.items()
    }
    parameters["expression"] = expr
    return parameters


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
        expr = f"{_frac(a)} + {_frac(b)} * {_frac(c)}"
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
        expr = f"{_frac(a)} * {_frac(b)} + {_frac(c)}"
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
        expr = f"{_frac(a)} - {_frac(b)} * {_frac(c)}"
        ans = a - (b * c)
        traps = {
            "subtracts_before_multiplying": (a - b) * c,
            "flattens_to_all_subtraction": a - b - c,
            "replaces_multiplication_with_addition": a - b + c,
        }
        # Ułamki Zwykłe forbids negative options (ADR-0007), so a draw where
        # all three Traps go negative offers none of them — the template
        # would test nothing (#272).
        if all(value < 0 for value in traps.values()):
            return None

    problem = build_problem_dict(
        render(parse(expr)),
        _option(ans),
        traps={slug: _option(value) for slug, value in traps.items()},
        parameters=_params(expr, a=a, b=b, c=c),
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
        expr = f"({_frac(a)} + {_frac(b)}) * {_frac(c)}"
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
        expr = f"{_frac(a)} * ({_frac(b)} - {_frac(c)})"
        ans = a * (b - c)
        traps = {
            "ignores_the_brackets": (a * b) - c,
            "flips_the_sign_inside_the_bracket": a * (b + c),
            "replaces_multiplication_with_addition": a + (b - c),
            "flattens_to_all_multiplication": a * b * c,
        }
    else:  # div_brack
        a = Fraction(random.randint(2, 5), random.choice([2, 3]))
        b = Fraction(random.randint(3, 5), random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        expr = f"{_frac(a)} : ({_frac(b)} - {_frac(c)})"
        ans = a / (b - c)
        traps = {
            "ignores_the_brackets": (a / b) - c,
            "flips_the_sign_inside_the_bracket": a / (b + c),
            "replaces_division_with_multiplication": a * (b - c),
        }

    problem = build_problem_dict(
        render(parse(expr)),
        _option(ans),
        traps={slug: _option(value) for slug, value in traps.items()},
        parameters=_params(expr, a=a, b=b, c=c),
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
        expr = f"({_frac(a)} + {_frac(b)}) : ({_frac(c)} - {_frac(d)})"
        ans = (a + b) / (c - d)
        traps = {
            "ignores_the_brackets": a + (b / c) - d,
            "ignores_the_second_bracket": (a + b) / c - d,
            "replaces_division_with_multiplication": (a + b) * (c - d),
        }
    else:
        a = Fraction(1, random.choice([2, 3, 4]))
        b = Fraction(random.randint(2, 3), random.choice([4, 5]))
        c = Fraction(1, random.choice([3, 4, 5]))
        d = Fraction(1, random.choice([2, 3, 4]))
        expr = f"{_frac(a)} + {_frac(b)} : {_frac(c)} + {_frac(d)}"
        ans = a + (b / c) + d
        traps = {
            "invents_brackets_around_both_additions": (a + b) / (c + d),
            "invents_a_bracket_around_the_first_addition": (a + b) / c + d,
            "replaces_addition_with_multiplication": a + (b / c) * d,
        }

    problem = build_problem_dict(
        render(parse(expr)),
        _option(ans),
        traps={slug: _option(value) for slug, value in traps.items()},
        parameters=_params(expr, a=a, b=b, c=c, d=d),
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
        expr = f"({_frac(a)})^2 + {_frac(b)} * {_frac(c)}"
        ans = (a**2) + (b * c)
        traps = {
            "adds_before_multiplying": ((a**2) + b) * c,
            "multiplies_by_the_exponent": (a * 2) + (b * c),
            "ignores_the_exponent": a + (b * c),
        }
        instance_parameters = _params(expr, a=a, b=b, c=c)
    else:
        b = Fraction(1, random.choice([2, 3, 4]))
        a = (b**2) + Fraction(random.randint(1, 2), random.choice([2, 3]))
        expr = f"{_frac(a)} - ({_frac(b)})^2"
        ans = a - (b**2)
        traps = {
            "subtracts_before_squaring": (a - b) ** 2,
            "multiplies_by_the_exponent": a - (b * 2),
            "ignores_the_exponent": a - b,
        }
        instance_parameters = _params(expr, a=a, b=b)

    problem = build_problem_dict(
        render(parse(expr)),
        _option(ans),
        traps={slug: _option(value) for slug, value in traps.items()},
        parameters=instance_parameters,
    )
    if problem:
        return problem


@declares_traps(
    "squares_the_bracket_terms_separately",
    "multiplies_by_the_exponent",
    "flips_the_final_sign",
    "multiplies_before_squaring",
    "subtracts_before_squaring",
)
def frac_ord_5() -> dict | None:
    """Potęgowanie Nawiasu (poziom 5)."""
    # Poziom 5: Potęga Nawiasu
    template = random.choice(["brack_sq_sub", "mul_brack_sq"])

    if template == "brack_sq_sub":
        a, b = [Fraction(1, random.choice([2, 3])) for _ in range(2)]
        c = Fraction(1, random.choice([2, 3, 4, 5]))
        expr = f"({_frac(a)} + {_frac(b)})^2 - {_frac(c)}"
        ans = ((a + b) ** 2) - c
        if ans < 0:
            return None
        traps = {
            "squares_the_bracket_terms_separately": (a**2 + b**2) - c,
            "multiplies_by_the_exponent": ((a + b) * 2) - c,
            "flips_the_final_sign": ((a + b) ** 2) + c,
            "subtracts_before_squaring": (a + b - c) ** 2,
        }
    else:
        a = Fraction(1, random.choice([2, 3]))
        b = Fraction(3, random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5, 6]))
        expr = f"{_frac(a)} * ({_frac(b)} - {_frac(c)})^2"
        ans = a * ((b - c) ** 2)
        traps = {
            "multiplies_before_squaring": (a * (b - c)) ** 2,
            "multiplies_by_the_exponent": a * ((b - c) * 2),
            "squares_the_bracket_terms_separately": a * (b**2 - c**2),
        }

    problem = build_problem_dict(
        render(parse(expr)),
        _option(ans),
        traps={slug: _option(value) for slug, value in traps.items()},
        parameters=_params(expr, a=a, b=b, c=c),
    )
    if problem:
        return problem


@declares_traps(
    "multiplies_before_squaring",
    "multiplies_by_the_exponent",
    "squares_the_bracket_terms_separately",
)
def frac_ord_6() -> dict | None:
    """Wszystko Naraz (poziom 6)."""
    # Poziom 6: nawias, potęgowanie, mnożenie i odejmowanie w jednym działaniu
    # A non-unit `a` and a small `d` are what keep every Trap positive, as
    # ADR-0007 requires; on unit fractions two of the three were always negative.
    a = random.choice([Fraction(2, 3), Fraction(3, 4)])
    b = random.choice([Fraction(1, 2), Fraction(1, 3)])
    c = random.choice([Fraction(1, 2), Fraction(1, 3)])
    d = random.choice([Fraction(1, 8), Fraction(1, 9), Fraction(1, 10)])

    expr = f"{_frac(a)} * ({_frac(b)} + {_frac(c)})^2 - {_frac(d)}"
    ans = a * ((b + c) ** 2) - d
    if ans < 0:
        return None

    problem = build_problem_dict(
        render(parse(expr)),
        _option(ans),
        traps={
            "multiplies_before_squaring": _option((a * (b + c)) ** 2 - d),
            "multiplies_by_the_exponent": _option(a * ((b + c) * 2) - d),
            "squares_the_bracket_terms_separately": _option(a * (b**2 + c**2) - d),
        },
        parameters=_params(expr, a=a, b=b, c=c, d=d),
    )
    if problem:
        return problem
