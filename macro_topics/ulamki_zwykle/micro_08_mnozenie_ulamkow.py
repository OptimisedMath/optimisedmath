import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def mult_frac_simple(level):
    while True:
        d1, d2 = random.randint(3, 7), random.randint(3, 7)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        if math.gcd(n1, d2) > 1 or math.gcd(n2, d1) > 1: continue
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2)}"
        
        c_str, _, _ = format_answers(n1 * n2, d1 * d2)
        t1, _, _ = format_answers(n1 + n2, d1 + d2) # Trap 1: Added
        t2, _, _ = format_answers(n1 * d2, d1 * n2) # Trap 2: Cross-multiplied
        w1, _, _ = format_answers((n1 * n2) + 1, d1 * d2)
        
        if len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def mult_frac_cross(level):
    while True:
        n1, d2 = 2, 4
        while math.gcd(n1, d2) == 1:
            n1, d2 = random.randint(2, 8), random.randint(2, 8)
        d1, n2 = random.randint(3, 9), random.randint(1, 7)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2)}"
        
        c_str, _, _ = format_answers(n1 * n2, d1 * d2)
        t1 = rf"\frac{{{n1 * n2}}}{{{d1 * d2}}}" # Trap 1: Unsimplified
        t2, _, _ = format_answers(1, d1 * d2) # Trap 2: Horizontal simplify
        w1, _, _ = format_answers(n1 * n2, d1 * d2 + 1)
        
        if c_str != t1 and len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def mult_frac_mixed(level):
    while True:
        w = random.randint(1, 3)
        d1, d2 = random.randint(2, 5), random.randint(2, 5)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2, w)}"
        
        c_str, _, _ = format_answers(n1 * ((w * d2) + n2), d1 * d2)
        t1, _, _ = format_answers(n1 * n2, d1 * d2, w) # Trap 1: Fraction only
        t2, _, _ = format_answers(n1 + ((w * d2) + n2), d1 + d2) # Trap 2: Added
        w1, _, _ = format_answers(n1 * ((w * d2) + n2) + 1, d1 * d2)
        
        if len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def mult_mixed_mixed(level):
    while True:
        w1, w2 = random.randint(1, 2), random.randint(1, 2)
        d1, d2 = random.randint(2, 4), random.randint(2, 4)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1, w1)} \cdot {format_fraction_question(n2, d2, w2)}"
        
        num1, num2 = (w1 * d1) + n1, (w2 * d2) + n2
        c_str, _, _ = format_answers(num1 * num2, d1 * d2)
        t1, _, _ = format_answers(n1 * n2, d1 * d2, w1 * w2) # Trap 1: Wholes by wholes
        t2, _, _ = format_answers(n1 * n2, d1 * d2, w1 + w2) # Trap 2: Added wholes
        w1_str, _, _ = format_answers(num1 * num2 + 1, d1 * d2)
        
        if len({c_str, t1, t2, w1_str}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1_str, level_name=f"Poziom {level}")