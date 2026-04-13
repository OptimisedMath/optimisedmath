import random
from core.utils import build_problem_dict, fmt_dec

def order_dec_simple(level):
    while True:
        v1 = random.randint(11, 29) / 10
        v2 = random.randint(2, 9) / 10
        v3 = random.randint(2, 5)
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)} \cdot {v3}"
        c_str = fmt_dec(round(v1 + (v2 * v3), 2))
        
        t1 = fmt_dec(round((v1 + v2) * v3, 2)) # Trap 1: Left to right
        t2 = fmt_dec(round(v1 + (v2 * v3 * 10), 2)) # Trap 2: Decimal error in mult
        t3 = fmt_dec(round(v1 + (v2 * v3) + 0.9, 2)) # Trap 3: Addition alignment error
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")

def order_dec_brackets(level):
    while True:
        v1 = random.randint(21, 49) / 10
        v2 = random.randint(11, 19) / 10
        v3 = random.randint(2, 9) / 10
        
        q_str = rf"\text{{Oblicz: }} ({fmt_dec(v1)} - {fmt_dec(v2)}) \cdot {fmt_dec(v3)}"
        c_str = fmt_dec(round((v1 - v2) * v3, 2))
        
        t1 = fmt_dec(round(v1 - (v2 * v3), 2)) # Trap 1: Ignored brackets
        t2 = fmt_dec(round((v1 - v2) * v3 * 10, 2)) # Trap 2: Mult place value error
        t3 = fmt_dec(round((v1 - v2 + 0.9) * v3, 2)) # Trap 3: Bracket arithmetic error
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")