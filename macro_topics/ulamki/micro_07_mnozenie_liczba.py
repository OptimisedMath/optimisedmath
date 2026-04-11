import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def mult_frac_int_simple(level):
    while True:
        d = random.randint(3, 9)
        n = random.randint(1, d - 1)
        k = random.randint(2, 5)
        if math.gcd(d, k) > 1: continue # No cross-simplify
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \cdot {k}"
        c_str, i_str, u_str = format_answers(n * k, d)
        t_str, _, _ = format_answers(n * k, d * k) # Trap: Multiply both
        w_str, _, _ = format_answers(n * k + 1, d)
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def mult_frac_int_cross(level):
    while True:
        k = random.randint(2, 6)
        factor = random.randint(2, 4)
        d = k * factor
        n = random.randint(1, d - 1)
        if math.gcd(n, d) > 1: continue
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \cdot {k}"
        c_str, i_str, u_str = format_answers(n * k, d)
        t_str = rf"\frac{{{n * k}}}{{{d}}}" # Trap: Mathematically correct but unsimplified string
        w_str, _, _ = format_answers(n * k, d + k)
        
        if c_str != t_str and len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def mult_mixed_int(level):
    while True:
        w = random.randint(1, 3)
        d = random.randint(2, 5)
        n = random.randint(1, d - 1)
        k = random.randint(2, 4)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d, w)} \cdot {k}"
        correct_num = ((w * d) + n) * k
        c_str, i_str, u_str = format_answers(correct_num, d)
        t_str, _, _ = format_answers(n * k, d, w) # Trap: Multiply only fraction
        w_str, _, _ = format_answers(correct_num + 1, d)
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")