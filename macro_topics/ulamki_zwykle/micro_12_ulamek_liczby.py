import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def frac_of_int_natural(level):
    while True:
        d = random.randint(2, 8)
        n = random.randint(1, d - 1)
        k = d * random.randint(2, 6)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
        
        c_str, _, _ = format_answers((k // d) * n, 1)
        t1, _, _ = format_answers(k * d + n, d) 
        t2, _, _ = format_answers(k // n * d, 1) 
        w1, _, _ = format_answers((k // d) * n + 1, 1)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result

def frac_of_int_frac(level):
    while True:
        d = random.randint(3, 9)
        n = random.randint(1, d - 1)
        k = random.randint(4, 15)
        if k % d == 0: continue
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \text{{ z liczby }} {k}"
        
        c_str, _, _ = format_answers(n * k, d)
        t1, _, _ = format_answers(k * d, n) 
        t2, _, _ = format_answers(n * k, d * k) 
        w1, _, _ = format_answers(n * k + 1, d)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result