import random
from core.utils import build_problem_dict, fmt_dec, generate_universal_number_line

def number_line_l1(level):
    while True:
        # Level 1: Absolute basics. 10 ticks, whole numbers. Step is always 0.1.
        base = random.randint(0, 20)
        target = random.randint(1, 9)
        step = 0.1
        
        c_val = base + target * step
        
        labeled = {0: str(base), 10: str(base + 1)}
        svg_graphic = generate_universal_number_line(10, labeled, target)
        
        hidden_id = r" \kern0pt" * ((base * 10) + target)
        q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}{hidden_id}"
        
        c_str = fmt_dec(round(c_val, 1))
        t1 = fmt_dec(round(base + target * 0.01, 2)) # Trap: Wrote 2.03 instead of 2.3
        t2 = fmt_dec(round(c_val + step, 1))         # Trap: Off by one tick
        w1_target = 10 - target if target != 5 else 6
        w1 = fmt_dec(round(base + w1_target * step, 1)) # Trap: Counted from the right
        
        if len({c_str, t1, t2, w1}) == 4:
            result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", image_html=svg_graphic)
            if result: return result

def number_line_l2(level):
    while True:
        # Level 2: 10 ticks, but with decimals (hundredths and thousandths). Step 0.01 or 0.001.
        step = random.choice([0.01, 0.001])
        base_mult = random.randint(1, 99)
        if base_mult % 10 == 0: base_mult += 1
        base = base_mult * (step * 10)
        
        target = random.randint(1, 9)
        c_val = base + target * step
        
        labeled = {0: fmt_dec(round(base, 3)), 10: fmt_dec(round(base + 10 * step, 3))}
        svg_graphic = generate_universal_number_line(10, labeled, target)
        
        hidden_id = r" \kern0pt" * random.randint(1, 1000)
        q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}{hidden_id}"
        
        c_str = fmt_dec(round(c_val, 4))
        t1 = fmt_dec(round(base + target * (step / 10), 5)) # Trap: Wrong magnitude
        t2 = fmt_dec(round(c_val + step, 4))
        w1_target = 10 - target if target != 5 else 6
        w1 = fmt_dec(round(base + w1_target * step, 4))
        
        if len({c_str, t1, t2, w1}) == 4:
            result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", image_html=svg_graphic)
            if result: return result

def number_line_l3(level):
    while True:
        # Level 3: Easy Scale Intro. 5 ticks, whole numbers. Step is 0.2.
        ticks = 5
        step = 0.2
        base = random.randint(0, 20)
        
        target = random.randint(1, 4)
        c_val = base + target * step
        
        labeled = {0: str(base), ticks: str(base + 1)}
        svg_graphic = generate_universal_number_line(ticks, labeled, target)
        
        hidden_id = r" \kern0pt" * random.randint(1, 1000)
        q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}{hidden_id}"
        
        c_str = fmt_dec(round(c_val, 1))
        t1 = fmt_dec(round(base + target * 0.1, 1)) # Trap: Assumed default 0.1 step
        t2 = fmt_dec(round(c_val + step, 1))
        w1_target = ticks - target if ticks - target != target else target + 1
        w1 = fmt_dec(round(base + w1_target * step, 1))
        
        if len({c_str, t1, t2, w1}) == 4:
            result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", image_html=svg_graphic)
            if result: return result

def number_line_l4(level):
    while True:
        # Level 4: Advanced Scale. 4 or 5 ticks, decimal numbers.
        ticks = random.choice([4, 5])
        step = 0.02 if ticks == 5 else 0.025
        base = random.randint(1, 50) * 0.1
        
        target = random.randint(1, ticks - 1)
        c_val = base + target * step
        
        labeled = {0: fmt_dec(round(base, 2)), ticks: fmt_dec(round(base + ticks * step, 2))}
        svg_graphic = generate_universal_number_line(ticks, labeled, target)
        
        hidden_id = r" \kern0pt" * random.randint(1, 1000)
        q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}{hidden_id}"
        
        c_str = fmt_dec(round(c_val, 3))
        t1 = fmt_dec(round(base + target * 0.01, 3)) # Trap: Assumed default 0.01 step
        t2 = fmt_dec(round(c_val + step, 3))
        w1_target = ticks - target if ticks - target != target else target + 1
        w1 = fmt_dec(round(base + w1_target * step, 3))
        
        if len({c_str, t1, t2, w1}) == 4:
            result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", image_html=svg_graphic)
            if result: return result

def number_line_l5(level):
    while True:
        # Level 5: Extrapolation. 10 ticks, target is outside bounds.
        ticks = 10
        step = random.choice([0.1, 0.01])
        base = random.randint(1, 50) * step
        
        idx1 = random.randint(1, 3)
        idx2 = idx1 + random.randint(1, 2)
        target = random.randint(idx2 + 2, 9)
        c_val = base + target * step
        
        labeled = {idx1: fmt_dec(round(base + idx1 * step, 3)), idx2: fmt_dec(round(base + idx2 * step, 3))}
        svg_graphic = generate_universal_number_line(ticks, labeled, target)
        
        hidden_id = r" \kern0pt" * random.randint(1, 1000)
        q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}{hidden_id}"
        
        c_str = fmt_dec(round(c_val, 3))
        t1 = fmt_dec(round(base + idx2 * step + (target - idx2) * step * 2, 3)) # Miscalculated gap size
        t2 = fmt_dec(round(c_val + step, 3))
        w1 = fmt_dec(round(base + target * step * 2, 3)) # Added distance from 0 instead of idx1
        
        if len({c_str, t1, t2, w1}) == 4:
            result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", image_html=svg_graphic)
            if result: return result

def number_line_l6(level):
    while True:
        # Level 6: Exam Boss. Scattered labels, calculate the step.
        ticks = 10
        step = random.choice([0.1, 0.2, 0.05])
        base = random.randint(1, 50) * step
        
        idx1 = random.randint(0, 2)
        idx2 = random.randint(6, 8)
        target = random.choice([x for x in range(3, 10) if x not in [idx1, idx2]])
        c_val = base + target * step
        
        labeled = {idx1: fmt_dec(round(base + idx1 * step, 3)), idx2: fmt_dec(round(base + idx2 * step, 3))}
        svg_graphic = generate_universal_number_line(ticks, labeled, target)
        
        hidden_id = r" \kern0pt" * random.randint(1, 1000)
        q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}{hidden_id}"
        
        c_str = fmt_dec(round(c_val, 3))
        t1 = fmt_dec(round(c_val + step, 3))
        t2 = fmt_dec(round(base + idx1 * step + (target - idx1) * 0.1, 3)) # Default step trap
        w1 = fmt_dec(round(c_val - step, 3))
        
        if len({c_str, t1, t2, w1}) == 4:
            result = build_problem_dict(q_str, c_str, t1=t1, t2=t2, w1=w1, level_name=f"Poziom {level}", image_html=svg_graphic)
            if result: return result