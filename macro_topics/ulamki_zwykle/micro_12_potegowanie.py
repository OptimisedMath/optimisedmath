import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def pow_frac_l1(level):
    while True:
        d = random.randint(3, 8)
        n = random.randint(1, d - 1)
        p = 2
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d)} \right)^{{{p}}}"
        
        c_str, _, _ = format_answers(n**p, d**p)
        
        # Trap 1: Squared only numerator
        t1, _, _ = format_answers(n**p, d) 
        # Trap 2: Multiplied by 2 instead of squaring
        t2, _, _ = format_answers(n * p, d * p) 
        w1, _, _ = format_answers((n**p) + 1, d**p)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result

def pow_frac_l2(level):
    while True:
        # Keeping denominator up to 5 so cubes don't get absurdly large
        d = random.randint(2, 5) 
        n = random.randint(1, d - 1)
        p = 3
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d)} \right)^{{{p}}}"
        
        c_str, _, _ = format_answers(n**p, d**p)
        
        # Trap 1: Cubed only numerator
        t1, _, _ = format_answers(n**p, d) 
        # Trap 2: Multiplied by 3 instead of cubing
        t2, _, _ = format_answers(n * p, d * p) 
        w1, _, _ = format_answers((n**p) + 1, d**p)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result

def pow_mixed_l3(level):
    while True:
        w = random.randint(1, 2)
        p = random.randint(2, 3)
        # Cap denominator if p=3 to prevent math from becoming tedious
        d = random.randint(2, 3) if p == 3 else random.randint(2, 4)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Oblicz: }} \left( {format_fraction_question(n, d, w)} \right)^{{{p}}}"
        
        num = (w * d) + n
        c_str, _, _ = format_answers(num**p, d**p)
        
        # Trap 1: Applied power to whole number and fraction separately
        t1, _, _ = format_answers(n**p, d**p, w**p) 
        # Trap 2: Applied power to numerator but forgot denominator
        t2, _, _ = format_answers(num**p, d) 
        w1, _, _ = format_answers(num**p + 1, d**p)
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
        if result: return result