import streamlit as st
import engine
from core import db
from core.utils import clean_mobile_input
from state_manager import StateManager
import config
import time
from ui.components import inject_enter_hack, inject_decimal_keyboard
from ui.login import render_login_gate
from ui.sidebar import render_sidebar

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



# --- 3. MAIN UI: THE LEARNING LAYER ---
st.title("🧮 Najlepszy nauczyciel matematyki")
st.subheader(f"Dział: {st.session_state.selected_macro}")
st.markdown(f"**Temat: {topic_map[st.session_state.selected_topic_order]['name']}**")

# Fetch Problem
if "current_problem" not in st.session_state:
    st.session_state.current_problem = engine.get_problem_from_db(
        st.session_state.selected_macro,
        topic_map[st.session_state.selected_topic_order]["name"],
        st.session_state.selected_level,
    )
    st.session_state.problem_start_time = time.time()

problem = st.session_state.current_problem

# Mastery Scoreboard
stars_display = "⭐" * st.session_state.streak + "⬛" * (config.MAX_STREAK - st.session_state.streak)
st.markdown(f"### Postęp do kolejnego poziomu: {stars_display}")

submitted = False
admin_solve = False

if problem is None or "error" in problem:
    st.error(f"❌ Nie można załadować zadania. Sprawdź plik CSV. Błąd: {problem.get('error', 'Unknown') if problem else 'None'}")
else:
    st.write("---")
    st.info(f"📍 {problem.get('level_display', 'Level ' + str(st.session_state.selected_level))}")

    # Render Task
    st.header("Zadanie:")
    st.markdown(f"<div id='{problem['problem_id']}'></div>", unsafe_allow_html=True)
    st.latex(problem["question"])
    if problem.get("image_html"):
        st.markdown(problem["image_html"], unsafe_allow_html=True)

    if "shuffled_options" not in st.session_state or st.session_state.get("last_id") != problem["problem_id"]:
        st.session_state.shuffled_options = problem["options"]
        st.session_state.last_id = problem["problem_id"]
        st.session_state.problem_answered = False

    # Form rendering
    with st.form("answer_form", border=False):
        if st.session_state.current_input_mode == "radio":
            st.markdown("<style>.stRadio label { padding-bottom: 25px; padding-top: 10px; }</style>", unsafe_allow_html=True)
            render_ui_option = lambda opt: f"${opt}$" if "\\" in opt else opt
            choice = st.radio("Wybierz wynik:", st.session_state.shuffled_options, index=None, format_func=render_ui_option)
            is_text_mode = False
        else:
            st.info("Wpisz wynik samodzielnie bez podpowiedzi.")
            st.markdown("*(Format wprowadzania: wpisz **3/4**, a dla liczb mieszanych **1 1/2**)*")
            user_text = st.text_input("Twoja odpowiedź:", key=f"text_input_{st.session_state.last_id}")
            is_text_mode = True

        # --- CONTEXT AWARE KEYBOARD INJECTION ---
            # Only force the numpad if the topic safely supports it
            if st.session_state.selected_macro == "Ułamki dziesiętne":
                inject_decimal_keyboard()

        cols = st.columns([1, 1])
        with cols[0]: submitted = st.form_submit_button("Sprawdź odpowiedź", disabled=st.session_state.problem_answered)
        with cols[1]: admin_solve = st.form_submit_button("🪄 Auto-Solve", disabled=st.session_state.problem_answered)

        if not st.session_state.problem_answered:
            if not is_text_mode:
                inject_enter_hack("Sprawdź odpowiedź")
            else:
                inject_enter_hack("NONE")

    # --- 4. LOGIC EVALUATION ---
    if admin_solve or submitted:
        if admin_solve:
            is_correct = True
            st.session_state.problem_answered = True
            st.session_state.feedback_type = "success"
            st.session_state.feedback_msg = "Brawo! To poprawna odpowiedź. 🎉 (+0 XP)"
        else:
            user_input = user_text if is_text_mode else choice

            if user_input is None or str(user_input).strip() == "":
                st.info("Najpierw podaj odpowiedź!")
                st.stop()
            
            if is_text_mode and isinstance(user_input, str):
                user_input = clean_mobile_input(user_input)

            StateManager.process_submission(st.session_state, problem, user_input, is_text_mode, topic_map)

        StateManager.sync_to_db(st.session_state) 
        st.rerun()

# --- 5. PERSISTENT FEEDBACK & NEXT STEPS ---
if st.session_state.problem_answered or st.session_state.get("feedback_type") in ["info", "warning"]:
    fb_type = st.session_state.get("feedback_type")
    if fb_type == "success":
        st.success(st.session_state.feedback_msg)
        if st.session_state.get("show_balloons") == "level":
            st.balloons()
            st.success(f"🎊 Poziom {st.session_state.progress[st.session_state.selected_macro]['unlocked_level']} odblokowany! Zostałeś automatycznie przeniesiony na nowy poziom. 🎊")
            st.session_state.show_balloons = False
        elif st.session_state.get("show_balloons") == "topic":
            st.balloons()
            st.success("🏆 Gratulacje! Ukończyłeś cały temat. Jesteś gotowy, aby przejść do kolejnego!")
            st.session_state.show_balloons = False
    elif fb_type == "error": st.error(st.session_state.feedback_msg)
    elif fb_type == "warning": st.warning(st.session_state.feedback_msg)
    elif fb_type == "info": st.info(st.session_state.feedback_msg)

if st.session_state.problem_answered:
    button_label = "Przejdź do kolejnego tematu ➡️" if st.session_state.topic_completed else "Następne zadanie ➡️"
    
    inject_enter_hack(button_label)

    if st.button(button_label, key="next_problem_btn"):
        if st.session_state.topic_completed:
            next_topics = [t for t in topic_map.keys() if t > st.session_state.selected_topic_order]
            if next_topics:
                next_topic_id = min(next_topics)
                st.session_state.progress[st.session_state.selected_macro]["unlocked_order"] = next_topic_id
                st.session_state.progress[st.session_state.selected_macro]["unlocked_level"] = 1
                StateManager.navigate_to(st.session_state, topic_order=next_topic_id, level=1)
                StateManager.sync_to_db(st.session_state)
                st.rerun()
            else:
                st.success("🎉 Gratulacje! Ukończyłeś cały ten dział. Wybierz nowy dział z menu po lewej stronie.")
        else:
            old_prob = st.session_state.current_problem
            
            def is_duplicate(old, new):
                if not old: return False
                return old.get("question") == new.get("question") and old.get("correct") == new.get("correct") and old.get("image_html") == new.get("image_html")

            attempts = 0
            while attempts < config.MAX_RETRIES_DUPLICATE_CHECK:
                new_problem = engine.get_problem_from_db(
                    st.session_state.selected_macro,
                    topic_map[st.session_state.selected_topic_order]["name"],
                    st.session_state.selected_level,
                )
                if not is_duplicate(old_prob, new_problem):
                    st.session_state.problem_start_time = time.time()
                    break
                attempts += 1
            
            st.session_state.current_problem = new_problem
            st.session_state.problem_answered = False
            st.session_state.feedback_type = None
            
            if st.session_state.streak >= config.STREAK_THRESHOLD_FOR_TEXT_MODE and "Porównywanie" not in topic_map[st.session_state.selected_topic_order]["name"]:
                st.session_state.current_input_mode = "text"
            else:
                st.session_state.current_input_mode = "radio"
                
            st.rerun()