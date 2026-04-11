import random
from core.utils import build_problem_dict

def fraction_as_division(level):
    while True:
        n = random.randint(1, 9)
        d = random.randint(2, 9)
        if n == d: continue

        q_str = rf"\text{{Zapisz dzielenie jako ułamek: }} {n} : {d}"
        
        # Correct: First number is top, second is bottom
        c_str = rf"\frac{{{n}}}{{{d}}}"
        
        # TRAP: Reversed the numbers (e.g., d / n)
        t_str = rf"\frac{{{d}}}{{{n}}}" 
        
        # WRONG: Just a random wrong denominator
        w_str = rf"\frac{{{n}}}{{{d + 1}}}"
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Dzielenie jako ułamek")