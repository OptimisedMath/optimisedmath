import streamlit as st
import engine
import random

st.set_page_config(page_title="Optimised Math", page_icon="🧮")

# --- SIDEBAR: The Level Selector ---
with st.sidebar:
    st.title("Settings")
    # This creates a slider from 1 to 5
    selected_level = st.slider("Select Difficulty Level:", 1, 5, 1)
    
    if st.button("Apply Level & Reset"):
        # When clicked, it forces the engine to get a new problem for the new level
        st.session_state.current_problem = engine.get_problem_from_db("Addition and Substraction", selected_level)
        st.rerun()

st.title("🧮 CKE Math Tutor")
st.subheader("Topic: Addition of Fractions")

# 1. Initialize Memory
if 'current_problem' not in st.session_state:
    # We use the selected_level from the sidebar
    st.session_state.current_problem = engine.get_problem_from_db("Addition and Substraction", selected_level)

problem = st.session_state.current_problem

# 2. Safety Check
if problem is None or "error" in problem:
    st.error(f"❌ Could not find Level {selected_level} in Courses_Data.csv.")
else:
    # 3. Display the Problem
    st.write("---")
    # Show the level badge we created in engine.py
    st.info(f"📍 {problem.get('level_display', 'Level ' + str(selected_level))}") 
    
    st.header("Zadanie:")
    st.latex(problem['question'].replace("Oblicz: ", "")) 

    # 4. Answer Buttons
    raw_options = [problem['correct'], problem['trap'], problem['wrong']]

    st.markdown(
        """
        <style>
        /* Target the radio button labels and add padding */
        .stRadio label {
            padding-bottom: 25px; 
            padding-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # --------------------------

    # Use problem_id to guarantee a mathematically clean reset every time
    if 'shuffled_options' not in st.session_state or st.session_state.get('last_id') != problem['problem_id']:
        shuffled = raw_options.copy()
        random.shuffle(shuffled)
        st.session_state.shuffled_options = shuffled
        st.session_state.last_id = problem['problem_id']

    options = st.session_state.shuffled_options
    choice = st.radio("Wybierz wynik:", options, index=None)

    # 5. Check Logic - Dynamically pulls the exact message from the Engine
    if st.button("Sprawdź odpowiedź"):
        if choice == problem['correct']:
            st.success("Brawo! To poprawna odpowiedź. 🎉")
        elif choice == problem['trap']:
            st.error(problem['trap_message'])
        else:
            st.warning(problem['wrong_message'])

    # 6. Next Problem
    if st.button("Następne zadanie ➡️"):
        st.session_state.current_problem = engine.get_problem_from_db("Addition and Substraction", selected_level)
        st.rerun()