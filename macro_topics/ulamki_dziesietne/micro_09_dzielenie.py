import random
from core.utils import build_problem_dict, fmt_dec

def div_dec_int(level):
    while True:
        c = random.randint(2, 9)
        d = random.randint(2, 5)
        v1 = (c * d) / 10
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {d}"
        c_str = fmt_dec(round(v1 / d, 2))
        
        t1 = fmt_dec(round((v1 * 10) / d, 2))
        t2 = fmt_dec(round(v1 / (d * 10), 3))
        w1 = fmt_dec(round((v1 / d) + 0.1, 2))
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result

def div_dec_dec(level):
    while True:
        c = random.randint(2, 9)
        d = random.randint(2, 5)
        v1 = (c * d) / 100
        v2 = d / 10
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 / v2, 2))
        
        t1 = fmt_dec(round(v1 / (v2 * 10), 3))
        t2 = fmt_dec(round((v1 / v2) * 10, 2))
        # FIX: Simulate student improperly summing the decimal places (3 total places instead of 1)
        t3 = fmt_dec(round((v1 / v2) / 100, 3)) 
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")
        if result: return result

def div_dec_expand(level):
    while True:
        c = random.randint(2, 9)
        d = random.randint(2, 5)
        v1 = (c * d) / 10
        v2 = d / 100
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 / v2, 2))
        
        t1 = fmt_dec(round((v1 / 10) / v2, 2))
        t2 = fmt_dec(round((v1 / 100) / v2, 3))
        w1 = fmt_dec(round((v1 / v2) + 1, 2))
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result

def div_dec_phantom_zero(level):
    while True:
        # Generate divisions like 0.3 : 2 = 0.15 where student must append a 0
        v1 = random.choice([1, 3, 5, 7, 9]) / 10
        d = random.choice([2, 4, 5])
        if (v1 * 10) % d == 0: continue # Skip if no phantom zero is needed
        
        q_str = rf"\text{{Oblicz (dopisz zero na końcu dzielnej): }} {fmt_dec(v1)} : {d}"
        c_str = fmt_dec(round(v1 / d, 3))
        
        t1 = fmt_dec(round((v1 * 10) / d, 3)) # Forgot the decimal shift
        t2 = fmt_dec(round(v1 / (d * 10), 4))
        w1 = fmt_dec(round((v1 / d) + 0.1, 3))
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result