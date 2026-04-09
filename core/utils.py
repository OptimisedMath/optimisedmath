import math
import uuid

def format_answers(num, den, whole=0):
    total_num = (whole * den) + num
    u_str = str(total_num) if den == 1 else rf"\frac{{{total_num}}}{{{den}}}"

    divisor = math.gcd(total_num, den)
    simp_num = total_num // divisor
    simp_den = den // divisor
    
    i_str = str(simp_num) if simp_den == 1 else rf"\frac{{{simp_num}}}{{{simp_den}}}"

    final_whole = simp_num // simp_den
    final_num = simp_num % simp_den
    
    if final_num == 0:
        c_str = str(final_whole) 
    elif final_whole > 0:
        c_str = rf"{final_whole}\frac{{{final_num}}}{{{simp_den}}}" 
    else:
        c_str = rf"\frac{{{final_num}}}{{{simp_den}}}" 
        
    return c_str, i_str, u_str

def format_fraction_question(n, d, w=None):
    if w is not None and w > 0:
        return rf"{w}\frac{{{n}}}{{{d}}}"
    else:
        return rf"\frac{{{n}}}{{{d}}}"

def build_problem_dict(question_str, c_str, i_str, u_str, t_str, w_str, level_display):
    return {
        "problem_id": str(uuid.uuid4()),
        "question": question_str,
        "correct": f"$\\displaystyle {c_str}$",
        "improper": f"$\\displaystyle {i_str}$",
        "unsimplified": f"$\\displaystyle {u_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": level_display 
    }