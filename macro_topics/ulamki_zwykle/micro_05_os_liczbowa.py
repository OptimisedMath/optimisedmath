import random
from core.utils import build_problem_dict, generate_universal_number_line

def frac_number_line_1(level):
    d = random.randint(3, 8)
    n = random.randint(1, d - 1)        
    q_str = rf"\text{{Jaki ułamek zaznaczono na osi?}}"
    
    # Standard 0 to 1
    svg_graphic = generate_universal_number_line(d, {0: "0", d: "1"}, n)

    c_str = rf"\frac{{{n}}}{{{d}}}"
    t1 = rf"\frac{{{n+1}}}{{{d+1}}}"        
    t2 = rf"\frac{{{n}}}{{{d+1}}}" 
    w1 = rf"\frac{{{d-n}}}{{{d}}}"        

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, w1=w1, 
        level_name=f"Poziom {level}", 
        image_html=svg_graphic, 
        grading_policy="equivalent_accepted"
    )
    if result: return result

def frac_number_line_2(level):
    d = random.randint(3, 8)
    n = random.randint(1, d - 1)
    W = random.randint(1, 5)        
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"
    
    # Mixed number between W and W+1
    svg_graphic = generate_universal_number_line(d, {0: str(W), d: str(W+1)}, n)

    c_str = rf"{W}\frac{{{n}}}{{{d}}}"
    t1 = rf"{W}\frac{{{n+1}}}{{{d+1}}}"        
    t2 = rf"{W+1}\frac{{{n}}}{{{d}}}" 
    w1 = rf"{W}\frac{{{d-n}}}{{{d}}}"        

    result = build_problem_dict(
        q_str, c_str, t1=t1, t2=t2, w1=w1, 
        level_name=f"Poziom {level}", 
        image_html=svg_graphic, 
        grading_policy="equivalent_accepted"
    )
    if result: return result

def frac_number_line_3(level):
    # Level 3: Decrypt the Axis (Gap > 1)
    d = random.choice([2, 3, 4])
    D = random.choice([2, 3]) # Difference between integer labels (e.g., 2 means labels are 1 and 3)
    gap = d * D
    
    total_ticks = gap + random.randint(2, 4)
    if total_ticks > 15: total_ticks = 15
    
    idx1 = random.randint(1, 2)
    idx2 = idx1 + gap
    W = random.randint(1, 5)

    labeled = {idx1: str(W), idx2: str(W + D)}
    
    valid_targets = [i for i in range(idx1 + 1, total_ticks + 1) if (i - idx1) % d != 0 and i != idx2]
    if not valid_targets: return None
    target = random.choice(valid_targets)        
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"
    
    svg_graphic = generate_universal_number_line(total_ticks, labeled, target)

    ticks_from_W = target - idx1
    whole = W + (ticks_from_W // d)
    num = ticks_from_W % d

    c_str = rf"{whole}\frac{{{num}}}{{{d}}}"

    # Trap 1: Assumed the gap between the two labels is just "1" whole number
    t1_num = ticks_from_W
    t1_whole = W
    if t1_num > gap:
        t1_whole += t1_num // gap
        t1_num = t1_num % gap
    t1 = rf"{t1_whole}\frac{{{t1_num}}}{{{gap}}}"

    # Trap 2: Off by one tick
    num2 = num + 1
    whole2 = whole
    if num2 == d:
        num2 = 1
        whole2 += 1
    t2 = rf"{whole2}\frac{{{num2}}}{{{d}}}"

    # Trap 3: Guessed the wrong whole number
    w1_whole = W if whole != W else W + 1
    w1 = rf"{w1_whole}\frac{{{num}}}{{{d}}}"
    
    if len({c_str, t1, t2, w1}) == 4:
        result = build_problem_dict(
            q_str, c_str, t1=t1, t2=t2, w1=w1, 
            level_name=f"Poziom {level}", 
            image_html=svg_graphic, 
            grading_policy="equivalent_accepted"
        )
        if result: return result

def frac_number_line_4(level):
    # Level 4: Extrapolation (Target is outside the labeled bounds)
    d = random.choice([3, 4, 5])
    W = random.randint(1, 5)
    
    idx1 = random.randint(1, 3)
    idx2 = idx1 + d # Gap is exactly 1 whole number for simplicity
    
    total_ticks = idx2 + random.randint(3, 5)
    if total_ticks > 16: total_ticks = 16
    
    labeled = {idx1: str(W), idx2: str(W + 1)}
    
    # Target MUST be strictly to the right of idx2
    valid_targets = [i for i in range(idx2 + 1, total_ticks + 1) if (i - idx1) % d != 0]
    if not valid_targets: return None
    target = random.choice(valid_targets)        
    q_str = rf"\text{{Jaka liczba zaznaczona jest na osi?}}"
    
    svg_graphic = generate_universal_number_line(total_ticks, labeled, target)
    
    ticks_from_W = target - idx1
    whole = W + (ticks_from_W // d)
    num = ticks_from_W % d
    
    c_str = rf"{whole}\frac{{{num}}}{{{d}}}"
    
    # Trap 1: Started counting from the visual start of the axis instead of idx1
    t1_whole = W + (target // d)
    t1_num = target % d
    if t1_num == 0: t1_num = 1 
    t1 = rf"{t1_whole}\frac{{{t1_num}}}{{{d}}}"
    
    # Trap 2: Off by one tick
    num2 = num + 1
    whole2 = whole
    if num2 == d:
        num2 = 1
        whole2 += 1
    t2 = rf"{whole2}\frac{{{num2}}}{{{d}}}"
    
    # Trap 3: Used total ticks on screen as denominator
    t3_num = num
    t3_whole = whole
    if t3_num >= total_ticks: t3_num = total_ticks - 1
    w1 = rf"{t3_whole}\frac{{{t3_num}}}{{{total_ticks}}}"
    
    if len({c_str, t1, t2, w1}) == 4:
        result = build_problem_dict(
            q_str, c_str, t1=t1, t2=t2, w1=w1, 
            level_name=f"Poziom {level}", 
            image_html=svg_graphic, 
            grading_policy="equivalent_accepted"
        )
        if result: return result