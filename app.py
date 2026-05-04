import streamlit as st
import engine
from core import db
from state_manager import StateManager
import time
from ui.login import render_login_gate
from ui.sidebar import render_sidebar
from ui.main_screen import render_learning_screen


st.set_page_config(page_title="Najszybsza nauka matematyki", page_icon="🧮")

db.init_db()

# --- 1. DYNAMIC CURRICULUM SETUP ---
curriculum = engine.get_curriculum()
if not curriculum:
    st.error("Brak dostępnych zadań w bazie.")
    st.stop()

macro_topics = list(curriculum.keys())

# Check if a user is logged in. If not, show the gate and STOP.
if "username" not in st.session_state:
    render_login_gate(macro_topics, curriculum)
    st.stop()

StateManager.init_defaults(st.session_state, macro_topics, curriculum)

# Build map for CURRENT macro topic
macro_curr = curriculum[st.session_state.selected_macro]
topic_map = {row["Topic_Order"]: {"name": row["Micro_Topic"], "max_level": row["Level"]} for row in macro_curr}


# --- 2. SIDEBAR: NAVIGATION & PROFILE ---
render_sidebar(st.session_state, macro_topics, curriculum, topic_map, admin_mode=False)

# --- 3. ORCHESTRATOR: FETCH PROBLEM ---
if "current_problem" not in st.session_state:
    st.session_state.current_problem = engine.get_problem_from_db(
        st.session_state.selected_macro,
        topic_map[st.session_state.selected_topic_order]["name"],
        st.session_state.selected_level,
    )
    st.session_state.problem_start_time = time.time()

problem = st.session_state.current_problem

# --- 4. RENDER MAIN SCREEN ---
render_learning_screen(st.session_state, problem, topic_map)