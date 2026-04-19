import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def frac_ord_1(level):
    d = random.randint(3, 6)
    n1, n2, n3 = random.randint(1, d-1), random.randint(1, d-1), random.randint(1, d-1)
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d)} + {format_fraction_question(n2, d)} \cdot {format_fraction_question(n3, d)}"
    
    c_str, _, _ = format_answers(n1 * d + (n2 * n3), d * d)
    t1, _, _ = format_answers((n1 + n2) * n3, d * d) 
    t2, _, _ = format_answers(n1 + (n2 * n3), d) 
    w1, _, _ = format_answers(n1 * d + (n2 * n3) + 1, d * d)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
    if result: return result

def frac_ord_1(level):
    d = random.randint(3, 6)
    n1, n2, n3 = random.randint(1, d-1), random.randint(1, d-1), random.randint(1, d-1)
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d)} \cdot \left( {format_fraction_question(n2, d)} + {format_fraction_question(n3, d)} \right)"
    
    c_str, _, _ = format_answers(n1 * (n2 + n3), d * d)
    t1, _, _ = format_answers((n1 * n2) + n3, d * d) 
    t2, _, _ = format_answers(n1 * (n2 + n3), d) 
    w1, _, _ = format_answers(n1 * (n2 + n3) + 1, d * d)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
    if result: return result