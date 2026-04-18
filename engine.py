import pandas as pd
import os
import importlib
from pathlib import Path
import streamlit as st
from core.utils import check_text_answer, parse_to_fraction

DATA_FILE = 'Courses_Data.csv'

# --- THE AUTOLOADER ---
macro_path = Path(__file__).parent / "macro_topics"
for file_path in macro_path.rglob("*.py"):
    if file_path.name.startswith("__"): continue
    module_path = ".".join(file_path.relative_to(Path(__file__).parent).parts)[:-3]
    module = importlib.import_module(module_path)
    globals().update({k: v for k, v in module.__dict__.items() if not k.startswith("_")})

# @st.cache_data <- for cache
def load_csv(file_path=DATA_FILE):
    return pd.read_csv(file_path, sep=';', encoding='utf-8')

def get_curriculum() -> dict:
    df = load_csv()
    if df is None: return {}
    valid_df = df[df['Function_Name'] != 'TBD']
    if valid_df.empty: return {}
    
    curriculum_dict = {}
    for macro, group in valid_df.groupby('Macro_Topic', sort=False):
        micro_group = group.groupby(['Topic_Order', 'Micro_Topic'], sort=False)['Level'].max().reset_index()
        micro_group = micro_group.sort_values('Topic_Order')
        curriculum_dict[macro] = micro_group.to_dict('records')
        
    return curriculum_dict

def get_problem_from_db(macro_topic, micro_topic, level) -> dict | None:
    df = load_csv()
    if df is None: return {"error": "Missing CSV"}
    
    filtered_df = df[(df['Macro_Topic'] == macro_topic) & (df['Micro_Topic'] == micro_topic) & (df['Level'] == level)]
    
    if not filtered_df.empty:
            row = filtered_df.iloc[0]
            func_name = str(row['Function_Name']).strip()
            problem_func = globals().get(func_name)
            
            if not problem_func: return {"error": f"Function {func_name} not found"}
            
            try:
                problem_dict = generate_problem(lambda: problem_func(level))
            except RuntimeError as e:
                return {"error": str(e)}
            
            # THE FIX: Added 'return' and a safety check for empty CSV cells (N/A, NaN)
            def get_msg(col_name):
                val = row.get(col_name)
                if pd.isna(val) or str(val).strip() in ["N/A", "None", "nan", ""]:
                    return "Zła odpowiedź."
                return str(val)

            problem_dict['messages'] = {
                't1': get_msg('Trap1_Message'), 't2': get_msg('Trap2_Message'),
                't3': get_msg('Trap3_Message'), 'w1': get_msg('Wrong_Message'),
                'w2': get_msg('Wrong_Message')
            }
            problem_dict['level_display'] = f"{row['Level_Name']} (Lvl {level})"
            return problem_dict
    return None

def generate_problem(topic_function):
    MAX_RETRIES = 50
    for _ in range(MAX_RETRIES):
        problem = topic_function() 
        if problem is not None:
            return problem
    raise RuntimeError(f"Failed to generate unique problem for {topic_function.__name__}")

def check_format_mismatch(user_text, correct_latex):
    """Intercepts answers that are mathematically correct but use the wrong notation system."""
    user_str = str(user_text)
    if "/" in user_str and "," in correct_latex:
        return "Wynik poprawny matematycznie, ale to jest zadanie z ułamków dziesiętnych! Zapisz odpowiedź używając przecinka, a nie ułamka zwykłego."
    if ("," in user_str or "." in user_str) and "\\frac" in correct_latex:
        return "Wynik poprawny matematycznie, ale w tym zadaniu powinieneś użyć ułamka zwykłego, a nie dziesiętnego!"
    return None

def evaluate_answer(user_input, problem, is_text_mode=False):
    from core.utils import check_text_answer, parse_to_fraction
    
    # --- 1. MULTIPLE CHOICE MODE ---
    if not is_text_mode and 'options' in problem and len(problem['options']) > 0:
        is_correct = (problem['options_map'].get(user_input) == "correct")
        if is_correct:
            return {"is_correct": True, "lock_answer": True}
        else:
            msg_key = problem['options_map'].get(user_input, "w1")
            msg_text = problem['messages'].get(msg_key, "Zła odpowiedź.")
            return {"lock_answer": True, "feedback_type": "warning", "feedback_msg": msg_text}

    # --- 2. TEXT INPUT MODE ---
    policy = problem.get('grading_policy', 'standard')
    
    # Exact Match Check
    if check_text_answer(problem['correct'], user_input):
        return {"is_correct": True, "lock_answer": True}

    # Mathematical Evaluation
    student_val = parse_to_fraction(str(user_input))
    correct_val = parse_to_fraction(problem['correct'])

    if student_val is None:
        return {"lock_answer": False, "feedback_type": "warning", "feedback_msg": "Niepoprawny zapis matematyczny."}

    if student_val == correct_val:
        format_warning = check_format_mismatch(user_input, problem['correct'])
        if format_warning:
            return {"lock_answer": False, "feedback_type": "warning", "feedback_msg": format_warning}
            
        if policy == "exact_match_only":
            return {"lock_answer": True, "feedback_type": "warning", "feedback_msg": "W tym zadaniu wartość matematyczna to nie wszystko. Musisz zapisać ułamek w dokładnie takiej postaci, o jaką prosi polecenie!"}
        elif policy == "equivalent_accepted":
            return {"is_correct": True, "lock_answer": True}
        else:
            return {"lock_answer": False, "feedback_type": "info", "feedback_msg": "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!"}

    # --- 3. TEXT MODE TRAP SCANNER ---
    # Secretly calculates the traps to see if the student mathematically fell for one
    for opt_str, opt_type in problem['options_map'].items():
        if opt_type in ["t1", "t2", "t3", "w1", "w2"]:
            opt_val = parse_to_fraction(opt_str)
            if check_text_answer(opt_str, user_input) or (opt_val is not None and student_val == opt_val):
                msg_text = problem['messages'].get(opt_type, "Zła odpowiedź.")
                return {"lock_answer": True, "feedback_type": "warning", "feedback_msg": msg_text}

    # If math is entirely wrong and misses all traps
    msg_text = problem['messages'].get('w1', "Zła odpowiedź.")
    return {"lock_answer": True, "feedback_type": "warning", "feedback_msg": msg_text}