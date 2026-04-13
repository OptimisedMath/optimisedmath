import random
from core.utils import build_problem_dict, fmt_dec

def div_dec_int(level):
    while True:
        c = random.randint(2, 9)
        d = random.randint(2, 5)
        v1 = (c * d) / 10
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {d}"
        c_str = fmt_dec(round(v1 / d, 2))
        
        t1 = fmt_dec(round((v1 * 10) / d, 2)) # Trap 1: Ignored comma
        t2 = fmt_dec(round(v1 / (d * 10), 3)) # Trap 2: Moved too far
        w1 = fmt_dec(round((v1 / d) + 0.1, 2))
        
        if len({c_str, t1, t2, w1}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def div_dec_dec(level):
    while True:
        c = random.randint(2, 9)
        d = random.randint(2, 5)
        v1 = (c * d) / 100
        v2 = d / 10
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 / v2, 2))
        
        t1 = fmt_dec(round(v1 / (v2 * 10), 3)) # Trap 1: Direct division bad shift
        t2 = fmt_dec(round((v1 / v2) * 10, 2)) # Trap 2: Shifted too far
        t3 = fmt_dec(round((v1 / v2) / 10, 3)) # Trap 3: Summed places like mult
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")

def div_dec_expand(level):
    while True:
        c = random.randint(2, 9)
        d = random.randint(2, 5)
        v1 = (c * d) / 10
        v2 = d / 100
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} : {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 / v2, 2))
        
        t1 = fmt_dec(round((v1 / 10) / v2, 2)) # Trap 1: Failed to add zero (0.6)
        t2 = fmt_dec(round((v1 / 100) / v2, 3)) # Trap 2: 0.06
        w1 = fmt_dec(round((v1 / v2) + 1, 2))
        
        if len({c_str, t1, t2, w1}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")