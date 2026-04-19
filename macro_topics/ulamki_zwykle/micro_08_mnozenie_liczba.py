import random
import math
from core.utils import format_answers, format_fraction_question, build_problem_dict

def frac_mult_num_1():
    d = random.randint(3, 9)
    n = random.randint(1, d - 1)
    k = random.randint(2, 5)
    if math.gcd(d, k) > 1: return None 
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \cdot {k}"
    
    c_str, _, _ = format_answers(n * k, d)
    t1, _, _ = format_answers(n * k, d * k) 
    t2, _, _ = format_answers(n, d * k) 
    w1, _, _ = format_answers(n * k + 1, d)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, )
    if result: return result

def frac_mult_num_2():
    k = random.randint(2, 6)
    factor = random.randint(2, 4)
    d = k * factor
    n = random.randint(1, d - 1)
    if math.gcd(n, d) > 1: return None
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} \cdot {k}"
    
    c_str, _, _ = format_answers(n * k, d)
    t1 = rf"\frac{{{n * k}}}{{{d}}}" 
    t2, _, _ = format_answers(1, factor) 
    w1, _, _ = format_answers(n * k + 1, d)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, )
    if result: return result

def frac_mult_num_3():
    w = random.randint(1, 3)
    d = random.randint(2, 5)
    n = random.randint(1, d - 1)
    k = random.randint(2, 4)
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d, w)} \cdot {k}"
    
    c_str, _, _ = format_answers(((w * d) + n) * k, d)
    t1, _, _ = format_answers(n * k, d, w) 
    t2, _, _ = format_answers(((w * d) + n) * k, d * k) 
    w1, _, _ = format_answers(((w * d) + n) * k + 1, d)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, )
    if result: return result