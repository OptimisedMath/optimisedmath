import random
from fractions import Fraction
from core.utils import build_problem_dict, fmt_dec

def dec_to_frac(level):
    while True:
        # Generate nice decimals ending in 5, 2, 4, 8 etc.
        denominators = [4, 5, 20, 25, 50]
        d = random.choice(denominators)
        n = random.randint(1, d - 1)
        if Fraction(n, d).denominator != d: continue # Ensure it's irreducible to start
        
        val = n / d
        q_str = rf"\text{{Zamień na ułamek nieskracalny: }} {fmt_dec(val)}"
        
        c_str = rf"\frac{{{n}}}{{{d}}}"
        
        # Calculate raw unsimplified math
        decimals = len(str(val).split('.')[1])
        raw_d = 10 ** decimals
        raw_n = int(val * raw_d)
        
        t1 = rf"\frac{{{raw_n}}}{{{raw_d // 10}}}" # Trap 1: Wrong denominator (10 instead of 100)
        t2 = rf"\frac{{{1}}}{{{raw_n}}}"          # Trap 2: Inverted
        
        wrong_d = d + random.choice([-1, 1])
        if wrong_d < 2: wrong_d = d + 2
        t3 = rf"\frac{{{n}}}{{{wrong_d}}}"        # Trap 3: Error during simplification
        
        w1 = rf"\frac{{{n + 1}}}{{{d}}}"          # Wrong 1
        
        if len({c_str, t1, t2, t3, w1}) == 5:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, w1=w1, level_name=f"Poziom {level}")

def frac_to_dec(level):
    while True:
        d = random.choice([4, 5, 20, 25])
        n = random.randint(1, d - 1)
        if Fraction(n, d).denominator != d: continue
        
        q_str = rf"\text{{Zamień na ułamek dziesiętny: }} \frac{{{n}}}{{{d}}}"
        
        val = n / d
        c_str = fmt_dec(val)
        
        t1 = f"0,{n}{d}"                          # Trap 1: Numerator and denominator after comma
        t2 = fmt_dec(val / 10)                    # Trap 2: Shift error (too small)
        t3 = fmt_dec(n + (d / 10))                # Trap 3: Mixed up logic (numerator as whole)
        w1 = fmt_dec(val + 0.1)
        
        if len({c_str, t1, t2, t3, w1}) == 5:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, w1=w1, level_name=f"Poziom {level}")

def mixed_to_dec(level):
    while True:
        w = random.randint(1, 5)
        d = random.choice([2, 4, 5, 20])
        n = random.randint(1, d - 1)
        if Fraction(n, d).denominator != d: continue
        
        q_str = rf"\text{{Zamień na ułamek dziesiętny: }} {w}\frac{{{n}}}{{{d}}}"
        
        val = w + (n / d)
        c_str = fmt_dec(val)
        
        t1 = f"{w},{n}{d}"                        # Trap 1: Fraction straight after comma
        t2 = fmt_dec(val / 10)                    # Trap 2: Ignored whole numbers position
        t3 = f"{w},{d}"                           # Trap 3: Put denominator as decimal
        t4 = fmt_dec(n / d)                       # Trap 4: Forgot whole number entirely
        
        if len({c_str, t1, t2, t3, t4}) == 5:
            # We map t4 to w1 since build_problem_dict only handles up to t3 natively for exact trap IDs
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, w1=t4, level_name=f"Poziom {level}")