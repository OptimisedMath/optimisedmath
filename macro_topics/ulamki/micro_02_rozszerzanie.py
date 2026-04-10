import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def expand_fraction_by_factor(level):
    while True:
        d = random.randint(2, 9)
        n = random.randint(1, d * 2) # Allows both proper and improper
        if n == d: continue
        factor = random.randint(2, 6)
        
        q_str = rf"\text{{Rozszerz ułamek }} {format_fraction_question(n, d)} \text{{ przez }} {factor}."
        
        # --- MANUAL FORMATTING (Bypasses automatic simplification) ---
        c_str = rf"\frac{{{n * factor}}}{{{d * factor}}}"
        t_str = rf"\frac{{{n * factor}}}{{{d}}}" 
        w_str = rf"\frac{{{n + factor}}}{{{d + factor}}}" 
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Rozszerzanie przez liczbę")

def expand_fraction_to_denominator(level):
    while True:
        d = random.randint(2, 9)
        n = random.randint(1, d * 2)
        if n == d: continue
        factor = random.randint(2, 6)
        target_d = d * factor
        
        q_str = rf"\text{{Rozszerz ułamek }} {format_fraction_question(n, d)} \text{{ tak, aby w mianowniku było }} {target_d}."
        
        # --- MANUAL FORMATTING ---
        c_str = rf"\frac{{{n * factor}}}{{{target_d}}}"
        t_str = rf"\frac{{{n}}}{{{target_d}}}" 
        w_str = rf"\frac{{{n * (factor + 1)}}}{{{target_d}}}" 
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Rozszerzanie do mianownika")

def simplify_fraction_by_factor(level):
    while True:
        d = random.randint(2, 9)
        n = random.randint(1, d * 2)
        if n == d: continue
        factor = random.randint(2, 6)
        
        start_n = n * factor
        start_d = d * factor
        
        q_str = rf"\text{{Skróć ułamek }} {format_fraction_question(start_n, start_d)} \text{{ przez }} {factor}."
        
        # --- MANUAL FORMATTING ---
        # Ensures a fraction like 4/8 shortened by 2 stays exactly 2/4, instead of auto-simplifying to 1/2
        c_str = rf"\frac{{{n}}}{{{d}}}"
        t_str = rf"\frac{{{n}}}{{{start_d}}}" 
        
        wrong_n = max(1, start_n - factor)
        wrong_d = max(2, start_d - factor)
        w_str = rf"\frac{{{wrong_n}}}{{{wrong_d}}}"
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Skracanie przez liczbę")

def simplify_fraction_fully(level):
    while True:
        d = random.randint(2, 9)
        n = random.randint(1, d * 2)
        if n == d or math.gcd(n, d) > 1: continue 
        
        factor1 = random.randint(2, 4)
        factor2 = random.randint(2, 4)
        total_factor = factor1 * factor2 
        
        start_n = n * total_factor
        start_d = d * total_factor
        
        q_str = rf"\text{{Skróć ułamek }} {format_fraction_question(start_n, start_d)} \text{{ do postaci nieskracalnej.}}"
        
        # --- MANUAL FORMATTING (Prevents improper fractions from becoming mixed numbers) ---
        c_str = rf"\frac{{{n}}}{{{d}}}"
        t_str = rf"\frac{{{n * factor2}}}{{{d * factor2}}}" 
        w_str = rf"\frac{{{d}}}{{{n}}}" 
        
        if len({c_str, t_str, w_str}) == 3:
            return build_problem_dict(q_str, c_str, c_str, c_str, t_str, w_str, f"Poziom {level}: Postać nieskracalna")