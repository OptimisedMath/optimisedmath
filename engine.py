import pandas as pd
import os
import streamlit as st

# UŁAMKI ZWYKŁE
from macro_topics.ulamki_zwykle.micro_01_zapisywanie import *
from macro_topics.ulamki_zwykle.micro_02_rozszerzanie import *
from macro_topics.ulamki_zwykle.micro_03_liczby_mieszane import * from macro_topics.ulamki_zwykle.micro_04_porownywanie import *
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
    """Loads the CSV into RAM once."""
    if not os.path.exists(DATA_FILE):
        return None
    return pd.read_csv(DATA_FILE, sep=';')

def get_curriculum() -> dict:
    """Returns a nested dictionary: { 'Macro_Topic_1': [ {Topic_Order, Micro_Topic, max_level}, ... ], ... }"""
    df = load_csv()
    if df is None: return {}
    
    valid_df = df[df['Function_Name'] != 'TBD']
    if valid_df.empty: return {}
    
    curriculum_dict = {}
    # Group by Macro_Topic, keeping the original order they appear in the CSV
    for macro, group in valid_df.groupby('Macro_Topic', sort=False):
        micro_group = group.groupby(['Topic_Order', 'Micro_Topic'], sort=False)['Level'].max().reset_index()
        micro_group = micro_group.sort_values('Topic_Order')
        curriculum_dict[macro] = micro_group.to_dict('records')
        
    return curriculum_dict

def get_problem_from_db(macro_topic, micro_topic, level) -> dict | None:
    """The Auto-Librarian: Finds the right problem based on the CSV. Now requires Macro Topic."""
    df = load_csv()
    if df is None:
        return {"error": "Missing CSV"}
    
    # Filter by Macro_Topic, Micro_Topic, and Level
    filtered_df = df[(df['Macro_Topic'] == macro_topic) & (df['Micro_Topic'] == micro_topic) & (df['Level'] == level)]
    
    if not filtered_df.empty:
        row = filtered_df.iloc[0]
        
        func_name = str(row['Function_Name']).strip()
        problem_func = globals().get(func_name)
        
        if not problem_func:
            return {"error": f"Function {func_name} not found"}
        
        problem_dict = problem_func(level)
        
        # Helper to grab the message from CSV or fallback to the generic Wrong_Message
        def get_msg(col_name):
            val = row.get(col_name)
            if pd.isna(val) or str(val).strip() in ["N/A", ""]:
                return str(row['Wrong_Message']).strip()
            return str(val).strip()

        # Attach the CSV messages dynamically
        problem_dict['messages'] = {
            't1': get_msg('Trap1_Message'),
            't2': get_msg('Trap2_Message'),
            't3': get_msg('Trap3_Message'),
            'w1': get_msg('Wrong_Message'),
            'w2': get_msg('Wrong_Message')
        }
        
        problem_dict['level_display'] = f"{row['Level_Name']} (Lvl {level})"
        return problem_dict
        
    return None