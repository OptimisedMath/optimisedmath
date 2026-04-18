import streamlit as st
import engine
import random
import re
import streamlit.components.v1 as components
from fractions import Fraction

st.set_page_config(page_title="Najszybsza nauka matematyki", page_icon="🧮")

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
            """, height=0, width=0
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
            """, height=0, width=0
        )

def reset_turn_state(rerun=True):
    """DRY Helper: Clears the current problem state when navigating."""
    st.session_state.streak = 0
    st.session_state.problem_answered = False
    st.session_state.current_input_mode = "radio"
    st.session_state.topic_completed = False
    if 'current_problem' in st.session_state: 
        del st.session_state['current_problem']
    if rerun:
        st.rerun()

# --- DYNAMIC CURRICULUM BUILDER ---
curriculum = engine.get_curriculum()
if not curriculum:
    st.error("Brak dostępnych zadań w bazie.")
    st.stop()

macro_topics = list(curriculum.keys())

# --- 1. INITIALIZE GAME STATE ---
default_state = {
    'xp': 0, 'streak': 0, 
    'selected_macro': macro_topics[0],
    'selected_topic_order': 1,
    'selected_level': 1,
    'problem_answered': False, 'current_input_mode': "radio",
    'topic_completed': False,
    'progress': {} # Isolated progress for each macro topic
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Ensure progress dict catches any new macro topics added to the CSV
for mt in macro_topics:
    if mt not in st.session_state.progress:
        st.session_state.progress[mt] = {'unlocked_order': 1, 'unlocked_level': 1}

# Build map for CURRENT macro topic
macro_curr = curriculum[st.session_state.selected_macro]
topic_map = {row['Topic_Order']: {"name": row['Micro_Topic'], "max_level": row['Level']} for row in macro_curr}

# --- SIDEBAR: Player Profile & Level Selector ---
with st.sidebar:
    st.title("🏆 Twój Profil")
    st.metric(label="Punkty Doświadczenia (XP)", value=st.session_state.xp)
    
    admin_mode = st.toggle("🛠️ Tryb Admina (Odblokuj wszystko)", value=False)
    
    if st.button("🔄 Zresetuj Postęp"):
        st.session_state.xp = 0
        st.session_state.streak = 0
        st.session_state.progress = {mt: {'unlocked_order': 1, 'unlocked_level': 1} for mt in macro_topics}
        st.session_state.selected_macro = macro_topics[0]
        st.session_state.selected_topic_order = 1
        st.session_state.selected_level = 1
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio" 
        st.session_state.topic_completed = False
        if 'current_problem' in st.session_state: del st.session_state['current_problem']
        st.rerun()

    st.markdown("---")
    st.title("Ustawienia")
    
    # 1. MACRO TOPIC SELECTOR
    new_macro = st.selectbox("Wybierz Dział:", macro_topics, index=macro_topics.index(st.session_state.selected_macro))
    
    if new_macro != st.session_state.selected_macro:
        st.session_state.selected_macro = new_macro
        prog = st.session_state.progress[new_macro]
        st.session_state.selected_topic_order = prog['unlocked_order']
        st.session_state.selected_level = prog['unlocked_level']
        st.session_state.streak = 0
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio"
        st.session_state.topic_completed = False
        if 'current_problem' in st.session_state: del st.session_state['current_problem']
        st.rerun()
    
    # 2. MICRO TOPIC SELECTOR
    prog = st.session_state.progress[st.session_state.selected_macro]
    if admin_mode:
        available_orders = list(topic_map.keys())
    else:
        available_orders = [order for order in topic_map.keys() if order <= prog['unlocked_order']]

    def format_topic(order):
        return f"{order}. {topic_map[order]['name']}"
        
    new_topic_order = st.selectbox(
        "Wybierz Temat:", 
        options=available_orders, 
        format_func=format_topic,
        index=available_orders.index(st.session_state.selected_topic_order) if st.session_state.selected_topic_order in available_orders else len(available_orders)-1
    )
    
    if new_topic_order != st.session_state.selected_topic_order:
        st.session_state.selected_topic_order = new_topic_order
        st.session_state.selected_level = 1
        reset_turn_state()

    # 3. LEVEL SELECTOR
    current_topic_max_level = topic_map[st.session_state.selected_topic_order]['max_level']
    
    if admin_mode:
        allowed_max_level = current_topic_max_level
    elif st.session_state.selected_topic_order < prog['unlocked_order']:
        allowed_max_level = current_topic_max_level 
    else:
        allowed_max_level = min(prog['unlocked_level'], current_topic_max_level)
    
    if allowed_max_level == 1 and current_topic_max_level > 1:
        st.info(f"🔒 Aktywny: Poziom 1\n\n*(Zdobądź 3 gwiazdki, aby odblokować kolejne poziomy!)*")
        new_level = 1
    elif current_topic_max_level == 1:
        st.info("Ten temat ma tylko jeden poziom.")
        new_level = 1
    else:
        safe_selected_level = min(st.session_state.selected_level, allowed_max_level)
        new_level = st.slider("Wybierz Poziom:", min_value=1, max_value=allowed_max_level, value=safe_selected_level)
    
    if new_level != st.session_state.selected_level:
        st.session_state.selected_level = new_level
        st.session_state.streak = 0 
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio"
        st.session_state.topic_completed = False
        if 'current_problem' in st.session_state: del st.session_state['current_problem']
        st.rerun()

st.title("🧮 Najlepszy nauczyciel matematyki")

st.subheader(f"Dział: {st.session_state.selected_macro}")
st.markdown(f"**Temat: {topic_map[st.session_state.selected_topic_order]['name']}**")

# Fetch initial problem if missing
if 'current_problem' not in st.session_state:
    st.session_state.current_problem = engine.get_problem_from_db(
        st.session_state.selected_macro,
        topic_map[st.session_state.selected_topic_order]['name'], 
        st.session_state.selected_level
    )

problem: dict | None = st.session_state.current_problem

# --- 2. THE MASTERY SCOREBOARD ---
stars_display = "⭐" * st.session_state.streak + "⬛" * (3 - st.session_state.streak)
st.markdown(f"### Postęp do kolejnego poziomu: {stars_display}")

submitted = False
admin_solve = False

if problem is None or "error" in problem:
    st.error(f"❌ Nie można załadować Poziomu {st.session_state.selected_level}. Sprawdź plik CSV.")
else:
    st.write("---")
    st.info(f"📍 {problem.get('level_display', 'Level ' + str(st.session_state.selected_level))}") 
    
    st.header("Zadanie:")
    st.markdown(f"<div id='{problem['problem_id']}'></div>", unsafe_allow_html=True)
    st.latex(problem['question'])
    
    if problem.get('image_html'):
        st.markdown(problem['image_html'], unsafe_allow_html=True)

    if 'shuffled_options' not in st.session_state or st.session_state.get('last_id') != problem['problem_id']:
        st.session_state.shuffled_options = problem['options']
        st.session_state.last_id = problem['problem_id']
        st.session_state.problem_answered = False 

    with st.form("answer_form", border=False):
        if st.session_state.current_input_mode == "radio":
            st.markdown("<style>.stRadio label { padding-bottom: 25px; padding-top: 10px; }</style>", unsafe_allow_html=True)
            
            # Format UI rendering: if string contains \frac or \cdot, use math mode, else normal text
            def render_ui_option(opt):
                if "\\" in opt: return f"${opt}$"
                return opt

            choice = st.radio("Wybierz wynik:", st.session_state.shuffled_options, index=None, format_func=render_ui_option)
            is_text_mode = False
        else:
            st.info("Wpisz wynik samodzielnie bez podpowiedzi.")
            st.markdown("*(Format wprowadzania: wpisz **3/4**, a dla liczb mieszanych **1 1/2**)*")
            user_text = st.text_input("Twoja odpowiedź:", key=f"text_input_{st.session_state.last_id}")
            is_text_mode = True
        
        cols = st.columns([1, 1])
        with cols[0]:
            submitted = st.form_submit_button("Sprawdź odpowiedź", disabled=st.session_state.problem_answered)
        with cols[1]:
            admin_solve = st.form_submit_button("🪄 Auto-Solve", disabled=st.session_state.problem_answered)
            
        if not st.session_state.problem_answered:
            if not is_text_mode:
                inject_enter_hack("Sprawdź odpowiedź")
            else:
                inject_enter_hack("NONE")

# --- 3. CHECK LOGIC & GAMIFICATION ---
if admin_solve or submitted:
    is_correct = False

    if admin_solve:
        is_correct = True
        st.session_state.problem_answered = True
        
    else:
        # THE UI IS DUMB: It just asks the Engine to grade the answer!
        user_input = user_text if is_text_mode else choice
        
        # --- THE FIX: Catch empty answers BEFORE they reach the engine! ---
        if user_input is None or str(user_input).strip() == "":
            st.info("Najpierw podaj odpowiedź!")
            st.stop() # Stops the script immediately so it doesn't grade or penalize you
        # ------------------------------------------------------------------

        eval_result = engine.evaluate_answer(user_input, problem, is_text_mode)
        
        is_correct = eval_result.get("is_correct", False)
        st.session_state.problem_answered = eval_result.get("lock_answer", False)
        st.session_state.feedback_type = eval_result.get("feedback_type", None)
        st.session_state.feedback_msg = eval_result.get("feedback_msg", "")
        
    # --- 3. REWARD & PROGRESSION LOGIC ---
    if is_correct:
        xp_rewards = {1: 5, 2: 10, 3: 20, 4: 35, 5: 60}
        earned_xp = xp_rewards.get(st.session_state.selected_level, 15)
        
        st.session_state.feedback_type = "success"
        st.session_state.feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
        st.session_state.xp += earned_xp
        
        if st.session_state.streak < 3:
            st.session_state.streak += 1
        
        prog = st.session_state.progress[st.session_state.selected_macro]
        if st.session_state.streak == 3 and st.session_state.selected_level == prog['unlocked_level']:
            current_topic_max = topic_map[st.session_state.selected_topic_order]['max_level']
            
            if prog['unlocked_level'] < current_topic_max:
                prog['unlocked_level'] += 1
                st.session_state.show_balloons = "level"
                st.session_state.selected_level = prog['unlocked_level']
                st.session_state.streak = 0 
            else:
                st.session_state.topic_completed = True
                st.session_state.show_balloons = "topic"
                st.session_state.streak = 0
    
    # Penalize streak ONLY if it's a hard error, not a soft "info" warning
    elif not is_correct and st.session_state.streak > 0:
        if st.session_state.feedback_type != "info":
            st.session_state.streak -= 1
    
    st.rerun()

# --- 4. PERSISTENT FEEDBACK DISPLAY ---
if st.session_state.problem_answered or st.session_state.get('feedback_type') in ["info", "warning"]:
    if st.session_state.get('feedback_type') == "success":
        st.success(st.session_state.feedback_msg)
        
        if st.session_state.get('show_balloons') == "level":
            st.balloons()
            prog = st.session_state.progress[st.session_state.selected_macro]
            st.success(f"🎊 Poziom {prog['unlocked_level']} odblokowany! Zostałeś automatycznie przeniesiony na nowy poziom. 🎊")
            st.session_state.show_balloons = False
        elif st.session_state.get('show_balloons') == "topic":
            st.balloons()
            st.success("🏆 Gratulacje! Ukończyłeś cały temat. Jesteś gotowy, aby przejść do kolejnego!")
            st.session_state.show_balloons = False
            
    elif st.session_state.get('feedback_type') == "error":
        st.error(st.session_state.feedback_msg)
    elif st.session_state.get('feedback_type') == "warning":
        st.warning(st.session_state.feedback_msg)
    elif st.session_state.get('feedback_type') == "info":
        st.info(st.session_state.feedback_msg) 

if st.session_state.problem_answered:
    if not st.session_state.get('topic_completed'):
        inject_enter_hack("Następne zadanie" if not st.session_state.get('topic_completed') else "NONE")

    button_label = "Przejdź do kolejnego tematu ➡️" if st.session_state.get('topic_completed') else "Następne zadanie ➡️"

    if st.button(button_label, key="next_problem_btn"):
        
        # --- EXECUTE TOPIC JUMP ---
        if st.session_state.get('topic_completed'):
            next_topics = [t for t in topic_map.keys() if t > st.session_state.selected_topic_order]
            if next_topics:
                next_topic_id = min(next_topics)
                st.session_state.progress[st.session_state.selected_macro]['unlocked_order'] = next_topic_id
                st.session_state.progress[st.session_state.selected_macro]['unlocked_level'] = 1
                
                st.session_state.selected_topic_order = next_topic_id
                st.session_state.selected_level = 1
                st.session_state.topic_completed = False
                st.session_state.streak = 0
                st.session_state.problem_answered = False
                st.session_state.current_input_mode = "radio"
                if 'current_problem' in st.session_state: del st.session_state['current_problem']
                st.rerun()
            else:
                st.success("🎉 Gratulacje! Ukończyłeś cały ten dział. Wybierz nowy dział z menu po lewej stronie.")
            
        # --- NORMAL NEXT PROBLEM LOGIC ---
        else:
            old_prob = st.session_state.current_problem
            
            new_problem = engine.get_problem_from_db(
                st.session_state.selected_macro,
                topic_map[st.session_state.selected_topic_order]['name'], 
                st.session_state.selected_level
            )
            
            if new_problem is None or 'error' in new_problem:
                st.error("Błąd krytyczny: Nie można załadować bazy zadań z pliku CSV!")
                st.stop() 
            
            # FIX: Smart Duplicate Checker (Checks math and images, not just static text)
            def is_duplicate(old, new):
                if not old: return False
                return (old.get('question') == new.get('question') and 
                        old.get('correct') == new.get('correct') and 
                        old.get('image_html') == new.get('image_html'))

            # We also add a max-attempt limit of 10 so the UI can NEVER freeze the server
            attempts = 0
            while is_duplicate(old_prob, new_problem) and attempts < 10:
                new_problem = engine.get_problem_from_db(
                    st.session_state.selected_macro,
                    topic_map[st.session_state.selected_topic_order]['name'], 
                    st.session_state.selected_level
                )
                attempts += 1
            
            st.session_state.current_problem = new_problem
            st.session_state.problem_answered = False
            st.session_state.feedback_type = None 
            
            if st.session_state.streak >= 2 and "Porównywanie" not in topic_map[st.session_state.selected_topic_order]['name']:
                st.session_state.current_input_mode = "text"
            else:
                st.session_state.current_input_mode = "radio"
                
            st.rerun()