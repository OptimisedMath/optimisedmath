import random
from core.utils import build_problem_dict, fmt_dec

def compare_dec_same(level):
    n1 = random.randint(11, 99)
    n2 = random.randint(11, 99)
    if n1 == n2 or n1 % 10 == 0 or n2 % 10 == 0: return None
    
    v1, v2 = n1 / 100, n2 / 100
    q_str = rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
    c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
    
    # t2 is strictly reserved for the "=" trap here
    result = build_problem_dict(q_str, c_str, t1=t1, t2="=", level_name=f"Poziom {level}")
    if result: return result

def compare_dec_diff(level):
    if random.random() < 0.2:
        base = random.randint(1, 9)
        s1 = f"0,{base}"
        s2 = f"0,{base}0"
        if random.choice([True, False]): s1, s2 = s2, s1
        q_str = rf"\text{{Wybierz znak: }} {s1} \text{{ \_\_\_ }} {s2}"
        
        # Equal scenario: We use t3 and w1 for the < and > traps
        result = build_problem_dict(q_str, "=", t3="<", w1=">", level_name=f"Poziom {level}")
        if result: return result
    else:
        v1 = random.randint(2, 9) / 10
        v2 = random.randint(11, 99) / 100
        if v1 == v2 or int(v2*100) % 10 == 0: return None
        
        if random.choice([True, False]): v1, v2 = v2, v1
        q_str = rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
        c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        
        # Normal scenario: We use t1 for the wrong inequality, t2 for the "=" trap
        result = build_problem_dict(q_str, c_str, t1=t1, t2="=", level_name=f"Poziom {level}")
        if result: return result

def compare_dec_zeros(level):
    if random.random() < 0.2:
        whole = random.randint(1, 5)
        digit = random.randint(1, 9)
        s1 = f"{whole},0{digit}"
        s2 = f"{whole},0{digit}0"
        if random.choice([True, False]): s1, s2 = s2, s1
        q_str = rf"\text{{Wybierz znak: }} {s1} \text{{ \_\_\_ }} {s2}"
        
        # Equal scenario: We use t3 and w1 for the < and > traps
        result = build_problem_dict(q_str, "=", t3="<", w1=">", level_name=f"Poziom {level}")
        if result: return result
    else:
        whole = random.randint(1, 5)
        digit = random.randint(1, 9)
        v1 = whole + (digit / 100)
        v2 = whole + (digit / 10)
        if random.choice([True, False]): v1, v2 = v2, v1
            
        q_str = rf"\text{{Wybierz znak: }} {fmt_dec(v1)} \text{{ \_\_\_ }} {fmt_dec(v2)}"
        c_str, t1 = ("<", ">") if v1 < v2 else (">", "<")
        
        # Normal scenario: We use t1 for the wrong inequality, t2 for the "=" trap
        result = build_problem_dict(q_str, c_str, t1=t1, t2="=", level_name=f"Poziom {level}")
        if result: return result