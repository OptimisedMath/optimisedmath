import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def pow_frac(level):
    while True:
        d = random.randint(3, 7)
        n = random.randint(1, d - 1)
        p = random.randint(2, 3)
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d)} \right)^{p}"
        
        c_str, _, _ = format_answers(n**p, d**p)
        t1, _, _ = format_answers(n**p, d) 
        t2, _, _ = format_answers(n * p, d * p) 
        w1, _, _ = format_answers((n**p) + 1, d**p)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result

def pow_mixed(level):
    while True:
        w = random.randint(1, 2)
        d = random.randint(2, 4)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d, w)} \right)^2"
        
        num = (w * d) + n
        c_str, _, _ = format_answers(num**2, d**2)
        t1, _, _ = format_answers(n**2, d**2, w**2) 
        t2, _, _ = format_answers(num**2, d) 
        w1, _, _ = format_answers(num**2 + 1, d**2)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result