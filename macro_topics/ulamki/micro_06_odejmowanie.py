import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def subtract_fractions_simple(level):
    while True:
        den = random.randint(3, 9) if level == 1 else random.randint(10, 20) 
        n1 = random.randint(2, den - 1)
        n2 = random.randint(1, n1 - 1) 
        
        c_str, i_str, u_str = format_answers(n1 - n2, den)
        
        trap_num = n1 - n2
        t_str = rf"\frac{{{trap_num}}}{{0}}" 
        
        error = random.choice([-1, 1])
        wrong_num = (n1 - n2) + error
        if wrong_num <= 0: 
            wrong_num = (n1 - n2) + 1 
            
        w_str, _, _ = format_answers(wrong_num, den) 
        
        if len({c_str, t_str, w_str}) == 3:
            q_str = f"Oblicz: {format_fraction_question(n1, den)} - {format_fraction_question(n2, den)}"
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}: Odejmowanie")

def subtract_fractions_single_conversion(level):
    pairs = [(2, 4), (2, 6), (2, 8), (3, 6), (3, 9), (4, 8), (5, 10)]
    while True:
        d1, d2 = random.choice(pairs)
        
        smaller_d, larger_d = min(d1, d2), max(d1, d2)
        n_smaller = random.randint(1, smaller_d - 1)
        n_larger = random.randint(1, larger_d - 1)
        
        val_small = n_smaller / smaller_d
        val_large = n_larger / larger_d
        
        if val_small == val_large: 
            continue 
            
        if val_small > val_large:
            n1, d1 = n_smaller, smaller_d
            n2, d2 = n_larger, larger_d
        else:
            n1, d1 = n_larger, larger_d
            n2, d2 = n_smaller, smaller_d
            
        num1_scaled = n1 * (larger_d // d1)
        num2_scaled = n2 * (larger_d // d2)
        
        c_str, i_str, u_str = format_answers(num1_scaled - num2_scaled, larger_d)
        
        trap_num = abs(n1 - n2) or 1 
        t_str, _, _ = format_answers(trap_num, larger_d)
        
        w_str, _, _ = format_answers(n1 * n2, larger_d)
        
        if len({c_str, t_str, w_str}) == 3:
            q_str = f"Oblicz: {format_fraction_question(n1, d1)} - {format_fraction_question(n2, d2)}"
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}: Pojedyncze rozszerzenie")