import pandas as pd
import os
import streamlit as st
from core.utils import check_text_answer, parse_to_fraction

# UŁAMKI ZWYKŁE
from macro_topics.ulamki_zwykle.micro_01_zapisywanie import *
from macro_topics.ulamki_zwykle.micro_02_rozszerzanie import *
from macro_topics.ulamki_zwykle.micro_03_liczby_mieszane import *
from macro_topics.ulamki_zwykle.micro_04_porownywanie import *
from macro_topics.ulamki_zwykle.micro_05_dodawanie import *
from macro_topics.ulamki_zwykle.micro_06_odejmowanie import *
from macro_topics.ulamki_zwykle.micro_07_mnozenie_liczba import *
from macro_topics.ulamki_zwykle.micro_08_mnozenie_ulamkow import *
from macro_topics.ulamki_zwykle.micro_09_dzielenie_liczba import *
from macro_topics.ulamki_zwykle.micro_10_dzielenie_ulamkow import *
from macro_topics.ulamki_zwykle.micro_11_potegowanie import *
from macro_topics.ulamki_zwykle.micro_12_ulamek_liczby import *
from macro_topics.ulamki_zwykle.micro_13_kolejnosc import *

# UŁAMKI DZIESIĘTNE
from macro_topics.ulamki_dziesietne.micro_01_zamiana import *
from macro_topics.ulamki_dziesietne.micro_02_porownywanie import *
from macro_topics.ulamki_dziesietne.micro_03_dodawanie import *
from macro_topics.ulamki_dziesietne.micro_04_odejmowanie import *
from macro_topics.ulamki_dziesietne.micro_05_przesuwanie import *
from macro_topics.ulamki_dziesietne.micro_06_mnozenie import *
from macro_topics.ulamki_dziesietne.micro_07_dzielenie import *
from macro_topics.ulamki_dziesietne.micro_08_kolejnosc import *
from macro_topics.ulamki_dziesietne.micro_09_jednostki import *

DATA_FILE = 'Courses_Data.csv'

def load_csv():
    if not os.path.exists(DATA_FILE): return None
    return pd.read_csv(DATA_FILE, sep=';')

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
        problem_dict = problem_func(level)
        
        def get_msg(col_name):
            val = row.get(col_name)
            if pd.isna(val) or str(val).strip() in ["N/A", ""]: return str(row['Wrong_Message']).strip()
            return str(val).strip()

        problem_dict['messages'] = {
            't1': get_msg('Trap1_Message'), 't2': get_msg('Trap2_Message'),
            't3': get_msg('Trap3_Message'), 'w1': get_msg('Wrong_Message'),
            'w2': get_msg('Wrong_Message')
        }
        problem_dict['level_display'] = f"{row['Level_Name']} (Lvl {level})"
        return problem_dict
    return None

def evaluate_answer(problem: dict, user_input: str, is_text_mode: bool) -> dict:
    """
    THE BLACK BOX GRADER: Processes the answer and returns a strictly formatted dictionary to the UI.
    """
    result = {
        "is_correct": False,
        "lock_answer": False, 
        "feedback_type": "warning",
        "feedback_msg": problem['messages'].get('w1', "Błędna odpowiedź.")
    }

    if not user_input:
        result['feedback_msg'] = "Wpisz swój wynik w puste pole!" if is_text_mode else "Najpierw wybierz odpowiedź!"
        return result

    correct_val = parse_to_fraction(problem['correct'])
    policy = problem.get('grading_policy', 'standard')

    # --- 1. MULTIPLE CHOICE MODE ---
    if not is_text_mode:
        answer_type = problem['options_map'].get(user_input, "w1")
        student_val = parse_to_fraction(user_input)

        if answer_type == "correct":
            result.update({"is_correct": True, "lock_answer": True})
            return result

        if student_val is not None and correct_val is not None and student_val == correct_val:
            if policy == "exact_match_only":
                result.update({"lock_answer": True, "feedback_type": "warning", "feedback_msg": problem['messages'].get(answer_type, "W tym zadaniu wartość to nie wszystko. Zapisz wynik w dokładnie takiej postaci, o jaką prosi polecenie!")})
            elif policy == "equivalent_accepted":
                result.update({"is_correct": True, "lock_answer": True})
            else:
                custom_msg = problem['messages'].get(answer_type, problem['messages']['w1'])
                if custom_msg == problem['messages']['w1']: custom_msg = "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!"
                result.update({"lock_answer": False, "feedback_type": "info", "feedback_msg": custom_msg})
            return result

        result.update({"lock_answer": True, "feedback_type": "error" if answer_type.startswith("t") else "warning", "feedback_msg": problem['messages'].get(answer_type, problem['messages']['w1'])})
        return result

    # --- 2. TEXT INPUT MODE ---
    answer_type = None
    for opt_str, opt_id in problem['options_map'].items():
        if check_text_answer(opt_str, user_input):
            answer_type = opt_id
            break

    student_val = parse_to_fraction(user_input)

    if answer_type == "correct":
        result.update({"is_correct": True, "lock_answer": True})
        return result

    if answer_type is not None:
        if student_val is not None and correct_val is not None and student_val == correct_val:
            if policy == "exact_match_only":
                result.update({"lock_answer": True, "feedback_type": "error" if answer_type.startswith("t") else "warning", "feedback_msg": problem['messages'].get(answer_type, problem['messages']['w1'])})
            elif policy == "equivalent_accepted":
                result.update({"is_correct": True, "lock_answer": True})
            else:
                result.update({"lock_answer": False, "feedback_type": "info", "feedback_msg": problem['messages'].get(answer_type, "Wynik poprawny matematycznie, ale zapisz go w najprostszej postaci!")})
        else:
            result.update({"lock_answer": True, "feedback_type": "error" if answer_type.startswith("t") else "warning", "feedback_msg": problem['messages'].get(answer_type, problem['messages']['w1'])})
        return result

    if student_val is None:
        result.update({"lock_answer": False, "feedback_type": "warning", "feedback_msg": "Niepoprawny zapis matematyczny."})
        return result

    if correct_val is not None and student_val == correct_val:
        if policy == "exact_match_only":
            result.update({"lock_answer": True, "feedback_type": "warning", "feedback_msg": "W tym zadaniu wartość matematyczna to nie wszystko. Musisz zapisać ułamek w dokładnie takiej postaci, o jaką prosi polecenie!"})
        elif policy == "equivalent_accepted":
            result.update({"is_correct": True, "lock_answer": True})
        else:
            result.update({"lock_answer": False, "feedback_type": "info", "feedback_msg": "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!"})
        return result

    result.update({"lock_answer": True, "feedback_type": "warning", "feedback_msg": problem['messages']['w1']})
    return result