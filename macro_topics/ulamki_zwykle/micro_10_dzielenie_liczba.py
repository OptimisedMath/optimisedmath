import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def frac_div_num_1():
    d = random.randint(2, 7)
    n = random.randint(1, d - 1)
    k = random.randint(2, 5)
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d)} : {k}"
    
    c_str, _, _ = format_answers(n, d * k)
    t1, _, _ = format_answers(n * k, d) 
    t2, _, _ = format_answers(n, d)     
    if d % k == 0: t2, _, _ = format_answers(n, d // k)
    w1, _, _ = format_answers(n + k, d * k)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, )
    if result: return result

def frac_div_num_2():
    k = random.randint(2, 5)
    d = random.randint(2, 7)
    n = random.randint(1, d - 1)
    
    q_str = rf"\text{{Oblicz: }} {k} : {format_fraction_question(n, d)}"
    
    c_str, _, _ = format_answers(k * d, n)
    t1, _, _ = format_answers(k * n, d) 
    t2, _, _ = format_answers(n, k * d) 
    w1, _, _ = format_answers((k * d) + 1, n)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, )
    if result: return result

def frac_div_num_3():
    w = random.randint(2, 4)
    d = random.randint(2, 5)
    n = random.randint(1, d - 1)
    k = random.randint(2, 3)
    if w % k != 0: return None 
    
    q_str = rf"\text{{Oblicz: }} {format_fraction_question(n, d, w)} : {k}"
    
    correct_num = (w * d) + n
    c_str, _, _ = format_answers(correct_num, d * k)
    t1, _, _ = format_answers(n, d, w // k) 
    t2, _, _ = format_answers(correct_num * k, d) 
    w1, _, _ = format_answers(correct_num + 1, d * k)
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, )
    if result: return result