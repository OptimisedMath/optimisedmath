import streamlit as st
import engine
import random

st.set_page_config(page_title="Najszybsza nauka matematyki", page_icon="🧮")

# --- 1. INITIALIZE GAME STATE (The Memory Card) ---
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'streak' not in st.session_state:
    st.session_state.streak = 0
if 'unlocked_level' not in st.session_state:
    st.session_state.unlocked_level = 1
if 'selected_level' not in st.session_state:
    st.session_state.selected_level = 1
if 'problem_answered' not in st.session_state:
    st.session_state.problem_answered = False

# --- SIDEBAR: Player Profile & Level Selector ---
with st.sidebar:
    st.title("🏆 Twój Profil")
    st.metric(label="Punkty Doświadczenia (XP)", value=st.session_state.xp)
    
    # --- RESET BUTTON ---
    if st.button("🔄 Zresetuj Postęp"):
        st.session_state.xp = 0
        st.session_state.streak = 0
        st.session_state.unlocked_level = 1
        st.session_state.selected_level = 1
        st.session_state.problem_answered = False
        st.session_state.current_problem = engine.get_problem_from_db("Addition", 1)
        st.rerun()
    st.markdown("---")
    st.title("Ustawienia")
    
    # Option A: The "Magical Appearance" Logic
    if st.session_state.unlocked_level == 1:
        # Hide the slider and show a motivational badge
        st.info("🔒 Aktywny: Poziom 1\n\n*(Zdobądź 3 gwiazdki, aby odblokować wybór poziomów!)*")
        new_level = 1 
    else:
        # Once Level 2 is unlocked, reveal the slider
        new_level = st.slider(
            "Wybierz Poziom:", 
            min_value=1, 
            max_value=st.session_state.unlocked_level, 
            value=st.session_state.selected_level
        )
    
    # If user manually changes the level, reset the streak and fetch a new problem
    if new_level != st.session_state.selected_level:
        st.session_state.selected_level = new_level
        st.session_state.streak = 0 
        st.session_state.problem_answered = False
        st.session_state.current_problem = engine.get_problem_from_db("Addition", st.session_state.selected_level)
        st.rerun()

st.title("🧮 Najlepszy nauczyciel matematyki")
st.subheader("Temat: Dodawanie Ułamków")

# Fetch initial problem if missing
if 'current_problem' not in st.session_state:
    st.session_state.current_problem = engine.get_problem_from_db("Addition", st.session_state.selected_level)

problem = st.session_state.current_problem

# --- 2. THE MASTERY SCOREBOARD ---
# Draw the stars based on the current streak
stars_display = "⭐" * st.session_state.streak + "⬛" * (3 - st.session_state.streak)
st.markdown(f"### Postęp do kolejnego poziomu: {stars_display}")

# Safety Check
if problem is None or "error" in problem:
    st.error(f"❌ Nie można załadować Poziomu {st.session_state.selected_level}. Sprawdź plik CSV.")
else:
    # Display Problem
    st.write("---")
    st.info(f"📍 {problem.get('level_display', 'Level ' + str(st.session_state.selected_level))}") 
    
    st.header("Zadanie:")
    st.latex(problem['question'].replace("Oblicz: ", "")) 

    # Answer Buttons styling
    st.markdown(
        """
        <style>
        .stRadio label { padding-bottom: 25px; padding-top: 10px; }
        </style>
        """,
        unsafe_allow_html=True
    )

    raw_options = [problem['correct'], problem['trap'], problem['wrong']]

    # Shuffle Logic using the unique Problem ID
    if 'shuffled_options' not in st.session_state or st.session_state.get('last_id') != problem['problem_id']:
        shuffled = raw_options.copy()
        random.shuffle(shuffled)
        st.session_state.shuffled_options = shuffled
        st.session_state.last_id = problem['problem_id']
        st.session_state.problem_answered = False 

    options = st.session_state.shuffled_options
    choice = st.radio("Wybierz wynik:", options, index=None)

# --- 3. CHECK LOGIC & GAMIFICATION ---
    if st.button("Sprawdź odpowiedź", disabled=st.session_state.problem_answered):
        if not choice:
            st.warning("Najpierw wybierz odpowiedź!")
        else:
            st.session_state.problem_answered = True 
            
            if choice == problem['correct']:
                # Dynamic XP Scaling Dictionary
                xp_rewards = {1: 5, 2: 10, 3: 20, 4: 35, 5: 60}
                earned_xp = xp_rewards.get(st.session_state.selected_level, 15)
                
                st.session_state.feedback_type = "success"
                st.session_state.feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
                st.session_state.xp += earned_xp
                
                if st.session_state.streak < 3:
                    st.session_state.streak += 1
                
                # Level Up Logic
                if st.session_state.streak == 3 and st.session_state.selected_level == st.session_state.unlocked_level:
                    if st.session_state.unlocked_level < 5:
                        st.session_state.unlocked_level += 1
                        st.session_state.show_balloons = True
                        
                        # --- Auto-Progress Mechanism ---
                        st.session_state.selected_level = st.session_state.unlocked_level
                        st.session_state.streak = 0 # Reset streak for the new level
            
            elif choice == problem['trap']:
                st.session_state.feedback_type = "error"
                st.session_state.feedback_msg = problem['trap_message']
                st.session_state.streak = max(0, st.session_state.streak - 1)
            
            else:
                st.session_state.feedback_type = "warning"
                st.session_state.feedback_msg = problem['wrong_message']
                st.session_state.streak = max(0, st.session_state.streak - 1)
            
            st.rerun()

    # --- 4. PERSISTENT FEEDBACK DISPLAY ---
    if st.session_state.problem_answered:
        if st.session_state.get('feedback_type') == "success":
            st.success(st.session_state.feedback_msg)
            if st.session_state.get('show_balloons'):
                st.balloons()
                # Added text to inform the user they were automatically moved
                st.success(f"🎊 Poziom {st.session_state.unlocked_level} odblokowany! Zostałeś automatycznie przeniesiony na nowy poziom. 🎊")
                st.session_state.show_balloons = False
        elif st.session_state.get('feedback_type') == "error":
            st.error(st.session_state.feedback_msg)
        elif st.session_state.get('feedback_type') == "warning":
            st.warning(st.session_state.feedback_msg)

        if st.button("Następne zadanie ➡️", key="next_problem_btn"):
            st.session_state.current_problem = engine.get_problem_from_db("Addition", st.session_state.selected_level)
            st.session_state.problem_answered = False
            st.rerun()