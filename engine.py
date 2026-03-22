import pandas as pd
import random
import os
import math
import streamlit as st
import uuid

DATA_FILE = 'Courses_Data.csv'

# --- OPTIMIZATION: Database Caching ---
@st.cache_data
def load_csv():
    """Loads the CSV into RAM once, making all future queries instant."""
    if not os.path.exists(DATA_FILE):
        return None
    return pd.read_csv(DATA_FILE, sep=';')

# --- HELPER FUNCTIONS ---
def simplify_and_format(num, den, whole=0):
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
    if whole is not None and whole > 0:
        return rf"{whole}\frac{{{num}}}{{{den}}}"
    else:
        return rf"\frac{{{num}}}{{{den}}}"

# --- THE MATH FUNCTIONS (The "Chefs") ---
def add_fractions_simple(level):
    while True:
        den = random.randint(3, 9) if level == 1 else random.randint(10, 20) 
        num1 = random.randint(1, den - 2)
        num2 = random.randint(1, den - num1 - 1)
        
        if math.gcd(num1 + num2, den) == 1:
            c_str = simplify_and_format(num1+num2, den)
            t_str = simplify_and_format(num1+num2, den+den)
            w_str = simplify_and_format(num1+num2+1, den)
            
            if len({c_str, t_str, w_str}) == 3:
                break
            
    return {
        "problem_id": str(uuid.uuid4()),
        "question": f"Oblicz: {format_fraction_question(num1, den)} + {format_fraction_question(num2, den)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}" 
    }

def add_fractions_single_conversion(level):
    pairs = [(2, 4), (2, 6), (2, 8), (3, 6), (3, 9), (4, 8), (5, 10)]
    while True:
        d1, d2 = random.choice(pairs)
        if random.choice([True, False]): d1, d2 = d2, d1
            
        smaller_d, larger_d = min(d1, d2), max(d1, d2)
        scale = larger_d // smaller_d
        
        n_smaller = random.randint(1, smaller_d - 1)
        n_larger = random.randint(1, larger_d - 1)
        
        correct_num = (n_smaller * scale) + n_larger
        n1, n2 = (n_smaller, n_larger) if d1 == smaller_d else (n_larger, n_smaller)
            
        c_str = simplify_and_format(correct_num, larger_d)
        t_str = simplify_and_format(n1 + n2, larger_d)
        w_str = simplify_and_format(n1 * n2, larger_d)
        
        if len({c_str, t_str, w_str}) == 3:
            break
    
    return {
        "problem_id": str(uuid.uuid4()),
        "question": f"Oblicz: {format_fraction_question(n1, d1)} + {format_fraction_question(n2, d2)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}: Rozszerzanie jednego ułamka"
    }

def add_fractions_complex(level):
    pairs = [(2, 3), (2, 5), (3, 4), (3, 5), (4, 5)]
    while True:
        d1, d2 = random.choice(pairs)
        if random.choice([True, False]): d1, d2 = d2, d1
            
        n1 = random.randint(1, d1 - 1)
        n2 = random.randint(1, d2 - 1)
        
        common_den = d1 * d2
        correct_num = (n1 * d2) + (n2 * d1)
        
        c_str = simplify_and_format(correct_num, common_den)
        t_str = simplify_and_format(n1 + n2, d1 + d2)
        w_str = simplify_and_format(n1 + n2, common_den)
        
        if len({c_str, t_str, w_str}) == 3:
            break
    
    return {
        "problem_id": str(uuid.uuid4()),
        "question": f"Oblicz: {format_fraction_question(n1, d1)} + {format_fraction_question(n2, d2)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}: Różne mianowniki"
    }

def add_mixed_numbers_simple(level):
    while True:
        den = random.randint(3, 9)
        w1, w2 = random.randint(1, 5), random.randint(1, 5)
        n1 = random.randint(1, den - 2)
        n2 = random.randint(1, den - n1 - 1) 
        
        correct_whole = w1 + w2
        correct_numerator = n1 + n2
        
        improper1_num = w1 * den + n1
        improper2_num = w2 * den + n2
        wrong_improper_sum = improper1_num + improper2_num + 1 
        
        c_str = simplify_and_format(correct_numerator, den, correct_whole)
        t_str = simplify_and_format(n1 + n2, den + den, w1 + w2)
        w_str = simplify_and_format(wrong_improper_sum, den)
        
        if len({c_str, t_str, w_str}) == 3:
            break
            
    return {
        "problem_id": str(uuid.uuid4()),
        "question": f"Oblicz: {format_fraction_question(n1, den, w1)} + {format_fraction_question(n2, den, w2)}",
        "correct": f"$\\displaystyle {c_str}$",
        "trap": f"$\\displaystyle {t_str}$",
        "wrong": f"$\\displaystyle {w_str}$",
        "level_display": f"Poziom {level}: Liczby mieszane (Łatwe)"
    }

def add_mixed_numbers_complex(level):
    pairs = [(2, 3), (2, 5), (3, 4), (3, 5), (4, 5)]
    while True:
        d1, d2 = random.choice(pairs)
        w1, w2 = random.randint(1, 3), random.randint(1, 3)
        common_den = d1 * d2
        
        while True:
            n1 = random.randint(1, d1 - 1)
            n2 = random.randint(1, d2 - 1)
            if (n1 * d2 + n2 * d1) > common_den: break
        
        correct_num = (n1 * d2) + (n2 * d1)
        
        c_str = simplify_and_format(correct_num, common_den, w1 + w2)
        t_str = simplify_and_format(n1 + n2, common_den, w1 + w2)
        w_str = simplify_and_format(n1 + n2, d1 + d2, w1 + w2)
        
        if len({c_str, t_str, w_str}) == 3:
            break
            
    return {
        "problem_id": str(uuid.uuid4()),
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
    df = load_csv()
    if df is None:
        return {"error": "Missing CSV"}
    
    row = df[(df['Micro_Topic'] == topic) & (df['Level'] == level)]
    
    if not row.empty:
        func_name = row.iloc[0]['Function_Name']
        current_level = int(row.iloc[0]['Level'])
        
        if func_name in MATH_MAP:
            problem_data = MATH_MAP[func_name](current_level)
            
            # The Librarian attaches the pedagogical feedback from the CSV to the math payload
            problem_data['trap_message'] = row.iloc[0]['Trap_Message']
            problem_data['wrong_message'] = row.iloc[0]['Wrong_Message']
            
            return problem_data
    return None