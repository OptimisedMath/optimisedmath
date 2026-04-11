import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def pow_frac(level):
    while True:
        d = random.randint(3, 7)
        n = random.randint(1, d - 1)
        p = random.randint(2, 3)
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d)} \right)^{p}"
        c_str, i_str, u_str = format_answers(n**p, d**p)
        t_str, _, _ = format_answers(n**p, d) # Trap: Powered only numerator
        w_str, _, _ = format_answers(n * p, d * p)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def pow_mixed(level):
    while True:
        w = random.randint(1, 2)
        d = random.randint(2, 4)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d, w)} \right)^2"
        num = (w * d) + n
        c_str, i_str, u_str = format_answers(num**2, d**2)
        t_str, _, _ = format_answers(n**2, d**2, w**2) # Trap: Power parts separately
        w_str, _, _ = format_answers(num**2 + 1, d**2)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")