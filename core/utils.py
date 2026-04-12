import math
import uuid
import re
from fractions import Fraction
import streamlit.components.v1 as components
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

def build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str=None, w2_str=None, level_name=""):
    """
    Packages the generated strings into a dictionary for the UI.
    Dynamically supports 2, 3, or 4 options by filtering out None values.
    """
    raw_options = [c_str, t_str, w_str, w2_str]
    # Filter out None and remove duplicates, then shuffle
    options = list(set([opt for opt in raw_options if opt is not None]))
    random.shuffle(options)
    
    return {
        'problem_id': str(uuid.uuid4()),
        'question': q_str,
        'correct': c_str,
        'improper': i_str,     
        'unsimplified': u_str, 
        'trap': t_str,         
        'wrong': w_str if w_str else "N/A",  
        'wrong2': w2_str if w2_str else "N/A", 
        'options': options,
        'level_name': level_name
    }

def clean_latex(latex_str):
    """Converts the database LaTeX string into a normal text string (e.g., \frac{1}{2} -> 1/2)"""
    s = latex_str.replace("$\\displaystyle", "").replace("$", "").strip()
    s = re.sub(r'\\frac\{(\d+)\}\{(\d+)\}', r'\1/\2', s)
    return s.strip()

def parse_to_fraction(val_str):
    """Safely converts either a LaTeX string or a user's text input into a mathematical Fraction object."""
    try:
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