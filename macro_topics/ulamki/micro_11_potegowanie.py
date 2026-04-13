import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def pow_frac(level):
    while True:
        d = random.randint(3, 7)
        n = random.randint(1, d - 1)
        p = random.randint(2, 3)
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d)} \right)^{p}"
        
        c_str, _, _ = format_answers(n**p, d**p)
        t1, _, _ = format_answers(n**p, d) # Trap 1: Only num
        t2, _, _ = format_answers(n * p, d * p) # Trap 2: Multiplied by exp
        w1, _, _ = format_answers((n**p) + 1, d**p)
        
        if len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def pow_mixed(level):
    while True:
        w = random.randint(1, 2)
        d = random.randint(2, 4)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d, w)} \right)^2"
        
        num = (w * d) + n
        c_str, _, _ = format_answers(num**2, d**2)
        t1, _, _ = format_answers(n**2, d**2, w**2) # Trap 1: Wholes separately
        t2, _, _ = format_answers(num**2, d) # Trap 2: Forgot denominator
        w1, _, _ = format_answers(num**2 + 1, d**2)
        
        if len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")