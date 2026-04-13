import pandas as pd
import os
import streamlit as st

# Import the math functions into memory so the Auto-Librarian can find them
from macro_topics.ulamki.micro_01_zapisywanie import *
from macro_topics.ulamki.micro_02_rozszerzanie import *
from macro_topics.ulamki.micro_03_liczby_mieszane import * 
from macro_topics.ulamki.micro_04_porownywanie import *
from macro_topics.ulamki.micro_05_dodawanie import *
from macro_topics.ulamki.micro_06_odejmowanie import *
from macro_topics.ulamki.micro_07_mnozenie_liczba import *
from macro_topics.ulamki.micro_08_mnozenie_ulamkow import *
from macro_topics.ulamki.micro_09_dzielenie_liczba import *
from macro_topics.ulamki.micro_10_dzielenie_ulamkow import *
from macro_topics.ulamki.micro_11_potegowanie import *
from macro_topics.ulamki.micro_12_ulamek_liczby import *
from macro_topics.ulamki.micro_13_kolejnosc import *


DATA_FILE = 'Courses_Data.csv'

# @st.cache_data -> for later
def load_csv():
    """Loads the CSV into RAM once."""
    if not os.path.exists(DATA_FILE):
        return None
    return pd.read_csv(DATA_FILE, sep=';')

def get_curriculum() -> list[dict]:
    """Scans the CSV to build the dynamic topic menu."""
    df = load_csv()
    if df is None: return []
    
    valid_df = df[df['Function_Name'] != 'TBD']
    if valid_df.empty: return []
    
    curriculum = valid_df.groupby(['Topic_Order', 'Micro_Topic'])['Level'].max().reset_index()
    curriculum = curriculum.sort_values('Topic_Order')
    
    return curriculum.to_dict('records')

def get_problem_from_db(topic, level) -> dict | None:
    """The Auto-Librarian: Finds the right problem based on the CSV."""
    df = load_csv()
    if df is None:
        return {"error": "Missing CSV"}
    
    # This filters the database and returns a DataFrame
    filtered_df = df[(df['Micro_Topic'] == topic) & (df['Level'] == level)]
    
    if not filtered_df.empty:
        # FIX: Explicitly grab the first row as a 1D object so we can read its strings!
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