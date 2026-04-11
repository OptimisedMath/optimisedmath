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
    
    row = df[(df['Micro_Topic'] == topic) & (df['Level'] == level)]
    
    if not row.empty:
        func_name = str(row.iloc[0]['Function_Name'])
        current_level = int(row.iloc[0]['Level'])
        
        target_function = globals().get(func_name)
        
        if callable(target_function):
            problem_data = target_function(current_level)
            
            if isinstance(problem_data, dict):
                problem_data['trap_message'] = str(row.iloc[0]['Trap_Message'])
                problem_data['wrong_message'] = str(row.iloc[0]['Wrong_Message'])
                return problem_data
                
    return None