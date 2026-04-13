import random
from core.utils import build_problem_dict, fmt_dec

def sub_dec_same(level):
    while True:
        v1 = random.randint(31, 99) / 10
        v2 = random.randint(11, int(v1*10) - 1) / 10
        if str(v1).endswith('.0') or str(v2).endswith('.0'): continue
        
        d1 = int(str(v1).split('.')[1])
        d2 = int(str(v2).split('.')[1])
        if d1 >= d2: continue # Ensure borrowing
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 - v2, 2))
        
        t1 = fmt_dec(round(int(v1) - int(v2) + abs(d1 - d2)/10, 2)) # Trap 1: Backwards subtraction
        w1 = fmt_dec(round(v1 - v2 + 0.1, 2))
        w2 = fmt_dec(round(v1 - v2 - 0.1, 2))
        
        if len({c_str, t1, w1, w2}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, w1=w1, w2=w2, level_name=f"Poziom {level}")

def sub_dec_diff_easy(level):
    while True:
        v1 = random.randint(311, 999) / 100 # e.g., 5.25
        v2 = random.randint(11, int(v1/10)*10 - 1) / 10 # e.g., 1.1
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 - v2, 2))
        
        t1 = fmt_dec(round(v1 - (v2 / 10), 2)) # Trap 1: Right aligned
        t2 = fmt_dec(round(v1 - v2 + 0.09, 2)) # Trap 2: Shifted subtraction mixup
        w1 = fmt_dec(round(v1 - v2 + 1, 2))
        
        if len({c_str, t1, t2, w1}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def sub_dec_diff_boss(level):
    while True:
        v1 = random.randint(31, 99) / 10 # e.g., 5.2
        v2 = random.randint(111, int(v1*100) - 1) / 100 # e.g., 1.45
        if str(v1).endswith('.0') or str(v2).endswith('.0'): continue
        
        d1 = int(str(v1).split('.')[1])
        d2_tenths = int(str(v2).split('.')[1][0])
        if d1 >= d2_tenths: continue # Ensure borrowing across decimal
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} - {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 - v2, 2))
        
        t1 = fmt_dec(round(v1 - round(v2, 1) + (int(str(v2)[-1])/100), 2)) # Trap 1: Dropped digit down (e.g., 4.25)
        t2 = fmt_dec(round(v1 - v2 - 0.4, 2)) # Trap 2: Backwards in middle column
        t3 = fmt_dec(round(v1 - v2 + 0.1, 2)) # Trap 3: Forgot to decrease previous column
        t4 = fmt_dec(round(v1 - v2 - 0.18, 2)) # Trap 4 (mapped to w1)
        
        if len({c_str, t1, t2, t3, t4}) == 5:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, w1=t4, level_name=f"Poziom {level}")