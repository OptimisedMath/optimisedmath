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
        t1 = rf"\frac{{{n * factor}}}{{{d}}}"        # T1: Multiplied ONLY numerator
        t2 = rf"\frac{{{n}}}{{{d * factor}}}"        # T2: Multiplied ONLY denominator
        t3 = rf"\frac{{{n + factor}}}{{{d + factor}}}" # T3: Added instead of multiplied
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")

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
        t1 = rf"\frac{{{n}}}{{{target_d}}}" # T1: Numerator left unchanged
        
        # T2: Numerator multiplied by wrong factor (off by 1)
        wrong_factor = factor + random.choice([-1, 1])
        if wrong_factor < 1: wrong_factor = factor + 2
        t2 = rf"\frac{{{n * wrong_factor}}}{{{target_d}}}"
        
        # W1: Simple multiplication error in the numerator
        w1 = rf"\frac{{{n * factor + random.choice([-1, 1])}}}{{{target_d}}}" 
        
        if len({c_str, t1, t2, w1}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")

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
        c_str = rf"\frac{{{n}}}{{{d}}}"
        t1 = rf"\frac{{{n}}}{{{start_d}}}" # T1: Divided ONLY numerator
        t2 = rf"\frac{{{start_n}}}{{{d}}}" # T2: Divided ONLY denominator
        
        # T3: Subtracted instead of dividing
        t3 = rf"\frac{{{max(1, start_n - factor)}}}{{{max(2, start_d - factor)}}}"
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")

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
        
        # --- MANUAL FORMATTING ---
        c_str = rf"\frac{{{n}}}{{{d}}}"
        t1 = rf"\frac{{{n * factor2}}}{{{d * factor2}}}" # T1: Partially simplified (divided by factor1, not total_factor)
        
        # T2: Divided top correctly, but divided bottom by the wrong factor (factor1 instead of total_factor)
        t2 = rf"\frac{{{n}}}{{{d * factor2}}}" 
        
        # T3: Divided bottom correctly, but divided top by the wrong factor (factor1 instead of total_factor)
        t3 = rf"\frac{{{n * factor2}}}{{{d}}}" 
        
        if len({c_str, t1, t2, t3}) == 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")