import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def mult_frac_simple(level):
    while True:
        d1, d2 = random.randint(3, 7), random.randint(3, 7)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        if math.gcd(n1, d2) > 1 or math.gcd(n2, d1) > 1: continue
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2)}"
        c_str, i_str, u_str = format_answers(n1 * n2, d1 * d2)
        t_str, _, _ = format_answers(n1 + n2, d1 + d2) # Trap: Add instead of multiply
        w_str, _, _ = format_answers((n1 * n2) + 1, d1 * d2)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def mult_frac_cross(level):
    while True:
        n1, d2 = 2, 4
        while math.gcd(n1, d2) == 1:
            n1, d2 = random.randint(2, 8), random.randint(2, 8)
        d1, n2 = random.randint(3, 9), random.randint(1, 7)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2)}"
        c_str, i_str, u_str = format_answers(n1 * n2, d1 * d2)
        t_str = rf"\frac{{{n1 * n2}}}{{{d1 * d2}}}" # Trap: Unsimplified
        w_str, _, _ = format_answers(n1 * n2, d1 * d2 + 1)
        
        if c_str != t_str and len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def mult_frac_mixed(level):
    while True:
        w = random.randint(1, 3)
        d1, d2 = random.randint(2, 5), random.randint(2, 5)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} \cdot {format_fraction_question(n2, d2, w)}"
        c_str, i_str, u_str = format_answers(n1 * ((w * d2) + n2), d1 * d2)
        t_str, _, _ = format_answers(n1 * n2, d1 * d2, w) # Trap: Frac * Frac only
        w_str, _, _ = format_answers((n1 * ((w * d2) + n2)) + 1, d1 * d2)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def mult_mixed_mixed(level):
    while True:
        w1, w2 = random.randint(1, 2), random.randint(1, 2)
        d1, d2 = random.randint(2, 4), random.randint(2, 4)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1, w1)} \cdot {format_fraction_question(n2, d2, w2)}"
        num1, num2 = (w1 * d1) + n1, (w2 * d2) + n2
        c_str, i_str, u_str = format_answers(num1 * num2, d1 * d2)
        t_str, _, _ = format_answers(n1 * n2, d1 * d2, w1 * w2) # Trap: W*W, F*F
        w_str, _, _ = format_answers(num1 * num2 + 1, d1 * d2)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")