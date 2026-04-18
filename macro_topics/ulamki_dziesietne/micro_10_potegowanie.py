import random
from core.utils import build_problem_dict, fmt_dec

def pow_dec_square(level):
    v = random.randint(2, 9) / 10
    q_str = rf"\text{{Oblicz: }} ({fmt_dec(v)})^2"
    
    c_str = fmt_dec(round(v**2, 2))
    
    t1 = fmt_dec(round(v * 2, 1)) 
    
    # TRAP 2: Student squares the number but forgets decimal places entirely (e.g., 0.2^2 = 4)
    t2 = fmt_dec(round(v * 10)**2) 
    
    w1 = fmt_dec(round(v**2 + 0.01, 2))
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
    if result: return result