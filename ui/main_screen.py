import streamlit as st
import time
import engine
from state_manager import StateManager
import config
from core.utils import clean_mobile_input, clean_latex
from ui.components import inject_enter_hack, inject_decimal_keyboard

# Module-level helper functions (avoid recreating on every render)

def format_radio_option(opt):
    """Format radio option: wrap LaTeX in $ delimiters for proper rendering."""
    return f"${opt}$" if "\\" in opt else opt


def is_duplicate(old, new):
    """Check if two problems are identical (same question, answer, and image)."""
    if not old:
        return False
    return (
        old.get("question") == new.get("question")
        and old.get("correct") == new.get("correct")
        and old.get("image_html") == new.get("image_html")
    )


def render_learning_screen(state, problem, topic_map):
    st.title("🧮 Najlepszy nauczyciel matematyki")
    st.subheader(f"Dział: {state.selected_macro}")
    st.markdown(f"**Temat: {topic_map[state.selected_topic_order]['name']}**")

    # Fetch Problem
    if "current_problem" not in state:
        state.current_problem = engine.get_problem_from_db(
            state.selected_macro,
            topic_map[state.selected_topic_order]["name"],
            state.selected_level,
        )
        state.problem_start_time = time.time()

    problem = state.current_problem

    # Mastery Scoreboard
    stars_display = "⭐" * state.streak + "⬛" * (config.MAX_STREAK - state.streak)
    st.markdown(f"### Postęp do kolejnego poziomu: {stars_display}")

    submitted = False
    admin_solve = False

    if problem is None or "error" in problem:
        st.error(f"❌ Nie można załadować zadania. Sprawdź plik CSV. Błąd: {problem.get('error', 'Unknown') if problem else 'None'}")
    else:
        st.write("---")
        st.info(f"📍 {problem.get('level_display', 'Level ' + str(state.selected_level))}")

        # Anticipation Bar - Macro Topic Progress
        macro_topic = state.selected_macro
        curriculum_map_for_progress = {macro_topic: topic_map} if macro_topic and topic_map else {}
        if macro_topic:
            percentage, completed, total = StateManager.get_macro_progress(state, macro_topic, curriculum_map_for_progress)
            st.markdown(f"### 🏆 {macro_topic}: {completed}/{total} ukończonych tematów")
            st.progress(percentage)
            st.markdown("---")

        # Anticipation Bar - Micro Topic Progress
        micro_topic = topic_map[state.selected_topic_order]['name']
        current_level = state.selected_level
        total_levels = topic_map[state.selected_topic_order]['max_level']
        
        # Calculate completed levels: current_level - 1 (e.g., on Level 1 = 0 completed)
        completed_levels = current_level - 1
        completed_levels = min(completed_levels, total_levels)  # Ensure doesn't exceed total
        
        # Calculate progress percentage with division by zero safety
        micro_progress_pct = completed_levels / total_levels if total_levels > 0 else 0.0
        
        st.markdown(f"### 📚 {micro_topic}: Poziom {current_level}/{total_levels}")
        st.progress(micro_progress_pct)
        st.markdown("---")

        # Render Task
        st.header("Zadanie:")
        st.markdown(f"<div id='{problem['problem_id']}'></div>", unsafe_allow_html=True)
        st.latex(problem["question"])
        if problem.get("image_html"):
            st.markdown(problem["image_html"], unsafe_allow_html=True)

        if "shuffled_options" not in state or state.get("last_id") != problem["problem_id"]:
            state.shuffled_options = problem["options"]
            state.last_id = problem["problem_id"]
            state.problem_answered = False

        # Form rendering
        with st.form("answer_form", border=False):
            if state.current_input_mode == "radio":
                st.markdown("<style>.stRadio label { padding-bottom: 25px; padding-top: 10px; }</style>", unsafe_allow_html=True)
                choice = st.radio("Wybierz wynik:", state.shuffled_options, index=None, format_func=format_radio_option)
                is_text_mode = False
            else:
                st.info("Wpisz wynik samodzielnie bez podpowiedzi.")
                st.markdown("*(Format wprowadzania: wpisz **3/4**, a dla liczb mieszanych **1 1/2**)*")
                user_text = st.text_input("Twoja odpowiedź:", key=f"text_input_{state.last_id}")
                is_text_mode = True

            # --- CONTEXT AWARE KEYBOARD INJECTION ---
                # Only force the numpad if the topic safely supports it
                if state.selected_macro == "Ułamki Dziesiętne":
                    inject_decimal_keyboard()

            cols = st.columns([1, 1])
            with cols[0]: submitted = st.form_submit_button("Sprawdź odpowiedź", disabled=state.problem_answered)
            with cols[1]: admin_solve = st.form_submit_button("🪄 Auto-Solve", disabled=state.problem_answered)

            if not state.problem_answered:
                if not is_text_mode:
                    inject_enter_hack("Sprawdź odpowiedź")
                else:
                    inject_enter_hack("NONE")

        # --- LOGIC EVALUATION ---
        if admin_solve or submitted:
            if admin_solve:
                correct_val = problem["correct"]
                
                # Convert to string, handling pandas float→int conversions (5.0 → 5)
                if isinstance(correct_val, float):
                    raw_input = str(int(correct_val) if correct_val.is_integer() else correct_val)
                else:
                    raw_input = str(correct_val)
                
                # If LaTeX format detected, convert to readable format first
                if "\\" in raw_input:
                    raw_input = clean_latex(raw_input)
                
                # Sanitize as if a user typed it: normalize spaces, decimals, etc.
                user_input = clean_mobile_input(raw_input)
                # Auto-solve always uses text mode evaluation
                eval_mode = True
            else:
                user_input = user_text if is_text_mode else choice

                if user_input is None or str(user_input).strip() == "":
                    st.info("Najpierw podaj odpowiedź!")
                    st.stop()
                
                if is_text_mode and isinstance(user_input, str):
                    user_input = clean_mobile_input(user_input)
                
                eval_mode = is_text_mode

            StateManager.process_submission(state, problem, user_input, eval_mode, topic_map)
            StateManager.sync_to_db(state) 
            st.rerun()

    # --- 5. PERSISTENT FEEDBACK & NEXT STEPS ---
    if state.problem_answered or state.get("feedback_type") in ["info", "warning"]:
        fb_type = state.get("feedback_type")
        if fb_type == "success":
            st.success(state.feedback_msg)
            if state.get("show_balloons") == "level":
                st.balloons()
                st.success(f"🎊 Poziom {state.progress[state.selected_macro]['unlocked_level']} odblokowany! Zostałeś automatycznie przeniesiony na nowy poziom. 🎊")
                state.show_balloons = False
            elif state.get("show_balloons") == "topic":
                st.balloons()
                st.success("🏆 Gratulacje! Ukończyłeś cały temat. Jesteś gotowy, aby przejść do kolejnego!")
                state.show_balloons = False
        elif fb_type == "error": st.error(state.feedback_msg)
        elif fb_type == "warning": st.warning(state.feedback_msg)
        elif fb_type == "info": st.info(state.feedback_msg)

    if state.problem_answered:
        button_label = "Przejdź do kolejnego tematu ➡️" if state.topic_completed else "Następne zadanie ➡️"
        
        inject_enter_hack(button_label)

        if st.button(button_label, key="next_problem_btn"):
            if state.topic_completed:
                next_topics = [t for t in topic_map.keys() if t > state.selected_topic_order]
                if next_topics:
                    next_topic_id = min(next_topics)
                    state.progress[state.selected_macro]["unlocked_order"] = next_topic_id
                    state.progress[state.selected_macro]["unlocked_level"] = 1
                    StateManager.navigate_to(state, topic_order=next_topic_id, level=1)
                    StateManager.sync_to_db(state)
                    st.rerun()
                else:
                    st.success("🎉 Gratulacje! Ukończyłeś cały ten dział. Wybierz nowy dział z menu po lewej stronie.")
            else:
                old_prob = state.current_problem
                attempts = 0
                while attempts < config.MAX_RETRIES_DUPLICATE_CHECK:
                    new_problem = engine.get_problem_from_db(
                        state.selected_macro,
                        topic_map[state.selected_topic_order]["name"],
                        state.selected_level,
                    )
                    if not is_duplicate(old_prob, new_problem):
                        state.problem_start_time = time.time()
                        break
                    attempts += 1
                
                state.current_problem = new_problem
                state.problem_answered = False
                state.feedback_type = None
                
                if state.streak >= config.STREAK_THRESHOLD_FOR_TEXT_MODE and "Porównywanie" not in topic_map[state.selected_topic_order]["name"]:
                    state.current_input_mode = "text"
                else:
                    state.current_input_mode = "radio"
                    
                st.rerun()