import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def div_frac_int(level):
    while True:
        d = random.randint(2, 7)
        n = random.randint(1, d - 1)
        k = random.randint(2, 5)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} : {k}"
        
        c_str, _, _ = format_answers(n, d * k)
        t1, _, _ = format_answers(n * k, d) # Trap 1: Numerator multiplied
        t2, _, _ = format_answers(n, d)     # Trap 2: Divided denominator (fails math but good distractor)
        if d % k == 0: t2, _, _ = format_answers(n, d // k)
        w1, _, _ = format_answers(n + k, d * k)
        
        if len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def div_int_frac(level):
    while True:
        k = random.randint(2, 5)
        d = random.randint(2, 7)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Oblicz: }} {k} : {format_fraction_question(n, d)}"
        
        c_str, _, _ = format_answers(k * d, n)
        t1, _, _ = format_answers(k * n, d) # Trap 1: Num only, no invert
        t2, _, _ = format_answers(n, k * d) # Trap 2: Denom straight, num bottom
        w1, _, _ = format_answers((k * d) + 1, n)
        
        if len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

def div_mixed_int(level):
    while True:
        w = random.randint(2, 4)
        d = random.randint(2, 5)
        n = random.randint(1, d - 1)
        k = random.randint(2, 3)
        if w % k != 0: continue 
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d, w)} : {k}"
        
        correct_num = (w * d) + n
        c_str, _, _ = format_answers(correct_num, d * k)
        t1, _, _ = format_answers(n, d, w // k) # Trap 1: Wholes only
        t2, _, _ = format_answers(correct_num * k, d) # Trap 2: Improper but straight across
        w1, _, _ = format_answers(correct_num + 1, d * k)
        
        if len({c_str, t1, t2, w1}) == 4: 
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")