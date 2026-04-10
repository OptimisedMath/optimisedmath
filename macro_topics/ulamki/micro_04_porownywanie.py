import random
from core.utils import format_fraction_question, build_problem_dict

def compare_fractions_same_den(level):
    d = random.randint(3, 12)
    n1 = random.randint(1, d + 5)
    n2 = random.randint(1, d + 5)
    
    # 20% chance to force the fractions to be equal
    if random.random() < 0.2:
        n2 = n1 
        
    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d)} \text{{ \_\_\_ }} {format_fraction_question(n2, d)}"
    
    if n1 < n2:
        c_str, t_str, w_str = "<", ">", "="
    elif n1 > n2:
        c_str, t_str, w_str = ">", "<", "="
    else:
        c_str, t_str, w_str = "=", "<", ">"
        
    return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Wspólne mianowniki")


def compare_fractions_same_num(level):
    n = random.randint(1, 9)
    d1 = random.randint(2, 12)
    d2 = random.randint(2, 12)
    
    # 20% chance to force the fractions to be equal
    if random.random() < 0.2:
        d2 = d1
    
    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n, d1)} \text{{ \_\_\_ }} {format_fraction_question(n, d2)}"
    
    v1 = n / d1
    v2 = n / d2
    
    if v1 < v2:
        c_str, t_str, w_str = "<", ">", "="
    elif v1 > v2:
        c_str, t_str, w_str = ">", "<", "="
    else:
        c_str, t_str, w_str = "=", "<", ">"
        
    return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Wspólne liczniki")


def compare_fractions_diff_den(level):
    d1 = random.randint(2, 9)
    d2 = random.randint(2, 9)
    n1 = random.randint(1, d1 * 2)
    n2 = random.randint(1, d2 * 2)
    
    # 20% chance to force equality by making them equivalent fractions
    if random.random() < 0.2:
        multiplier = random.randint(1, 3)
        n2 = n1 * multiplier
        d2 = d1 * multiplier
    
    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d1)} \text{{ \_\_\_ }} {format_fraction_question(n2, d2)}"
    
    v1 = n1 / d1
    v2 = n2 / d2
    
    if v1 < v2:
        c_str, t_str, w_str = "<", ">", "="
    elif v1 > v2:
        c_str, t_str, w_str = ">", "<", "="
    else:
        c_str, t_str, w_str = "=", "<", ">"
        
    return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Różne mianowniki")