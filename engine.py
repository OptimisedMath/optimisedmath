import pandas as pd
import importlib
from pathlib import Path
from core.utils import check_text_answer, parse_to_fraction
import uuid

BASE_DIR = Path(__file__).resolve().parent

# --- THE AUTOLOADER ---
FUNCTION_REGISTRY = {}
macro_path = Path(__file__).parent / "macro_topics"
for file_path in macro_path.rglob("*.py"):
    if file_path.name.startswith("__"): continue
    module_path = ".".join(file_path.relative_to(Path(__file__).parent).parts)[:-3]
    module = importlib.import_module(module_path)
    
    # Safely store functions in a specific dictionary instead of global memory
    for k, v in module.__dict__.items():
         if callable(v) and not k.startswith("_"):
             FUNCTION_REGISTRY[k] = v

def get_curriculum() -> dict:
    curriculum_dict = {}
    data_dir = BASE_DIR / "data"
    
    if not data_dir.exists():
        return curriculum_dict
        
    # 1. Dynamically scan for every CSV file in the data folder
    for file_path in data_dir.glob("*.csv"):
        # 2. Convert the file name to the Macro Topic (e.g., "Ułamki_dziesiętne.csv" -> "Ułamki dziesiętne")
        macro_topic = file_path.stem.replace("_", " ")
        
        try:
            # 3. Load the specific topic database
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            
            # Filter out any rows you haven't finished building yet
            valid_df = df[df['Function_Name'] != 'TBD']
            
            if not valid_df.empty:
                # 4. Group by Topic_Order to build the sidebar menu correctly
                micro_group = valid_df.groupby(['Topic_Order', 'Micro_Topic'], sort=False)['Level'].max().reset_index()
                micro_group = micro_group.sort_values('Topic_Order')
                curriculum_dict[macro_topic] = micro_group.to_dict('records')
                
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")
            
    return curriculum_dict

def get_problem_from_db(macro_topic, micro_topic, level) -> dict | None:
    # 1. Convert the UI topic name to a file name (e.g., "Ułamki dziesiętne" -> "Ułamki_dziesiętne.csv")
    safe_filename = macro_topic.replace(" ", "_") + ".csv"
    csv_path = BASE_DIR / "data" / safe_filename
    
    # 2. Check if the specific database exists
    if not csv_path.exists(): 
        return {"error": f"Missing database file: {safe_filename}"}
        
    # 3. Load ONLY the relevant macro topic data
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    
    # 4. Filter by Micro Topic and Level
    filtered_df = df[(df['Micro_Topic'] == micro_topic) & (df['Level'] == level)]
    
    if not filtered_df.empty:
        row = filtered_df.iloc[0]
        func_name = str(row['Function_Name']).strip()
        problem_func = FUNCTION_REGISTRY.get(func_name)
        
        if not problem_func: return {"error": f"Function {func_name} not found"}
        
        try:
            problem_dict = generate_problem(problem_func)
            problem_dict['level'] = int(level)
            problem_dict['level_name'] = f"Poziom {level}"
            problem_dict['problem_id'] = str(uuid.uuid4())
        except RuntimeError as e:
            return {"error": str(e)}
        
        # Pull messages cleanly
        def get_msg(col_name):
            val = row.get(col_name)
            if pd.isna(val) or str(val).strip() in ["N/A", "None", "nan", ""]:
                return "Niepoprawna odpowiedź, spróbuj ponownie."
            return str(val)

        problem_dict['messages'] = {
            't1': get_msg('Trap1_Message'), 
            't2': get_msg('Trap2_Message'),
            't3': get_msg('Trap3_Message')
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
    
    # --- 1. MULTIPLE CHOICE MODE ---
    if not is_text_mode and 'options' in problem and len(problem['options']) > 0:
        is_correct = (problem['options_map'].get(user_input) == "correct")
        if is_correct:
            return {"is_correct": True, "lock_answer": True}
        else:
            # Check what kind of option was clicked
            msg_key = problem['options_map'].get(user_input, "w1")
            
            # THE FIX: Safely try to fetch the dictionary. If it's missing, default gracefully.
            msg_text = problem.get('messages', {}).get(msg_key, "Niepoprawna odpowiedź, spróbuj ponownie.")
            
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
        # SHIFT: Gibberish math format is a soft error (Blue)
        return {"lock_answer": False, "feedback_type": "info", "feedback_msg": "Niepoprawny zapis matematyczny."}

    if student_val == correct_val:
        format_warning = check_format_mismatch(user_input, problem['correct'])
        if format_warning:
            # SHIFT: Wrong notation system is a soft error (Blue)
            return {"lock_answer": False, "feedback_type": "info", "feedback_msg": format_warning}
            
        if policy == "exact_match_only":
            return {"lock_answer": True, "feedback_type": "warning", "feedback_msg": "W tym zadaniu wartość matematyczna to nie wszystko. Musisz zapisać ułamek w dokładnie takiej postaci, o jaką prosi polecenie!"}
        elif policy == "equivalent_accepted":
            return {"is_correct": True, "lock_answer": True}
        else:
            # SHIFT: Unsimplified fraction is a soft error (Blue)
            return {"lock_answer": False, "feedback_type": "info", "feedback_msg": "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!"}

    # --- 3. TEXT MODE TRAP SCANNER ---
    for opt_str, opt_type in problem['options_map'].items():
        if opt_type in ["t1", "t2", "t3", "w1", "w2"]:
            opt_val = parse_to_fraction(opt_str)
            if check_text_answer(opt_str, user_input) or (opt_val is not None and student_val == opt_val):
                msg_text = problem.get('messages', {}).get(opt_type, "Niepoprawna odpowiedź, spróbuj ponownie.")
                # Hard Trap (Yellow)
                return {"lock_answer": True, "feedback_type": "warning", "feedback_msg": msg_text}

    # If math is entirely wrong and misses all traps
    msg_text = problem.get('messages', {}).get('w1', "Niepoprawna odpowiedź, spróbuj ponownie.")
    # Hard Error (Yellow)
    return {"lock_answer": True, "feedback_type": "warning", "feedback_msg": msg_text}