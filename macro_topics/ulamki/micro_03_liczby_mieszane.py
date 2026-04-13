import random
from core.utils import format_fraction_question, build_problem_dict

def mixed_to_improper(level):
    while True:
        w = random.randint(1, 5)
        d = random.randint(2, 9)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Zamień na ułamek niewłaściwy: }} {format_fraction_question(n, d, w)}"
        
        c_str = rf"\frac{{{(w * d) + n}}}{{{d}}}"
        t1 = rf"\frac{{{(w * d) * n}}}{{{d}}}"     # Trap 1: Multiplied numerator
        t2 = rf"\frac{{{w + n}}}{{{d}}}"           # Trap 2: Added whole directly
        t3 = rf"\frac{{{(w * d) + n}}}{{{d * w}}}" # Trap 3: Multiplied denominator too
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")

def improper_to_mixed(level):
    while True:
        w = random.randint(1, 5)
        d = random.randint(2, 9)
        n = random.randint(1, d - 1)
        
        start_n = (w * d) + n
        q_str = rf"\text{{Wyłącz całości z ułamka: }} \frac{{{start_n}}}{{{d}}}"
        
        c_str = format_fraction_question(n, d, w)
        t1 = str(w)                                # Trap 1: Forgot remainder entirely
        t2 = format_fraction_question(d, n, w)     # Trap 2: Swapped remainder & den
        
        w_wrong = w + random.choice([-1, 1])
        if w_wrong < 1: w_wrong = w + 2
        w1 = format_fraction_question(n, d, w_wrong) # Wrong 1: Math error
        
        if len({c_str, t1, t2, w1}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")