import random
from core.utils import build_problem_dict, fmt_dec

def add_dec_same(level):
    while True:
        w1, w2 = random.randint(1, 4), random.randint(1, 4)
        d1, d2 = random.randint(1, 8), random.randint(1, 8)
        if d1 + d2 >= 10: continue
        
        v1 = w1 + (d1 / 10)
        v2 = w2 + (d2 / 10)
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)}"
        c_str = fmt_dec(v1 + v2)
        
        t1 = fmt_dec((w1 + d2) + ((w2 + d1)/10))
        w1_ans = fmt_dec(v1 + v2 + 0.1)
        w2_ans = fmt_dec(v1 + v2 + 1)
        
        result = build_problem_dict(q_str, c_str, t1=t1, w1=w1_ans, w2=w2_ans, level_name=f"Poziom {level}")
        if result: return result

def add_dec_carry(level):
    while True:
        d1 = random.randint(5, 9)
        d2 = random.randint(15 - d1, 9)
        v1, v2 = d1 / 10, d2 / 10
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)}"
        c_str = fmt_dec(v1 + v2)
        
        t1 = fmt_dec((d1 + d2) / 100)
        t2 = str(d1 + d2)
        w1 = fmt_dec(v1 + v2 + 0.1)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result

def add_dec_diff(level):
    while True:
        v1 = random.randint(11, 49) / 10
        v2 = random.randint(11, 99) / 100
        if str(v1).endswith('.0') or str(v2).endswith('.0'): continue
        
        q_str = rf"\text{{Oblicz: }} {fmt_dec(v1)} + {fmt_dec(v2)}"
        c_str = fmt_dec(round(v1 + v2, 2))
        
        d1_tenth = int(str(v1).split('.')[1])
        d2_hundredth = int(str(v2).split('.')[1][1])
        d2_tenth = int(str(v2).split('.')[1][0])
        w1_whole = int(v1)
        w2_whole = int(v2)
        
        t1 = fmt_dec(round(w1_whole + w2_whole + (d1_tenth + d2_hundredth)/100 + (d2_tenth)/10, 2))
        t2 = fmt_dec(round((w1_whole + w2_whole)/10 + (d1_tenth + d2_tenth)/100, 2))
        t3 = fmt_dec(round(v1 + int(v2*10)/10, 2))
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")
        if result: return result