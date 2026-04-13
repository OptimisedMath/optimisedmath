import random
from core.utils import build_problem_dict, fmt_dec

def compare_dec_same(level):
    n1 = random.randint(11, 99)
    n2 = random.randint(11, 99)
    while n1 == n2: n2 = random.randint(11, 99)
    
    v1, v2 = n1 / 100, n2 / 100
    q_str = rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
    
    c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
    return build_problem_dict(q_str, c_str, t1=t1, level_name=f"Poziom {level}")

def compare_dec_diff(level):
    # Generates cases like 0.3 vs 0.15 where 15 looks bigger but 0.3 is mathematically larger
    v1 = random.randint(2, 9) / 10           # e.g., 0.3
    v2 = random.randint(11, int(v1*100)-1) / 100 # e.g., 0.15
    
    if random.choice([True, False]):
        v1, v2 = v2, v1
        
    q_str = rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
    
    c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
    return build_problem_dict(q_str, c_str, t1=t1, level_name=f"Poziom {level}")

def compare_dec_zeros(level):
    whole = random.randint(1, 5)
    digit = random.randint(1, 9)
    v1 = whole + (digit / 100) # e.g., 1.02
    v2 = whole + (digit / 10)  # e.g., 1.2
    
    if random.choice([True, False]):
        v1, v2 = v2, v1
        
    q_str = rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
    
    c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
    return build_problem_dict(q_str, c_str, t1=t1, level_name=f"Poziom {level}")