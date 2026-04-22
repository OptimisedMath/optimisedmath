import random
from fractions import Fraction
from core.utils import build_problem_dict


def frac_ord_1():
    # Poziom 1: Podstawy bez nawiasów
    template = random.choice(["add_mul", "mul_add", "sub_mul"])
    dens = [2, 3, 4, 5]

    if template == "add_mul":
        a, b, c = [
            Fraction(random.randint(1, 3), random.choice(dens)) for _ in range(3)
        ]
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = a + (b * c)
        t1, t2, t3 = (a + b) * c, a + b + c, a * b * c
    elif template == "mul_add":
        a, b, c = [
            Fraction(random.randint(1, 3), random.choice(dens)) for _ in range(3)
        ]
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot \\frac{{{b.numerator}}}{{{b.denominator}}} + \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a * b) + c
        t1, t2, t3 = a * (b + c), a + b + c, a * b * c
    else:  # sub_mul
        b, c = [
            Fraction(random.randint(1, 3), random.choice([2, 3, 4])) for _ in range(2)
        ]
        a = (b * c) + Fraction(random.randint(1, 2), random.choice([2, 3]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} - \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = a - (b * c)
        t1, t2, t3 = (a - b) * c, a - b - c, a - b + c

    return build_problem_dict(
        q,
        f"{ans.numerator}/{ans.denominator}",
        t1=f"{t1.numerator}/{t1.denominator}",
        t2=f"{t2.numerator}/{t2.denominator}",
        t3=f"{t3.numerator}/{t3.denominator}",
    )


def frac_ord_2():
    # Poziom 2: Nawiasy
    template = random.choice(["brack_mul", "mul_brack", "div_brack"])

    if template == "brack_mul":
        a, b = [Fraction(1, random.choice([2, 3, 4])) for _ in range(2)]
        c = Fraction(random.randint(1, 3), random.choice([2, 3, 5]))
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}}) \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a + b) * c
        t1, t2, t3 = a + (b * c), (a + b) + c, a * b * c
    elif template == "mul_brack":
        a = Fraction(random.randint(1, 3), random.choice([2, 3]))
        b = Fraction(random.randint(3, 5), random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot (\\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}})"
        ans = a * (b - c)
        t1, t2, t3 = (a * b) - c, a * (b + c), a + (b - c)
    else:  # div_brack
        a = Fraction(random.randint(2, 5), random.choice([2, 3]))
        b = Fraction(random.randint(3, 5), random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} : (\\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}})"
        ans = a / (b - c)
        t1, t2, t3 = (a / b) - c, a / (b + c), a * (b - c)

    return build_problem_dict(
        q,
        f"{ans.numerator}/{ans.denominator}",
        t1=f"{t1.numerator}/{t1.denominator}",
        t2=f"{t2.numerator}/{t2.denominator}",
        t3=f"{t3.numerator}/{t3.denominator}",
    )


def frac_ord_3():
    # Poziom 3: Dwa zestawy działań
    template = random.choice(["brack_div_brack", "add_div_add"])

    if template == "brack_div_brack":
        a, b = Fraction(1, 2), Fraction(1, 3)
        c, d = Fraction(3, 4), Fraction(1, 4)
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}}) : (\\frac{{{c.numerator}}}{{{c.denominator}}} - \\frac{{{d.numerator}}}{{{d.denominator}}})"
        ans = (a + b) / (c - d)
        t1, t2, t3 = a + (b / c) - d, (a + b) * (c - d), (a + b) / c - d
    else:
        a, b = Fraction(1, 2), Fraction(3, 4)
        c, d = Fraction(1, 4), Fraction(1, 3)
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}} : \\frac{{{c.numerator}}}{{{c.denominator}}} + \\frac{{{d.numerator}}}{{{d.denominator}}}"
        ans = a + (b / c) + d
        t1, t2, t3 = (a + b) / (c + d), a + (b / c) * d, (a + b) / c + d

    return build_problem_dict(
        q,
        f"{ans.numerator}/{ans.denominator}",
        t1=f"{t1.numerator}/{t1.denominator}",
        t2=f"{t2.numerator}/{t2.denominator}",
        t3=f"{t3.numerator}/{t3.denominator}",
    )


def frac_ord_4():
    # Poziom 4: Potęgi
    template = random.choice(["pow_add", "sub_pow"])

    if template == "pow_add":
        a = Fraction(1, random.choice([2, 3, 4]))
        b, c = [Fraction(random.randint(1, 3), random.choice([2, 3])) for _ in range(2)]
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}})^2 + \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a**2) + (b * c)
        t1, t2, t3 = ((a**2) + b) * c, a + (b * c), (a * 2) + (b * c)
    else:
        b = Fraction(1, random.choice([2, 3, 4]))
        a = (b**2) + Fraction(random.randint(1, 2), random.choice([2, 3]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} - (\\frac{{{b.numerator}}}{{{b.denominator}}})^2"
        ans = a - (b**2)
        t1, t2, t3 = (a - b) ** 2, a - b, a - (b * 2)

    return build_problem_dict(
        q,
        f"{ans.numerator}/{ans.denominator}",
        t1=f"{t1.numerator}/{t1.denominator}",
        t2=f"{t2.numerator}/{t2.denominator}",
        t3=f"{t3.numerator}/{t3.denominator}",
    )


def frac_ord_5():
    # Poziom 5: Potęga Nawiasu
    template = random.choice(["brack_sq_sub", "mul_brack_sq"])

    if template == "brack_sq_sub":
        a, b = [Fraction(1, random.choice([2, 3])) for _ in range(2)]
        c = Fraction(1, random.choice([2, 3, 4]))
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}})^2 - \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = ((a + b) ** 2) - c
        if ans < 0:
            ans = abs(ans)
        t1, t2, t3 = (a**2 + b**2) - c, ((a + b) * 2) - c, ((a + b) ** 2) + c
    else:
        a = Fraction(1, random.choice([2, 3]))
        b = Fraction(3, random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot (\\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}})^2"
        ans = a * ((b - c) ** 2)
        t1, t2, t3 = (a * (b - c)) ** 2, a * ((b - c) * 2), a * (b**2 - c**2)

    return build_problem_dict(
        q,
        f"{ans.numerator}/{ans.denominator}",
        t1=f"{t1.numerator}/{t1.denominator}",
        t2=f"{t2.numerator}/{t2.denominator}",
        t3=f"{t3.numerator}/{t3.denominator}",
    )


def frac_ord_6():
    # Poziom 6: Ultimate Boss
    a, b = [Fraction(1, random.choice([2, 3])) for _ in range(2)]
    c = Fraction(1, random.choice([2, 3]))
    d = Fraction(1, random.choice([4, 5]))

    q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot (\\frac{{{b.numerator}}}{{{b.denominator}}} + \\frac{{{c.numerator}}}{{{c.denominator}}})^2 - \\frac{{{d.numerator}}}{{{d.denominator}}}"
    ans = a * ((b + c) ** 2) - d
    if ans < 0:
        ans = abs(ans)

    t1 = (a * (b + c)) ** 2 - d
    t2 = a * ((b + c) * 2) - d
    t3 = a * (b**2 + c**2) - d

    return build_problem_dict(
        q,
        f"{ans.numerator}/{ans.denominator}",
        t1=f"{t1.numerator}/{t1.denominator}",
        t2=f"{t2.numerator}/{t2.denominator}",
        t3=f"{t3.numerator}/{t3.denominator}",
    )
