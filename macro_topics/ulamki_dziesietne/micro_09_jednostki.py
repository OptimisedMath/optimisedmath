import random
from core.utils import build_problem_dict, fmt_dec

def unit_len(level):
    while True:
        v = random.randint(2, 99)
        pairs = [("mm", "cm", 10), ("cm", "m", 100), ("m", "km", 1000)]
        unit_in, unit_out, factor = random.choice(pairs)
        
        q_str = rf"\text{{Zamień: }} {v} \text{{ }} {unit_in} = \_\_\_ \text{{ }} {unit_out}"
        c_str = fmt_dec(round(v / factor, 4))
        
        t1 = fmt_dec(round(v / (factor / 10 if factor > 10 else 100), 4)) # Trap 1: Wrong multiplier
        t2 = fmt_dec(round(v * factor, 2)) # Trap 2: Wrong direction
        t3 = f"{v}00" # Trap 3: Just added zeros
        w1 = fmt_dec(round(v / (factor * 10), 4))
        
        if len({c_str, t1, t2, t3, w1}) >= 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, w1=w1, level_name=f"Poziom {level}")

def unit_mass(level):
    while True:
        v = random.randint(2, 99)
        pairs = [("g", "dag", 10), ("dag", "kg", 100), ("g", "kg", 1000)]
        unit_in, unit_out, factor = random.choice(pairs)
        
        q_str = rf"\text{{Zamień: }} {v} \text{{ }} {unit_in} = \_\_\_ \text{{ }} {unit_out}"
        c_str = fmt_dec(round(v / factor, 4))
        
        t1 = fmt_dec(round(v / (factor * 10 if factor == 100 else 100), 4)) # Trap 1: Wrong multiplier
        t2 = fmt_dec(round(v / 10, 4)) if factor == 100 else fmt_dec(round(v / 100, 4)) # Trap 2: dag to kg classic trap
        t3 = fmt_dec(round(v / 10, 2)) # Trap 3: Small values ignore comma
        w1 = fmt_dec(round(v * factor, 2))
        
        if len({c_str, t1, t2, t3, w1}) >= 4:
            return build_problem_dict(q_str, c_str, t1=t1, t2=t2, t3=t3, w1=w1, level_name=f"Poziom {level}")