import random
from core.utils import build_problem_dict, fmt_dec

def move_comma_mult(level):
    while True:
        v = random.randint(111, 999) / 100
        zeros = random.choice([10, 100, 1000])
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v)} \cdot {zeros}"
        c_str = fmt_dec(round(v * zeros, 2))
        
        t1 = fmt_dec(round(v / zeros, 4)) # Trap 1: Moved left
        wrong_zeros = zeros * 10 if zeros < 1000 else 100
        t2 = fmt_dec(round(v * wrong_zeros, 2)) # Trap 2: Wrong count
        t3 = fmt_dec(v) + "0" # Trap 3: Appended zero string
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")

def move_comma_div(level):
    while True:
        v = random.randint(111, 999) / 10
        zeros = random.choice([10, 100, 1000])
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v)} : {zeros}"
        c_str = fmt_dec(round(v / zeros, 5))
        
        t1 = fmt_dec(round(v * zeros, 2)) # Trap 1: Moved right
        wrong_zeros = zeros / 10 if zeros > 10 else 100
        t2 = fmt_dec(round(v / wrong_zeros, 4)) # Trap 2: Wrong count
        t3 = fmt_dec(round(v / (zeros * 10), 6)) # Trap 3: Too far
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")