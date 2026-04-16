import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def expand_fraction_by_factor(level):
    while True:
        d = random.randint(2, 9)
        n = random.randint(1, d * 2)
        if n == d: continue
        factor = random.randint(2, 6)
        
        q_str = rf"\text{{Rozszerz ułamek }} {format_fraction_question(n, d)} \text{{ przez }} {factor}."
        
        c_str = rf"\frac{{{n * factor}}}{{{d * factor}}}"
        t1 = rf"\frac{{{n * factor}}}{{{d}}}"        
        t2 = rf"\frac{{{n}}}{{{d * factor}}}"        
        t3 = rf"\frac{{{n + factor}}}{{{d + factor}}}" 
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}", grading_policy="exact_match_only")
        if result: return result

def expand_fraction_to_denominator(level):
    while True:
        d = random.randint(2, 9)
        n = random.randint(1, d * 2)
        if n == d: continue
        factor = random.randint(2, 6)
        target_d = d * factor
        
        q_str = rf"\text{{Rozszerz ułamek }} {format_fraction_question(n, d)} \text{{ tak, aby w mianowniku było }} {target_d}."
        
        c_str = rf"\frac{{{n * factor}}}{{{target_d}}}"
        t1 = rf"\frac{{{n}}}{{{target_d}}}" 
        
        wrong_factor = factor + random.choice([-1, 1])
        if wrong_factor < 1: wrong_factor = factor + 2
        t2 = rf"\frac{{{n * wrong_factor}}}{{{target_d}}}"
        
        w1 = rf"\frac{{{n * factor + random.choice([-1, 1])}}}{{{target_d}}}" 
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", grading_policy="exact_match_only")
        if result: return result

def simplify_fraction_by_factor(level):
    while True:
        d = random.randint(2, 9)
        n = random.randint(1, d * 2)
        if n == d: continue
        factor = random.randint(2, 6)
        
        start_n = n * factor
        start_d = d * factor
        
        q_str = rf"\text{{Skróć ułamek }} {format_fraction_question(start_n, start_d)} \text{{ przez }} {factor}."
        
        c_str = rf"\frac{{{n}}}{{{d}}}"
        t1 = rf"\frac{{{n}}}{{{start_d}}}" 
        t2 = rf"\frac{{{start_n}}}{{{d}}}" 
        t3 = rf"\frac{{{max(1, start_n - factor)}}}{{{max(2, start_d - factor)}}}"
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}", grading_policy="exact_match_only")
        if result: return result

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
        
        c_str = rf"\frac{{{n}}}{{{d}}}"
        t1 = rf"\frac{{{n * factor2}}}{{{d * factor2}}}" 
        t2 = rf"\frac{{{n}}}{{{d * factor2}}}" 
        t3 = rf"\frac{{{n * factor2}}}{{{d}}}" 
        
        result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}", grading_policy="exact_match_only")
        if result: return result