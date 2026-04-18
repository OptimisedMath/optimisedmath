import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def add_fractions_simple(level):
    d = random.randint(3, 9)
    n1 = random.randint(1, d - 1)
    n2 = random.randint(1, d - 1)
    
    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d}}} + \frac{{{n2}}}{{{d}}}"
    
    c_str, _, _ = format_answers(n1 + n2, d)
    t1, _, _ = format_answers(n1 + n2, d + d) 
    w1, _, _ = format_answers(n1 + n2 + 1, d) 
    w2, _, _ = format_answers(abs(n1 + n2 - 1), d) 
    
    result = build_problem_dict(q_str, c_str, t1=t1, w1=w1, w2=w2, level_name=f"Poziom {level}")
    if result: return result

def add_fractions_single_conversion(level):
    d1 = random.randint(2, 5)
    factor = random.randint(2, 4)
    d2 = d1 * factor
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    
    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} + \frac{{{n2}}}{{{d2}}}"
    
    c_str, _, _ = format_answers((n1 * factor) + n2, d2)
    t1, _, _ = format_answers(n1 + n2, d2) 
    t2, _, _ = format_answers(n1 + n2, d1 + d2) 
    w1, _, _ = format_answers((n1 * factor) + n2 + 1, d2)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}")
    if result: return result

def add_fractions_complex(level):
    d1, d2 = random.randint(3, 7), random.randint(3, 7)
    if math.gcd(d1, d2) > 1 or d1 == d2: return None
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    
    q_str = rf"\text{{Oblicz: }} \frac{{{n1}}}{{{d1}}} + \frac{{{n2}}}{{{d2}}}"
    
    c_str, _, _ = format_answers((n1 * d2) + (n2 * d1), d1 * d2)
    t1, _, _ = format_answers(n1 + n2, d1 + d2) 
    t2, _, _ = format_answers(n1 + n2, d1 * d2) 
    t3, _, _ = format_answers(n1 * d2 * n2 * d1, d1 * d2) 
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, level_name=f"Poziom {level}")
    if result: return result

def add_mixed_numbers_simple(level):
    w1, w2 = random.randint(1, 3), random.randint(1, 3)
    d = random.randint(3, 7)
    n1, n2 = random.randint(1, d - 1), random.randint(1, d - 1)
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d, w1)} + {format_fraction_question(n2, d, w2)}"
    
    c_str, _, _ = format_answers((w1 * d + n1) + (w2 * d + n2), d)
    t1, _, _ = format_answers(n1 + n2, d + d, w1 + w2) 
    w1_str, _, _ = format_answers((w1 * d + n1) + (w2 * d + n2) + d, d) 
    w2_str, _, _ = format_answers((w1 * d + n1) + (w2 * d + n2) + 1, d) 
    
    result = build_problem_dict(q_str, c_str, t1=t1, w1=w1_str, w2=w2_str, level_name=f"Poziom {level}")
    if result: return result

def add_mixed_numbers_complex(level):
    w1, w2 = random.randint(1, 2), random.randint(1, 2)
    d1, d2 = random.randint(2, 5), random.randint(2, 5)
    if math.gcd(d1, d2) > 1 or d1 == d2: return None
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d1, w1)} + {format_fraction_question(n2, d2, w2)}"
    
    num1, num2 = (w1 * d1) + n1, (w2 * d2) + n2
    c_str, _, _ = format_answers((num1 * d2) + (num2 * d1), d1 * d2)
    t1, _, _ = format_answers(n1 + n2, d1 * d2, w1 + w2) 
    t2, _, _ = format_answers(n1 + n2, d1 + d2, w1 + w2) 
    w1_str, _, _ = format_answers((num1 * d2) + (num2 * d1) + 1, d1 * d2)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1_str, level_name=f"Poziom {level}")
    if result: return result