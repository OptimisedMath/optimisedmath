import math
import uuid
import re
from fractions import Fraction
import random

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

def build_problem_dict(q_str, c_str, i_str=None, u_str=None, t1=None, t2=None, t3=None, w1=None, w2=None, level_name="", grading_policy="standard"):
    """
    Packages strings into a UI dictionary while mapping them to specific message IDs.
    grading_policy options: "standard", "exact_match_only", "equivalent_accepted"
    """
    # Defensive fix: If old functions passed 'Poziom...' into one of the wrong answer slots positionally, shift it.
    opts = [t1, t2, t3, w1, w2]
    real_opts = []
    for opt in opts:
        if isinstance(opt, str) and opt.startswith("Poziom"):
            level_name = opt
        else:
            real_opts.append(opt)
            
    t1, t2, t3, w1, w2 = (real_opts + [None]*5)[:5]

    # Map the generated strings to their internal ID
    options_map = {}
    if c_str is not None: options_map[c_str] = "correct"
    if t1 is not None: options_map[t1] = "t1"
    if t2 is not None: options_map[t2] = "t2"
    if t3 is not None: options_map[t3] = "t3"
    if w1 is not None: options_map[w1] = "w1"
    if w2 is not None: options_map[w2] = "w2"
    
    options = list(options_map.keys())
    random.shuffle(options)
    
    return {
        'problem_id': str(uuid.uuid4()),
        'question': q_str,
        'correct': c_str,
        'improper': i_str,     
        'unsimplified': u_str, 
        'options': options,
        'options_map': options_map, # Contains the exact ID mapping for the UI
        'level_name': level_name,
        'grading_policy': grading_policy # <-- The Engine reads this!
    }

def clean_latex(latex_str):
    """Converts the database LaTeX string into a normal text string (e.g., \frac{1}{2} -> 1/2)"""
    s = latex_str.replace("$\\displaystyle", "").replace("$", "").strip()
    s = re.sub(r'\\frac\{(\d+)\}\{(\d+)\}', r'\1/\2', s)
    return s.strip()

def parse_to_fraction(val_str):
    """Safely converts either a LaTeX string or a user's text input into a mathematical Fraction object."""
    try:
        # Convert decimal strings like "0,6" or "0.6" into a fraction so Decimals engine can grade them properly
        if "," in val_str or "." in val_str:
            clean_val = val_str.replace(",", ".").strip()
            return Fraction(clean_val)

        if "displaystyle" in val_str or "\\frac" in val_str:
            val_str = clean_latex(val_str)
        
        val_str = val_str.strip()
        
        # Handle mixed numbers (e.g., "1 1/2")
        if " " in val_str:
            parts = val_str.split(" ")
            if len(parts) == 2 and "/" in parts[1]:
                whole = int(parts[0])
                frac = Fraction(parts[1])
                # Convert to improper fraction math
                if whole >= 0:
                    return Fraction(whole * frac.denominator + frac.numerator, frac.denominator)
                else:
                    return Fraction(whole * frac.denominator - frac.numerator, frac.denominator)
        
        # Handle standard fractions or whole numbers
        return Fraction(val_str)
    except Exception:
        return None

def check_text_answer(correct_latex, user_text):
    """Checks if the user's text perfectly matches the correct answer string (ignoring spaces)."""
    clean_correct = clean_latex(correct_latex).replace(" ", "")
    clean_user = user_text.replace(" ", "")
    return clean_correct == clean_user

def fmt_dec(val):
    """Formats a Python float/decimal into a Polish string (e.g., 2.5 -> 2,5)"""
    # Remove unnecessary trailing zeros and decimal points for whole numbers
    s = f"{val:g}" 
    return s.replace(".", ",")