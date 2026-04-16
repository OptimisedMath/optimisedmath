import random
from core.utils import build_problem_dict, fmt_dec

def number_line_midpoint(level):
    while True:
        base = random.randint(1, 8)
        v1 = base / 10
        v2 = (base + 1) / 10
        
        # Visual LaTeX Number Line
        q_str = (
            rf"\text{{Jaka liczba znajduje się na osi dokładnie pośrodku?}}"
            rf"\\ \quad \\"
            rf"\Large | \xrightarrow{{\quad \textbf{{ ? }} \quad}} |"
            rf"\\ \small {fmt_dec(v1)} \quad\quad\quad\quad\quad {fmt_dec(v2)}"
        )
        
        c_str = fmt_dec(v1 + 0.05)
        
        t1 = fmt_dec(v1 + 0.5) 
        t2 = fmt_dec(v2 + 0.05) 
        w1 = fmt_dec(v1 + 0.01)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result