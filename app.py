import streamlit as st
import engine
import streamlit.components.v1 as components
from core import db

st.set_page_config(page_title="Najszybsza nauka matematyki", page_icon="🧮")

db.init_db()

# --- 1. UTILITIES & HACKS ---
def inject_enter_hack(target_button_text=None):
    """DRY Helper: Injects JS to click a specific button ONLY on a fresh Enter press."""
    if target_button_text is None or target_button_text == "NONE":
        components.html(
            """
            <script>
            const doc = window.parent.document;
            if (doc.customKeyDown) doc.removeEventListener('keydown', doc.customKeyDown, true);
            if (doc.customKeyUp) doc.removeEventListener('keyup', doc.customKeyUp, true);
            </script>
            """,
            height=0,
            width=0,
        )
    else:
        components.html(
            f"""
            <script>
            const doc = window.parent.document;
            
            // 1. Clear old listeners to prevent double-firing
            if (doc.customKeyDown) doc.removeEventListener('keydown', doc.customKeyDown, true);
            if (doc.customKeyUp) doc.removeEventListener('keyup', doc.customKeyUp, true);
            
            let freshPress = false;
            
            // 2. Track when the key is explicitly pressed DOWN on this new screen
            doc.customKeyDown = function(e) {{
                if (e.key === 'Enter' && !e.repeat) {{
                    freshPress = true; 
                }}
            }};
            
            // 3. Only click the button if the key goes UP after being pressed DOWN
            doc.customKeyUp = function(e) {{
                if (e.key === 'Enter' && freshPress) {{
                    const allButtons = Array.from(doc.querySelectorAll('button'));
                    const targetBtn = allButtons.find(b => b.innerText.includes('{target_button_text}'));
                    if (targetBtn) targetBtn.click();
                    freshPress = false; // Reset for safety
                }}
            }};
            
            doc.addEventListener('keydown', doc.customKeyDown, true);
            doc.addEventListener('keyup', doc.customKeyUp, true);
            </script>
            """,
            height=0,
            width=0,
        )


# --- 2. STATE MANAGEMENT ---
class StateManager:
    """Centralizes all state mutations to prevent race conditions during Streamlit reruns."""
    
    @staticmethod
    def init_defaults(macro_topics, curriculum):
        default_state = {
            "xp": 0,
            "streak": 0,
            "selected_macro": macro_topics[0] if macro_topics else None,
            "selected_topic_order": curriculum[macro_topics[0]][0]["Topic_Order"] if macro_topics and curriculum[macro_topics[0]] else 1,
            "selected_level": 1,
            "problem_answered": False,
            "current_input_mode": "radio",
            "topic_completed": False,
            "progress": {},
            "feedback_type": None,
            "feedback_msg": "",
            "show_balloons": False
        }
        
        for key, value in default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value

        # Ensure progress dictionary catches new macro topics AND heals old broken saves
        for mt in macro_topics:
            first_order = curriculum[mt][0]["Topic_Order"] if curriculum[mt] else 1
            if mt not in st.session_state.progress or st.session_state.progress[mt]["unlocked_order"] < first_order:
                st.session_state.progress[mt] = {
                    "unlocked_order": first_order,
                    "unlocked_level": 1,
                }

        # Heal the selected topic order if it's currently broken (None or 1)
        curr_macro = st.session_state.selected_macro
        first_curr = curriculum[curr_macro][0]["Topic_Order"] if curr_macro and curriculum[curr_macro] else 1
        if st.session_state.selected_topic_order is None or st.session_state.selected_topic_order < first_curr:
            st.session_state.selected_topic_order = first_curr

    @staticmethod
    def reset_turn():
        """Clears the current problem state when navigating or advancing."""
        st.session_state.streak = 0
        st.session_state.problem_answered = False
        st.session_state.topic_completed = False
        st.session_state.feedback_type = None
        st.session_state.feedback_msg = ""
        st.session_state.current_input_mode = "radio"
        if "current_problem" in st.session_state:
            del st.session_state["current_problem"]

    @staticmethod
    def load_profile(username, macro_topics, curriculum):
        """Loads user data from DB or initializes a fresh profile."""
        st.session_state.username = username
        user_data = db.load_user(username)

        if user_data:
            st.session_state.xp = user_data["xp"]
            st.session_state.streak = user_data["streak"]
            st.session_state.selected_macro = user_data["selected_macro"]
            st.session_state.selected_topic_order = user_data["selected_topic_order"]
            st.session_state.selected_level = user_data["selected_level"]
            st.session_state.progress = user_data["progress"]
            StateManager.reset_turn()
        else:
            # If it's a new user, reset to level 1 and save immediately
            StateManager.hard_reset(macro_topics, curriculum)

    @staticmethod
    def sync_to_db():
        """Pushes current session state to the database."""
        if st.session_state.get("username"):
            db.save_user(st.session_state.username, st.session_state)

    @staticmethod
    def hard_reset(macro_topics, curriculum):
        """Wipes all progress."""
        st.session_state.xp = 0
        st.session_state.progress = {
            mt: {"unlocked_order": curriculum[mt][0]["Topic_Order"] if curriculum[mt] else 1, "unlocked_level": 1}
            for mt in macro_topics
        }
        st.session_state.selected_macro = macro_topics[0] if macro_topics else None
        st.session_state.selected_topic_order = curriculum[macro_topics[0]][0]["Topic_Order"] if macro_topics and curriculum[macro_topics[0]] else 1
        st.session_state.selected_level = 1
        StateManager.reset_turn()
        StateManager.sync_to_db()

    @staticmethod
    def navigate_to(macro=None, topic_order=None, level=None):
        if macro is not None: st.session_state.selected_macro = macro
        if topic_order is not None: st.session_state.selected_topic_order = topic_order
        if level is not None: st.session_state.selected_level = level
        StateManager.reset_turn()
        StateManager.sync_to_db()


# --- 3. DYNAMIC CURRICULUM SETUP ---
curriculum = engine.get_curriculum()
if not curriculum:
    st.error("Brak dostępnych zadań w bazie.")
    st.stop()

macro_topics = list(curriculum.keys())
StateManager.init_defaults(macro_topics, curriculum)

# Build map for CURRENT macro topic
macro_curr = curriculum[st.session_state.selected_macro]
topic_map = {row["Topic_Order"]: {"name": row["Micro_Topic"], "max_level": row["Level"]} for row in macro_curr}


# --- 4. SIDEBAR: NAVIGATION & PROFILE ---
with st.sidebar:
    st.title("👤 Zaloguj się")
    username_input = st.text_input("Wpisz swoje imię (np. Janek):", key="login_input")
    
    if username_input and username_input != st.session_state.get("username"):
        StateManager.load_profile(username_input, macro_topics, curriculum)
        st.rerun()

    # THE GATE: Stop the app if nobody is logged in
    if not st.session_state.get("username"):
        st.warning("Zaloguj się, aby zapisywać postępy i rozpocząć naukę!")
        st.stop()

    st.markdown("---")
    st.title("🏆 Twój Profil")
    st.metric(label="Punkty Doświadczenia (XP)", value=st.session_state.xp)
    admin_mode = st.toggle("🛠️ Tryb Admina (Odblokuj wszystko)", value=False)

    if st.button("🔄 Zresetuj Postęp"):
        StateManager.hard_reset(macro_topics, curriculum)
        st.rerun()

    st.markdown("---")
    st.title("Ustawienia")

    # Macro Topic Selector
    new_macro = st.selectbox("Wybierz Dział:", macro_topics, index=macro_topics.index(st.session_state.selected_macro))
    if new_macro != st.session_state.selected_macro:
        prog = st.session_state.progress[new_macro]
        StateManager.navigate_to(macro=new_macro, topic_order=prog["unlocked_order"], level=prog["unlocked_level"])
        st.rerun()

    # Micro Topic Selector
    prog = st.session_state.progress[st.session_state.selected_macro]
    first_key = list(topic_map.keys())[0] if topic_map else 1
    unlocked_order = prog.get("unlocked_order", first_key)

    available_orders = list(topic_map.keys()) if admin_mode else [order for order in topic_map.keys() if order <= unlocked_order]
    if not available_orders: available_orders = [first_key]

    def format_topic(order):
        visual_number = list(topic_map.keys()).index(order) + 1 if order in topic_map else 1
        topic_name = topic_map.get(order, {"name": "Nieznany"})["name"]
        return f"{visual_number}. {topic_name}"

    safe_index = available_orders.index(st.session_state.selected_topic_order) if st.session_state.selected_topic_order in available_orders else len(available_orders) - 1
    new_topic_order = st.selectbox("Wybierz Temat:", options=available_orders, format_func=format_topic, index=safe_index)

    if new_topic_order and new_topic_order != st.session_state.selected_topic_order:
        StateManager.navigate_to(topic_order=new_topic_order, level=1)
        st.rerun()

    # Level Selector
    current_topic_max_level = topic_map.get(st.session_state.selected_topic_order, {"max_level": 1}).get("max_level", 1)
    unlocked_lvl = prog.get("unlocked_level", 1)

    allowed_max_level = current_topic_max_level if admin_mode else (current_topic_max_level if st.session_state.selected_topic_order < unlocked_order else min(unlocked_lvl, current_topic_max_level))

    if allowed_max_level == 1 and current_topic_max_level > 1:
        st.info(f"🔒 Aktywny: Poziom 1\n\n*(Zdobądź 3 gwiazdki, aby odblokować kolejne poziomy!)*")
        new_level = 1
    elif current_topic_max_level == 1:
        st.info("Ten temat ma tylko jeden poziom.")
        new_level = 1
    else:
        new_level = st.slider("Wybierz Poziom:", min_value=1, max_value=allowed_max_level, value=min(st.session_state.selected_level, allowed_max_level))

    if new_level != st.session_state.selected_level:
        StateManager.navigate_to(level=new_level)
        st.rerun()


# --- 5. MAIN UI: THE LEARNING LAYER ---
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

problem = st.session_state.current_problem

# Mastery Scoreboard
stars_display = "⭐" * st.session_state.streak + "⬛" * (3 - st.session_state.streak)
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

        cols = st.columns([1, 1])
        with cols[0]: submitted = st.form_submit_button("Sprawdź odpowiedź", disabled=st.session_state.problem_answered)
        with cols[1]: admin_solve = st.form_submit_button("🪄 Auto-Solve", disabled=st.session_state.problem_answered)

        if not st.session_state.problem_answered:
            if not is_text_mode:
                inject_enter_hack("Sprawdź odpowiedź")
            else:
                inject_enter_hack("NONE")

    # --- 6. LOGIC EVALUATION ---
    if admin_solve or submitted:
        is_correct = False

        if admin_solve:
            is_correct = True
            st.session_state.problem_answered = True
        else:
            user_input = user_text if is_text_mode else choice

            if user_input is None or str(user_input).strip() == "":
                st.info("Najpierw podaj odpowiedź!")
                st.stop()

            eval_result = engine.evaluate_answer(user_input, problem, is_text_mode)
            is_correct = eval_result.get("is_correct", False)
            st.session_state.problem_answered = eval_result.get("lock_answer", False)
            st.session_state.feedback_type = eval_result.get("feedback_type", None)
            st.session_state.feedback_msg = eval_result.get("feedback_msg", "")

        # Gamification & Rewards
        if is_correct:
            xp_rewards = {1: 5, 2: 10, 3: 20, 4: 35, 5: 60}
            earned_xp = xp_rewards.get(st.session_state.selected_level, 15)
            
            st.session_state.feedback_type = "success"
            st.session_state.feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
            st.session_state.xp += earned_xp

            if st.session_state.streak < 3: st.session_state.streak += 1

            prog = st.session_state.progress[st.session_state.selected_macro]
            if st.session_state.streak == 3 and st.session_state.selected_level == prog["unlocked_level"]:
                current_topic_max = topic_map[st.session_state.selected_topic_order]["max_level"]

                if prog["unlocked_level"] < current_topic_max:
                    prog["unlocked_level"] += 1
                    st.session_state.show_balloons = "level"
                    st.session_state.selected_level = prog["unlocked_level"]
                    st.session_state.streak = 0
                else:
                    st.session_state.topic_completed = True
                    st.session_state.show_balloons = "topic"
                    st.session_state.streak = 0

        elif not is_correct and st.session_state.streak > 0:
            if st.session_state.feedback_type != "info": 
                st.session_state.streak -= 1

        StateManager.sync_to_db() 
        st.rerun()

# --- 7. PERSISTENT FEEDBACK & NEXT STEPS ---
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
                StateManager.navigate_to(topic_order=next_topic_id, level=1)
                StateManager.sync_to_db()
                st.rerun()
            else:
                st.success("🎉 Gratulacje! Ukończyłeś cały ten dział. Wybierz nowy dział z menu po lewej stronie.")
        else:
            old_prob = st.session_state.current_problem
            
            def is_duplicate(old, new):
                if not old: return False
                return old.get("question") == new.get("question") and old.get("correct") == new.get("correct") and old.get("image_html") == new.get("image_html")

            attempts = 0
            while attempts < 10:
                new_problem = engine.get_problem_from_db(
                    st.session_state.selected_macro,
                    topic_map[st.session_state.selected_topic_order]["name"],
                    st.session_state.selected_level,
                )
                if not is_duplicate(old_prob, new_problem):
                    break
                attempts += 1
            
            st.session_state.current_problem = new_problem
            st.session_state.problem_answered = False
            st.session_state.feedback_type = None
            
            if st.session_state.streak >= 1 and "Porównywanie" not in topic_map[st.session_state.selected_topic_order]["name"]:
                st.session_state.current_input_mode = "text"
            else:
                st.session_state.current_input_mode = "radio"
                
            st.rerun()