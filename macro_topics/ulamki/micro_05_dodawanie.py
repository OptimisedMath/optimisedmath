import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def add_fractions_simple(level):
    while True:
        den = random.randint(2, 9) if level == 1 else random.randint(10, 20) 
        n1 = random.randint(1, den - 1)
        n2 = random.randint(1, den - 1)
        
        c_str, i_str, u_str = format_answers(n1 + n2, den)
        t_str, _, _ = format_answers(n1 + n2, den + den) 
        w_str, _, _ = format_answers(n1 + n2 + 1, den) 
        
        if len({c_str, t_str, w_str}) == 3:
            q_str = f"Oblicz: {format_fraction_question(n1, den)} + {format_fraction_question(n2, den)}"
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def add_fractions_single_conversion(level):
    pairs = [(2, 4), (2, 6), (2, 8), (3, 6), (3, 9), (4, 8), (5, 10)]
    while True:
        d1, d2 = random.choice(pairs)
        if random.choice([True, False]): d1, d2 = d2, d1
            
        smaller_d, larger_d = min(d1, d2), max(d1, d2)
        scale = larger_d // smaller_d
        
        n_smaller = random.randint(1, smaller_d - 1)
        n_larger = random.randint(1, larger_d - 1)
        
        correct_num = (n_smaller * scale) + n_larger
        n1, n2 = (n_smaller, n_larger) if d1 == smaller_d else (n_larger, n_smaller)
            
        c_str, i_str, u_str = format_answers(correct_num, larger_d)
        t_str, _, _ = format_answers(n1 + n2, larger_d)
        w_str, _, _ = format_answers(n1 * n2, larger_d)
        
        if len({c_str, t_str, w_str}) == 3:
            q_str = f"Oblicz: {format_fraction_question(n1, d1)} + {format_fraction_question(n2, d2)}"
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}: Rozszerzanie jednego ułamka")

def add_fractions_complex(level):
    pairs = [(2, 3), (2, 5), (3, 4), (3, 5), (4, 5)]
    while True:
        d1, d2 = random.choice(pairs)
        if random.choice([True, False]): d1, d2 = d2, d1
            
        n1 = random.randint(1, d1 - 1)
        n2 = random.randint(1, d2 - 1)
        
        common_den = d1 * d2
        correct_num = (n1 * d2) + (n2 * d1)
        
        c_str, i_str, u_str = format_answers(correct_num, common_den)
        t_str, _, _ = format_answers(n1 + n2, d1 + d2)
        w_str, _, _ = format_answers(n1 + n2, common_den)
        
        if len({c_str, t_str, w_str}) == 3:
            q_str = f"Oblicz: {format_fraction_question(n1, d1)} + {format_fraction_question(n2, d2)}"
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}: Różne mianowniki")

def add_mixed_numbers_simple(level):
    while True:
        den = random.randint(3, 9)
        w1, w2 = random.randint(1, 5), random.randint(1, 5)
        n1 = random.randint(1, den - 2)
        n2 = random.randint(1, den - n1 - 1) 
        
        correct_whole = w1 + w2
        correct_numerator = n1 + n2
        
        improper1_num = w1 * den + n1
        improper2_num = w2 * den + n2
        wrong_improper_sum = improper1_num + improper2_num + 1 
        
        c_str, i_str, u_str = format_answers(correct_numerator, den, correct_whole)
        t_str, _, _ = format_answers(n1 + n2, den + den, w1 + w2)
        w_str, _, _ = format_answers(wrong_improper_sum, den)
        
        if len({c_str, t_str, w_str}) == 3:
            q_str = f"Oblicz: {format_fraction_question(n1, den, w1)} + {format_fraction_question(n2, den, w2)}"
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}: Liczby mieszane (Łatwe)")

def add_mixed_numbers_complex(level):
    pairs = [(2, 3), (2, 5), (3, 4), (3, 5), (4, 5)]
    while True:
        d1, d2 = random.choice(pairs)
        w1, w2 = random.randint(1, 3), random.randint(1, 3)
        common_den = d1 * d2
        
        while True:
            n1 = random.randint(1, d1 - 1)
            n2 = random.randint(1, d2 - 1)
            if (n1 * d2 + n2 * d1) > common_den: break
        
        correct_num = (n1 * d2) + (n2 * d1)
        
        c_str, i_str, u_str = format_answers(correct_num, common_den, w1 + w2)
        t_str, _, _ = format_answers(n1 + n2, common_den, w1 + w2)
        w_str, _, _ = format_answers(n1 + n2, d1 + d2, w1 + w2)
        
        if len({c_str, t_str, w_str}) == 3:
            q_str = f"Oblicz: {format_fraction_question(n1, d1, w1)} + {format_fraction_question(n2, d2, w2)}"
            return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}: Liczby mieszane (Ostateczny boss)")
