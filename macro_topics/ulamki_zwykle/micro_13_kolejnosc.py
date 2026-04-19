import random
from fractions import Fraction
from core.utils import build_problem_dict

def frac_ord_1():
    # Poziom 1: Bez nawiasów
    template = random.choice(["add_mul", "mul_sub"])
    dens = [2, 3, 4, 5]
    
    if template == "add_mul":
        a = Fraction(random.randint(1, 3), random.choice(dens))
        b = Fraction(random.randint(1, 3), random.choice(dens))
        c = Fraction(random.randint(1, 3), random.choice(dens))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = a + (b * c)
        trap1 = (a + b) * c
        
    else: # mul_sub
        a = Fraction(random.randint(2, 4), random.choice(dens))
        b = Fraction(random.randint(2, 4), random.choice(dens))
        c = Fraction(1, random.choice([4, 5, 6]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} \\cdot \\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a * b) - c
        if ans < 0: ans = abs(ans)
        trap1 = a * (b - c)
        
    return build_problem_dict(q, f"{ans.numerator}/{ans.denominator}", t1=f"{trap1.numerator}/{trap1.denominator}")

def frac_ord_2():
    # Poziom 2: Nawiasy
    template = random.choice(["brack_mul", "div_brack"])
    
    if template == "brack_mul":
        a = Fraction(1, random.choice([2, 3, 4]))
        b = Fraction(1, random.choice([2, 3, 4]))
        c = Fraction(random.randint(1, 3), random.choice([2, 3, 5]))
        q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}}) \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
        ans = (a + b) * c
        trap1 = a + (b * c)
        
    else: # div_brack
        a = Fraction(random.randint(2, 5), random.choice([2, 3]))
        b = Fraction(random.randint(3, 5), random.choice([4, 5]))
        c = Fraction(1, random.choice([4, 5]))
        q = f"\\frac{{{a.numerator}}}{{{a.denominator}}} : (\\frac{{{b.numerator}}}{{{b.denominator}}} - \\frac{{{c.numerator}}}{{{c.denominator}}})"
        ans = a / (b - c)
        trap1 = (a / b) - c
        
    return build_problem_dict(q, f"{ans.numerator}/{ans.denominator}", t1=f"{trap1.numerator}/{trap1.denominator}")

def frac_ord_3():
    # Poziom 3: Potęgi
    a = Fraction(1, random.choice([2, 3, 4]))
    b = Fraction(random.randint(1, 3), random.choice([2, 3]))
    c = Fraction(random.randint(1, 3), random.choice([2, 3]))
    
    q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}})^2 + \\frac{{{b.numerator}}}{{{b.denominator}}} \\cdot \\frac{{{c.numerator}}}{{{c.denominator}}}"
    ans = (a**2) + (b * c)
    trap1 = a + (b * c)
    trap2 = ((a**2) + b) * c
    
    return build_problem_dict(q, f"{ans.numerator}/{ans.denominator}", t1=f"{trap1.numerator}/{trap1.denominator}", t2=f"{trap2.numerator}/{trap2.denominator}")

def frac_ord_4():
    # Poziom 4: Nawiasy i potęgi razem
    a = Fraction(1, random.choice([2, 3]))
    b = Fraction(1, random.choice([2, 3]))
    c = Fraction(1, random.choice([2, 3, 4]))
    
    q = f"(\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}})^2 - \\frac{{{c.numerator}}}{{{c.denominator}}}"
    ans = ((a + b)**2) - c
    if ans < 0: ans = abs(ans)
    trap1 = (a**2 + b**2) - c
    
    return build_problem_dict(q, f"{ans.numerator}/{ans.denominator}", t1=f"{trap1.numerator}/{trap1.denominator}")