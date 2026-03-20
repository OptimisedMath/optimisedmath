import pandas as pd
import random
import os
import math

DATA_FILE = 'Courses_Data.csv'

# --- HELPER FUNCTIONS ---
def simplify_and_format(num, den, whole=0):
    """Simplifies a fraction, extracts whole numbers, and formats as LaTeX."""
    total_num = (whole * den) + num
    
    divisor = math.gcd(total_num, den)
    simp_num = total_num // divisor
    simp_den = den // divisor
    
    final_whole = simp_num // simp_den
    final_num = simp_num % simp_den
    
    if final_num == 0:
        return str(final_whole) 
    elif final_whole > 0:
        return rf"{final_whole}\frac{{{final_num}}}{{{simp_den}}}" 
    else:
        return rf"\frac{{{final_num}}}{{{simp_den}}}" 

def format_fraction_question(num, den, whole=None):
    """Formats the raw question elements without simplifying them."""
    if whole is not None and whole > 0:
        return rf"{whole}\frac{{{num}}}{{{den}}}"
    else:
        return rf"\frac{{{num}}}{{{den}}}"

# --- THE MATH FUNCTIONS (The "Chefs") ---
def add_fractions_simple(level):
    """Level 1: Identical denominators, sum < 1, NOT simplifiable."""
    while True:
        if level == 1:
            den = random.randint(3, 9)
        else:
            den = random.randint(10, 20) 
            
        num1 = random.randint(1, den - 2)
        num2 = random.randint(1, den - num1 - 1)
        
        if math.gcd(num1 + num2, den) == 1:
            # Generate the simplified strings
            c_str = simplify_and_format(num1+num2, den)
            t_str = simplify_and_format(num1+num2, den+den)
            w_str = simplify_and_format(num1+num2+1, den)
            
            # Uniqueness Filter
            if len({c_str, t_str, w_str}) == 3:
                break
            
    return {
        "question": f"Oblicz: {format_fraction_question(num1, den)} + {format_fraction_question(num2, den)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}" 
    }

def add_fractions_single_conversion(level):
    """Level 2: Single Conversion."""
    pairs = [(2, 4), (2, 6), (2, 8), (3, 6), (3, 9), (4, 8), (5, 10)]
    while True:
        d1, d2 = random.choice(pairs)
        
        if random.choice([True, False]):
            d1, d2 = d2, d1
            
        smaller_d = min(d1, d2)
        larger_d = max(d1, d2)
        scale = larger_d // smaller_d
        
        n_smaller = random.randint(1, smaller_d - 1)
        n_larger = random.randint(1, larger_d - 1)
        
        correct_num = (n_smaller * scale) + n_larger
        
        if d1 == smaller_d:
            n1, n2 = n_smaller, n_larger
        else:
            n1, n2 = n_larger, n_smaller
            
        trap_num = n1 + n2
        trap_den = larger_d
        wrong_num = n1 * n2
        wrong_den = larger_d
        
        c_str = simplify_and_format(correct_num, larger_d)
        t_str = simplify_and_format(trap_num, trap_den)
        w_str = simplify_and_format(wrong_num, wrong_den)
        
        # Uniqueness Filter
        if len({c_str, t_str, w_str}) == 3:
            break
    
    return {
        "question": f"Oblicz: {format_fraction_question(n1, d1)} + {format_fraction_question(n2, d2)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}: Rozszerzanie jednego ułamka"
    }

def add_fractions_complex(level):
    """Level 3: Coprime denominators."""
    pairs = [(2, 3), (2, 5), (3, 4), (3, 5), (4, 5)]
    while True:
        d1, d2 = random.choice(pairs)
        
        if random.choice([True, False]):
            d1, d2 = d2, d1
            
        n1 = random.randint(1, d1 - 1)
        n2 = random.randint(1, d2 - 1)
        
        common_den = d1 * d2
        correct_num = (n1 * d2) + (n2 * d1)
        
        trap_num = n1 + n2
        trap_den = d1 + d2
        wrong_num = n1 + n2
        wrong_den = common_den
        
        c_str = simplify_and_format(correct_num, common_den)
        t_str = simplify_and_format(trap_num, trap_den)
        w_str = simplify_and_format(wrong_num, wrong_den)
        
        # Uniqueness Filter
        if len({c_str, t_str, w_str}) == 3:
            break
    
    return {
        "question": f"Oblicz: {format_fraction_question(n1, d1)} + {format_fraction_question(n2, d2)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}: Różne mianowniki"
    }

def add_mixed_numbers_simple(level):
    """Level 4: Mixed Numbers (Easy)."""
    while True:
        den = random.randint(3, 9)
        w1 = random.randint(1, 5)
        w2 = random.randint(1, 5)
        n1 = random.randint(1, den - 2)
        n2 = random.randint(1, den - n1 - 1) 
        
        correct_whole = w1 + w2
        correct_numerator = n1 + n2
        
        trap_whole = w1 + w2
        trap_numerator = n1 + n2
        trap_denominator = den + den 
        
        improper1_num = w1 * den + n1
        improper2_num = w2 * den + n2
        wrong_improper_sum = improper1_num + improper2_num + 1 
        
        c_str = simplify_and_format(correct_numerator, den, correct_whole)
        t_str = simplify_and_format(trap_numerator, trap_denominator, trap_whole)
        w_str = simplify_and_format(wrong_improper_sum, den)
        
        # Uniqueness Filter
        if len({c_str, t_str, w_str}) == 3:
            break
            
    return {
        "question": f"Oblicz: {format_fraction_question(n1, den, w1)} + {format_fraction_question(n2, den, w2)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}: Liczby mieszane (Łatwe)"
    }

def add_mixed_numbers_complex(level):
    """Level 5: Mixed Numbers (The Final Boss)."""
    pairs = [(2, 3), (2, 5), (3, 4), (3, 5), (4, 5)]
    while True:
        d1, d2 = random.choice(pairs)
        w1 = random.randint(1, 3)
        w2 = random.randint(1, 3)
        
        common_den = d1 * d2
        # Ensure fraction sum > 1
        while True:
            n1 = random.randint(1, d1 - 1)
            n2 = random.randint(1, d2 - 1)
            if (n1 * d2 + n2 * d1) > common_den:
                break
        
        correct_num = (n1 * d2) + (n2 * d1)
        correct_whole = w1 + w2
        
        trap_whole = w1 + w2
        trap_num = n1 + n2
        trap_den = common_den
        
        wrong_whole = w1 + w2
        wrong_num = n1 + n2
        wrong_den = d1 + d2
        
        c_str = simplify_and_format(correct_num, common_den, correct_whole)
        t_str = simplify_and_format(trap_num, trap_den, trap_whole)
        w_str = simplify_and_format(wrong_num, wrong_den, wrong_whole)
        
        # Uniqueness Filter
        if len({c_str, t_str, w_str}) == 3:
            break
            
    return {
        "question": f"Oblicz: {format_fraction_question(n1, d1, w1)} + {format_fraction_question(n2, d2, w2)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}: Liczby mieszane (Ostateczny boss)"
    }

MATH_MAP = {
    "add_fractions_simple": add_fractions_simple,
    "add_fractions_single_conversion": add_fractions_single_conversion,
    "add_fractions_complex": add_fractions_complex,
    "add_mixed_numbers_simple": add_mixed_numbers_simple,
    "add_mixed_numbers_complex": add_mixed_numbers_complex
}

# --- THE LIBRARIAN ---
def get_problem_from_db(topic, level):
    if not os.path.exists(DATA_FILE):
        return {"error": "Missing CSV"}
    
    df = pd.read_csv(DATA_FILE, sep=';')
    
    row = df[(df['Micro_Topic'] == topic) & (df['Level'] == level)]
    
    if not row.empty:
        func_name = row.iloc[0]['Function_Name']
        current_level = int(row.iloc[0]['Level'])
        
        if func_name in MATH_MAP:
            return MATH_MAP[func_name](current_level)
    return None