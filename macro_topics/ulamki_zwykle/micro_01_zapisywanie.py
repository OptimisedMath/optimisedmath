import random
from core.utils import build_problem_dict

def fraction_as_division(level):
    while True:
        n = random.randint(1, 9)
        d = random.randint(2, 9)
        if n == d: continue

        q_str = rf"\text{{Zapisz dzielenie jako ułamek: }} {n} : {d}"
        
        c_str = rf"\frac{{{n}}}{{{d}}}"
        t1 = rf"\frac{{{d}}}{{{n}}}"                  
        t2 = rf"\frac{{{n}}}{{{n+d}}}"                
        w1 = rf"\frac{{{n}}}{{{d + random.choice([-1, 1])}}}" 
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", grading_policy="equivalent_accepted")
        if result: return result