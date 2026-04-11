import random
from core.utils import format_fraction_question, build_problem_dict

def mixed_to_improper(level):
    while True:
        w = random.randint(1, 5)
        d = random.randint(2, 9)
        n = random.randint(1, d - 1)
        
        q_str = rf"\text{{Zamień na ułamek niewłaściwy: }} {format_fraction_question(n, d, w)}"
        
        # Correct: (Whole * Denominator) + Numerator
        correct_num = (w * d) + n
        c_str = rf"\frac{{{correct_num}}}{{{d}}}"
        
        # TRAP: Multiplied the numerator instead of adding it -> (w * d) * n
        trap_num = (w * d) * n
        t_str = rf"\frac{{{trap_num}}}{{{d}}}"
        
        # WRONG: Simple math error in the addition
        wrong_num = correct_num + random.choice([-1, 1])
        if wrong_num == trap_num:
            wrong_num += 1
        w_str = rf"\frac{{{wrong_num}}}{{{d}}}"
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Zamiana na ułamek niewłaściwy")


def improper_to_mixed(level):
    while True:
        w = random.randint(1, 5)
        d = random.randint(2, 9)
        n = random.randint(1, d - 1)
        
        # Build the starting improper fraction
        start_n = (w * d) + n
        q_str = rf"\text{{Wyłącz całości z ułamka: }} \frac{{{start_n}}}{{{d}}}"
        
        # Correct: Proper mixed number
        c_str = format_fraction_question(n, d, w)
        
        # TRAP: Forgot the remainder entirely, just outputs the whole number
        t_str = str(w) 
        
        # WRONG: Miscalculated the whole number by 1
        wrong_w = w + random.choice([-1, 1])
        if wrong_w < 1: 
            wrong_w = w + 2
        w_str = format_fraction_question(n, d, wrong_w)
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Wyłączanie całości")