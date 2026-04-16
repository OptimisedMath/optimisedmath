import random
from core.utils import build_problem_dict, fmt_dec

def number_line_midpoint(level):
    while True:
        base = random.randint(1, 8)
        v1 = base / 10
        v2 = (base + 1) / 10
        
        # Generates a continuous mathematical axis with ticks and a pointer
        # e.g., <----|--------↓--------|---->
        #           0,1       ?       0,2
        axis_str = rf"\xleftrightarrow{{\quad \underset{{{fmt_dec(v1)}}}{{|}} \quad\quad\quad \underset{{\textbf{{?}}}}{{\downarrow}} \quad\quad\quad \underset{{{fmt_dec(v2)}}}{{|}} \quad}}"
        
        q_str = rf"\text{{Jaka liczba znajduje się na osi dokładnie pośrodku?}}\\ \quad \\ {axis_str}"
        
        c_str = fmt_dec(v1 + 0.05)
        
        t1 = fmt_dec(v1 + 0.01)               # Trap 1: Just picked the next hundredth (e.g., 0.11)
        t2 = fmt_dec(v1 + v2)                 # Trap 2: Added the boundaries together (e.g., 0.3)
        w1 = fmt_dec((v1 + 0.05) * 10)        # Trap 3: Decimal shift error (e.g., 1.5)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result