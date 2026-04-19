import random
from core.utils import build_problem_dict, fmt_dec

def dec_order_1():
    # Poziom 1: Mnożenie/Dzielenie vs Dodawanie/Odejmowanie (bez nawiasów)
    template = random.choice(["add_mul", "sub_div", "mul_sub"])
    
    if template == "add_mul":
        a = round(random.randint(1, 5) * 0.1, 1)
        b = round(random.randint(2, 5) * 0.1, 1)
        c = round(random.randint(2, 5) * 0.1, 1)
        q = f"{fmt_dec(a)} + {fmt_dec(b)} \\cdot {fmt_dec(c)}"
        ans = fmt_dec(a + (b * c))
        trap1 = fmt_dec((a + b) * c)
        
    elif template == "sub_div":
        c = round(random.randint(2, 5) * 0.1, 1)
        ans_div = round(random.randint(2, 5) * 0.1, 1)
        b = round(ans_div * c, 2)
        a = round(random.randint(10, 20) * 0.1, 1)
        q = f"{fmt_dec(a)} - {fmt_dec(b)} : {fmt_dec(c)}"
        ans = fmt_dec(a - ans_div)
        trap1 = fmt_dec((a - b) / c) if c != 0 else fmt_dec(0)
        
    else: # mul_sub
        a = round(random.randint(2, 6) * 0.1, 1)
        b = round(random.randint(2, 6) * 0.1, 1)
        c = round(random.randint(1, 5) * 0.1, 1)
        q = f"{fmt_dec(a)} \\cdot {fmt_dec(b)} - {fmt_dec(c)}"
        ans = fmt_dec((a * b) - c)
        trap1 = fmt_dec(a * (b - c))
        
    return build_problem_dict(q, ans, t1=trap1)

def dec_order_2():
    # Poziom 2: Nawiasy
    template = random.choice(["brack_mul", "mul_brack"])
    
    if template == "brack_mul":
        a = round(random.randint(1, 5) * 0.1, 1)
        b = round(random.randint(1, 5) * 0.1, 1)
        c = round(random.randint(2, 6) * 0.1, 1)
        q = f"({fmt_dec(a)} + {fmt_dec(b)}) \\cdot {fmt_dec(c)}"
        ans = fmt_dec((a + b) * c)
        trap1 = fmt_dec(a + (b * c))
        
    else: # mul_brack
        a = round(random.randint(2, 6) * 0.1, 1)
        b = round(random.randint(5, 9) * 0.1, 1)
        c = round(random.randint(1, 4) * 0.1, 1)
        q = f"{fmt_dec(a)} \\cdot ({fmt_dec(b)} - {fmt_dec(c)})"
        ans = fmt_dec(a * (b - c))
        trap1 = fmt_dec((a * b) - c)
        
    return build_problem_dict(q, ans, t1=trap1)

def dec_order_3():
    # Poziom 3: Potęgi
    template = random.choice(["pow_add", "sub_pow"])
    
    if template == "pow_add":
        a = round(random.randint(2, 5) * 0.1, 1)
        b = round(random.randint(2, 5) * 0.1, 1)
        c = round(random.randint(2, 5) * 0.1, 1)
        q = f"{fmt_dec(a)}^2 + {fmt_dec(b)} \\cdot {fmt_dec(c)}"
        ans = fmt_dec((a**2) + (b * c))
        trap1 = fmt_dec(((a**2) + b) * c)
        trap2 = fmt_dec((a**2) + b + c)
        
    else: # sub_pow
        a = round(random.randint(10, 20) * 0.1, 1)
        b = round(random.randint(2, 5) * 0.1, 1)
        q = f"{fmt_dec(a)} - {fmt_dec(b)}^2"
        ans = fmt_dec(a - (b**2))
        trap1 = fmt_dec((a - b)**2)
        trap2 = fmt_dec(a - (b * 2))
        
    return build_problem_dict(q, ans, t1=trap1, t2=trap2)

def dec_order_4():
    # Poziom 4: Nawiasy i Potęgi razem (Boss Level)
    a = round(random.randint(1, 4) * 0.1, 1)
    b = round(random.randint(1, 4) * 0.1, 1)
    c = round(random.randint(2, 5) * 0.1, 1)
    
    q = f"({fmt_dec(a)} + {fmt_dec(b)})^2 - {fmt_dec(c)}"
    ans = fmt_dec(((a + b)**2) - c)
    trap1 = fmt_dec((a**2) + (b**2) - c)
    trap2 = fmt_dec((a + b) * 2 - c)
    
    return build_problem_dict(q, ans, t1=trap1, t2=trap2)