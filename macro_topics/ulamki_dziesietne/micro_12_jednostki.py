import random
from core.utils import build_problem_dict, fmt_dec

def dec_unit_1():
    v = random.randint(2, 99)
    pairs = [("mm", "cm", 10), ("cm", "m", 100), ("m", "km", 1000)]
    unit_in, unit_out, factor = random.choice(pairs)
    
    q_str = rf"\text{{Zamień: }} {v} \text{{ }} {unit_in} = \_\_\_ \text{{ }} {unit_out}"
    c_str = fmt_dec(round(v / factor, 4))
    
    t1 = fmt_dec(round(v / (factor / 10 if factor > 10 else 100), 4))
    t2 = fmt_dec(round(v * factor, 2))
    t3 = f"{v}00"
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, )
    if result: return result

def dec_unit_2():
    v = random.randint(2, 99)
    pairs = [("g", "dag", 10), ("dag", "kg", 100), ("g", "kg", 1000)]
    unit_in, unit_out, factor = random.choice(pairs)
    
    q_str = rf"\text{{Zamień: }} {v} \text{{ }} {unit_in} = \_\_\_ \text{{ }} {unit_out}"
    c_str = fmt_dec(round(v / factor, 4))
    
    t1 = fmt_dec(round(v / (factor * 10 if factor == 100 else 100), 4))
    t2 = fmt_dec(round(v / 10, 4)) if factor == 100 else fmt_dec(round(v / 100, 4))
    t3 = fmt_dec(round(v / 10, 2))
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, )
    if result: return result

def dec_unit_3():
    zl = random.randint(2, 15)
    gr = random.randint(1, 9) # Single digit grosze forces the "0" trap (e.g. 5.08)
    
    q_str = rf"\text{{Zamień na złote: }} {zl} \text{{ zł }} {gr} \text{{ gr}}"
    c_str = fmt_dec(zl + (gr / 100))
    
    t1 = fmt_dec(zl + (gr / 10)) # Trap: 5.8 instead of 5.08
    t2 = f"{zl},{gr}0"
    w1 = fmt_dec(zl + ((gr + 1) / 100))
    
    result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, )
    if result: return result