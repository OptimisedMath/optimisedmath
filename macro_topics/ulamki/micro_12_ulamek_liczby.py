import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def frac_of_int_natural(level):
    while True:
        d = random.randint(2, 8)
        n = random.randint(1, d - 1)
        k = d * random.randint(2, 6) # Guarantees integer result
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
        c_str, i_str, u_str = format_answers((k // d) * n, 1)
        t_str, _, _ = format_answers(k * d + n, d) # Trap: Added them
        w_str, _, _ = format_answers((k // d) * n + 1, 1)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def frac_of_int_frac(level):
    while True:
        d = random.randint(3, 9)
        n = random.randint(1, d - 1)
        k = random.randint(4, 15)
        if k % d == 0: continue
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
        c_str, i_str, u_str = format_answers(n * k, d)
        t_str, _, _ = format_answers(k * d, n) # Trap: Divided instead of multiplied
        w_str, _, _ = format_answers(n * k + 1, d)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")