import random
from core.utils import build_problem_dict, fmt_dec

def mult_dec_int(level):
    while True:
        v1 = random.randint(2, 9) / 10
        v2 = random.randint(2, 9)
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {v2}"
        c_str = fmt_dec(round(v1 * v2, 2))
        
        t1 = fmt_dec(round(v1 * v2 / 100, 3)) # Trap 1: Extra zeros (e.g. 0.012)
        t2 = fmt_dec(round(v1 * 10 * v2, 2))  # Trap 2: Ignored comma (e.g. 12)
        w1 = fmt_dec(round((v1 * 10 * v2 + 1) / 10, 2))
        
        if len({c_str, t1, t2, w1}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def mult_dec_dec(level):
    while True:
        v1 = random.randint(2, 9) / 10
        v2 = random.randint(2, 9) / 10
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 * v2, 2))
        
        t1 = fmt_dec(round(v1 * v2 * 10, 2)) # Trap 1: Only 1 place (0.6)
        t2 = fmt_dec(round(v1 * 10 * v2 * 10, 2)) # Trap 2: No comma (6)
        t3 = fmt_dec(round(v1 * v2 / 10, 3)) # Trap 3: Too many zeros (0.006)
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")

def mult_dec_trim(level):
    while True:
        # Generate to force a .0 at the end (e.g., 1.5 * 0.4 = 0.60 -> 0.6)
        v1 = random.choice([1.5, 2.5, 3.5, 4.5])
        v2 = random.choice([0.2, 0.4, 0.6, 0.8])
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} \cdot {fmt_dec(v2)}"
        val = round(v1 * v2, 2)
        c_str = fmt_dec(val) # 0.6
        
        t1 = fmt_dec(round(val * 10, 2)) # Trap 1: Cut from left side (e.g., 6)
        t2 = fmt_dec(round(val / 10, 2)) # Trap 2: 0.06
        t3 = fmt_dec(round((v1 * 10 * v2 * 10) + 1, 2)) # Wrong answer
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=t3, level_name=f"Poziom {level}")