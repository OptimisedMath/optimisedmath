import random
from fractions import Fraction
from core.utils import build_problem_dict, fmt_dec

def dec_to_frac(level):
    denominators = [4, 5, 20, 25, 50]
    d = random.choice(denominators)
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d: return None
    
    val = n / d
    q_str = rf"\text{{Zamień na ułamek nieskracalny: }} {fmt_dec(val)}"
    c_str = rf"\frac{{{n}}}{{{d}}}"
    
    decimals = len(str(val).split('.')[1])
    raw_d = 10 ** decimals
    raw_n = int(val * raw_d)
    
    t1 = rf"\frac{{{raw_n}}}{{{raw_d // 10}}}"
    t2 = rf"\frac{{{1}}}{{{raw_n}}}"
    
    wrong_d = d + random.choice([-1, 1])
    if wrong_d < 2: wrong_d = d + 2
    t3 = rf"\frac{{{n}}}{{{wrong_d}}}"
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")
    if result: return result

def frac_to_dec(level):
    d = random.choice([4, 5, 20, 25])
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d: return None
    
    q_str = rf"\text{{Zamień na ułamek dziesiętny: }} \frac{{{n}}}{{{d}}}"
    val = n / d
    c_str = fmt_dec(val)
    
    t1 = f"0,{n}{d}"
    t2 = fmt_dec(val / 10)
    t3 = fmt_dec(n + (d / 10))
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")
    if result: return result

def mixed_to_dec(level):
    w = random.randint(1, 5)
    d = random.choice([2, 4, 5, 20])
    n = random.randint(1, d - 1)
    if Fraction(n, d).denominator != d: return None
    
    q_str = rf"\text{{Zamień na ułamek dziesiętny: }} {w}\frac{{{n}}}{{{d}}}"
    val = w + (n / d)
    c_str = fmt_dec(val)
    
    t1 = f"{w},{n}{d}"
    t2 = fmt_dec(val / 10)
    t3 = f"{w},{d}"
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")
    if result: return result

def frac_to_dec_infinite(level):
    d = random.choice([3, 9])
    n = random.randint(1, d - 1)
    
    q_str = rf"\text{{Rozwiń ułamek (zapisz w okresie): }} \frac{{{n}}}{{{d}}}"
    
    # 1/3 = 0,(3) and 1/9 = 0,(1)
    val = int((n/d) * 10)
    c_str = f"0,({val})"
    
    t1 = f"0,{val}" # Student forgets the period brackets
    t2 = f"0,0({val})"
    w1 = f"0,({val + 1})"
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
    if result: return result