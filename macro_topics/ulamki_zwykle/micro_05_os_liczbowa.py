import random
from core.utils import build_problem_dict

def fraction_number_line(level):
    while True:
        d = random.randint(3, 8)
        n = random.randint(1, d - 1)
        
        # Dynamically build the contents of the continuous axis
        line_content = r"\quad \underset{0}{|} "
        for i in range(1, d):
            if i == n:
                line_content += r"\quad \underset{\textbf{?}}{\downarrow} "
            else:
                line_content += r"\quad \underset{}{|} "
        line_content += r"\quad \underset{1}{|} \quad"
        
        q_str = rf"\text{{Jaki ułamek zaznaczono na osi?}}\\ \quad \\ \xleftrightarrow{{{line_content}}}"

        c_str = rf"\frac{{{n}}}{{{d}}}"
        
        t1 = rf"\frac{{{n}}}{{{d-1}}}"        # Trap 1: Counted lines instead of spaces
        t2 = rf"\frac{{{max(1, n-1)}}}{{{d}}}" # Trap 2: Off-by-one error starting from 0
        w1 = rf"\frac{{{d-n}}}{{{d}}}"        # Trap 3: Counted from the right side (1) instead of left (0)

        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result