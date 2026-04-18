import random
from core.utils import format_fraction_question, build_problem_dict

def compare_fractions_same_den(level):
    d = random.randint(3, 12)
    n1 = random.randint(1, d + 5)
    n2 = n1
    while n2 == n1: n2 = random.randint(1, d + 5)
        
    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d)} \text{{ \_\_\_ }} {format_fraction_question(n2, d)}"
    
    c_str, t1 = ("<", ">") if n1 < n2 else (">", "<")
        
    result = build_problem_dict(q_str, c_str, t1=t1, level_name=f"Poziom {level}")
    if result: return result

def compare_fractions_same_num(level):
    n = random.randint(1, 9)
    d1 = random.randint(2, 12)
    d2 = d1
    while d2 == d1: d2 = random.randint(2, 12)
    
    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n, d1)} \text{{ \_\_\_ }} {format_fraction_question(n, d2)}"
    
    v1, v2 = n / d1, n / d2
    
    c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        
    result = build_problem_dict(q_str, c_str, t1=t1, level_name=f"Poziom {level}")
    if result: return result

def compare_fractions_diff_den(level):
    if random.random() < 0.25:
        d1 = random.randint(2, 6)
        n1 = random.randint(1, d1 * 2)
        multiplier = random.randint(2, 4)
        d2, n2 = d1 * multiplier, n1 * multiplier
        if random.choice([True, False]):
            n1, n2 = n2, n1
            d1, d2 = d2, d1
    else:
            d1, d2 = random.randint(2, 9), random.randint(2, 9)
            if d1 == d2: return None
            n1, n2 = random.randint(1, d1 * 2), random.randint(1, d2 * 2)
            if (n1 / d1) != (n2 / d2): return None

    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d1)} \text{{ \_\_\_ }} {format_fraction_question(n2, d2)}"
    v1, v2 = n1 / d1, n2 / d2
    
    if v1 < v2:
        result = build_problem_dict(q_str, "<", t1=">", t2="=", level_name=f"Poziom {level}")
        if result: return result
    elif v1 > v2:
        result = build_problem_dict(q_str, ">", t1="<", t2="=", level_name=f"Poziom {level}")
        if result: return result
    else:
        result = build_problem_dict(q_str, "=", t3="<", w1=">", level_name=f"Poziom {level}")
        if result: return result