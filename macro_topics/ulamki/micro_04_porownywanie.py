import random
from core.utils import format_fraction_question, build_problem_dict

def compare_fractions_same_den(level):
    d = random.randint(3, 12)
    n1 = random.randint(1, d + 5)
    
    n2 = n1
    while n2 == n1:
        n2 = random.randint(1, d + 5)
        
    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d)} \text{{ \_\_\_ }} {format_fraction_question(n2, d)}"
    
    # Only 2 options provided (No '=' sign)
    c_str, t_str = ("<", ">") if n1 < n2 else (">", "<")
        
    return build_problem_dict(q_str, c_str, c_str, c_str, t_str, None, None, f"Poziom {level}: Wspólne mianowniki")


def compare_fractions_same_num(level):
    n = random.randint(1, 9)
    d1 = random.randint(2, 12)
    
    d2 = d1
    while d2 == d1:
        d2 = random.randint(2, 12)
    
    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n, d1)} \text{{ \_\_\_ }} {format_fraction_question(n, d2)}"
    
    v1 = n / d1
    v2 = n / d2
    
    # Only 2 options provided (No '=' sign)
    c_str, t_str = ("<", ">") if v1 < v2 else (">", "<")
        
    return build_problem_dict(q_str, c_str, c_str, c_str, t_str, None, None, f"Poziom {level}: Wspólne liczniki")


def compare_fractions_diff_den(level):
    # 25% chance to test equivalent fractions (testing the '=' sign)
    if random.random() < 0.25:
        d1 = random.randint(2, 6)
        n1 = random.randint(1, d1 * 2)
        multiplier = random.randint(2, 4)
        d2 = d1 * multiplier
        n2 = n1 * multiplier
        
        if random.choice([True, False]):
            n1, n2 = n2, n1
            d1, d2 = d2, d1
    else:
        while True:
            d1, d2 = random.randint(2, 9), random.randint(2, 9)
            if d1 == d2: continue
            n1, n2 = random.randint(1, d1 * 2), random.randint(1, d2 * 2)
            if (n1 / d1) != (n2 / d2): break

    q_str = rf"\text{{Wybierz znak: }} {format_fraction_question(n1, d1)} \text{{ \_\_\_ }} {format_fraction_question(n2, d2)}"
    
    v1 = n1 / d1
    v2 = n2 / d2
    
    # 3 options provided here
    if v1 < v2:
        c_str, t_str, w_str = "<", ">", "="
    elif v1 > v2:
        c_str, t_str, w_str = ">", "<", "="
    else:
        c_str, t_str, w_str = "=", "<", ">"
        
    return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, None, f"Poziom {level}: Różne mianowniki")