import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def div_frac_simple(level):
    while True:
        d1, d2 = random.randint(3, 7), random.randint(3, 7)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} : {format_fraction_question(n2, d2)}"
        c_str, i_str, u_str = format_answers(n1 * d2, d1 * n2)
        t_str, _, _ = format_answers(n1 * n2, d1 * d2) # Trap: Direct multiply
        w_str, _, _ = format_answers((n1 * d2) + 1, d1 * n2)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def div_frac_cross(level):
    while True:
        n1, n2 = 2, 4
        while math.gcd(n1, n2) == 1:
            n1, n2 = random.randint(2, 8), random.randint(2, 8)
        d1, d2 = random.randint(3, 9), random.randint(3, 9)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1)} : {format_fraction_question(n2, d2)}"
        c_str, i_str, u_str = format_answers(n1 * d2, d1 * n2)
        
        # Trap: Simplify BEFORE flip
        g = math.gcd(n1, n2)
        trap_n1, trap_n2 = n1 // g, n2 // g
        t_str, _, _ = format_answers(trap_n1 * d2, d1 * trap_n2) 
        w_str, _, _ = format_answers((n1 * d2) + 1, d1 * n2)
        
        if c_str != t_str and len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def div_mixed_mixed(level):
    while True:
        w1, w2 = random.randint(1, 2), random.randint(1, 2)
        d1, d2 = random.randint(2, 4), random.randint(2, 4)
        n1, n2 = random.randint(1, d1-1), random.randint(1, d2-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1, w1)} : {format_fraction_question(n2, d2, w2)}"
        num1, num2 = (w1 * d1) + n1, (w2 * d2) + n2
        c_str, i_str, u_str = format_answers(num1 * d2, d1 * num2)
        t_str, _, _ = format_answers(num1 * n2, d1 * d2) # Trap: Didn't flip
        w_str, _, _ = format_answers(num1 * d2 + 1, d1 * num2)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")