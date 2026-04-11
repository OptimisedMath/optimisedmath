import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def div_frac_int(level):
    while True:
        d = random.randint(2, 7)
        n = random.randint(1, d - 1)
        k = random.randint(2, 5)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} : {k}"
        c_str, i_str, u_str = format_answers(n, d * k)
        t_str, _, _ = format_answers(n * k, d) # Trap: Multiplied instead of divided
        w_str, _, _ = format_answers(n + k, d * k)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def div_int_frac(level):
    while True:
        k = random.randint(2, 5)
        d = random.randint(2, 7)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Oblicz: }} {k} : {format_fraction_question(n, d)}"
        c_str, i_str, u_str = format_answers(k * d, n)
        t_str, _, _ = format_answers(k * n, d) # Trap: Multiplied by top
        w_str, _, _ = format_answers((k * d) + 1, n)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def div_mixed_int(level):
    while True:
        w = random.randint(2, 4)
        d = random.randint(2, 5)
        n = random.randint(1, d - 1)
        k = random.randint(2, 3)
        if w % k != 0: continue # Make sure trap looks believable
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d, w)} : {k}"
        correct_num = (w * d) + n
        c_str, i_str, u_str = format_answers(correct_num, d * k)
        t_str, _, _ = format_answers(n, d, w // k) # Trap: Divided only whole number
        w_str, _, _ = format_answers(correct_num, d)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")