import streamlit as st
import engine
import random
import re
import streamlit.components.v1 as components
from fractions import Fraction
from core.utils import check_text_answer, parse_to_fraction

st.set_page_config(page_title="Najszybsza nauka matematyki", page_icon="🧮")

# --- 1. INITIALIZE GAME STATE ---
default_state = {
    'xp': 0, 'streak': 0, 
    'unlocked_topic_order': 1, 'selected_topic_order': 1,
    'unlocked_level': 1, 'selected_level': 1,
    'problem_answered': False, 'current_input_mode': "radio",
    'topic_completed': False
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

def inject_enter_hack(target_button_text=None, delay_ms=300):
    """DRY Helper: Injects JS to click a specific button when Enter is pressed."""
    if target_button_text is None:
        components.html(
            """
            <script>
            const doc = window.parent.document;
            if (doc.customKeyListener) {
                doc.removeEventListener('keyup', doc.customKeyListener, true);
            }
            </script>
            """, height=0, width=0
        )
    else:
        components.html(
            f"""
            <script>
            const doc = window.parent.document;
            if (doc.customKeyListener) {{
                doc.removeEventListener('keyup', doc.customKeyListener, true);
            }}
            doc.customKeyListener = function(e) {{
                if (e.key === 'Enter') {{
                    const allButtons = Array.from(doc.querySelectorAll('button'));
                    const targetBtn = allButtons.find(b => b.innerText.includes('{target_button_text}'));
                    if (targetBtn) targetBtn.click();
                }}
            }};
            setTimeout(() => {{
                doc.addEventListener('keyup', doc.customKeyListener, true);
            }}, {delay_ms});
            </script>
            """, height=0, width=0
        )

# --- DYNAMIC CURRICULUM BUILDER ---
curriculum = engine.get_curriculum()
if not curriculum:
    st.error("Brak dostępnych zadań w bazie.")
    st.stop()

# Build a dictionary for easy lookup: {Order: {"name": Name, "max_level": MaxLevel}}
topic_map = {row['Topic_Order']: {"name": row['Micro_Topic'], "max_level": row['Level']} for row in curriculum}

# --- SIDEBAR: Player Profile & Level Selector ---
with st.sidebar:
    st.title("🏆 Twój Profil")
    st.metric(label="Punkty Doświadczenia (XP)", value=st.session_state.xp)
    
    # --- 🛠️ THE ADMIN FEATURE FLAG ---
    admin_mode = st.toggle("🛠️ Tryb Admina (Odblokuj wszystko)", value=False)
    
    if st.button("🔄 Zresetuj Postęp"):
        st.session_state.xp = 0
        st.session_state.streak = 0
        st.session_state.unlocked_topic_order = 5 # Reset back to the first available topic
        st.session_state.unlocked_level = 1
        st.session_state.selected_topic_order = 5
        st.session_state.selected_level = 1
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio" 
        st.session_state.current_problem = engine.get_problem_from_db(topic_map[5]['name'], 1)
        st.session_state.topic_completed = False
        st.rerun()

    st.markdown("---")
    st.title("Ustawienia")
    
    # 1. TOPIC SELECTOR
    if admin_mode:
        available_orders = list(topic_map.keys()) # Admin sees everything
    else:
        available_orders = [order for order in topic_map.keys() if order <= st.session_state.unlocked_topic_order]

    # Formatting function for the selectbox so it looks nice
    def format_topic(order):
        return f"{order}. {topic_map[order]['name']}"
        
    new_topic_order = st.selectbox(
        "Wybierz Temat:", 
        options=available_orders, 
        format_func=format_topic,
        # If admin mode hides a topic we were just looking at, default back to the highest unlocked
        index=available_orders.index(st.session_state.selected_topic_order) if st.session_state.selected_topic_order in available_orders else len(available_orders)-1
    )
    
    # If the user changes the topic, reset their level selection to 1
    if new_topic_order != st.session_state.selected_topic_order:
        st.session_state.selected_topic_order = new_topic_order
        st.session_state.selected_level = 1
        st.session_state.streak = 0
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio"
        st.session_state.current_problem = engine.get_problem_from_db(topic_map[new_topic_order]['name'], 1)
        st.session_state.topic_completed = False
        st.rerun()

    # 2. LEVEL SELECTOR
    current_topic_max_level = topic_map[st.session_state.selected_topic_order]['max_level']
    
    # Determine how many levels they are allowed to see in the slider
    if admin_mode:
        allowed_max_level = current_topic_max_level # Admin can access any level
    elif st.session_state.selected_topic_order < st.session_state.unlocked_topic_order:
        # If they went back to an older topic, all levels are unlocked
        allowed_max_level = current_topic_max_level 
    else:
        # If they are on their highest unlocked topic, restrict by unlocked_level
        allowed_max_level = min(st.session_state.unlocked_level, current_topic_max_level)
    
    if allowed_max_level == 1 and current_topic_max_level > 1:
        st.info(f"🔒 Aktywny: Poziom 1\n\n*(Zdobądź 3 gwiazdki, aby odblokować kolejne poziomy!)*")
        new_level = 1
    elif current_topic_max_level == 1:
        st.info("Ten temat ma tylko jeden poziom.")
        new_level = 1
    else:
        # If admin mode drops our allowed max level below our current selection, force us down safely
        safe_selected_level = min(st.session_state.selected_level, allowed_max_level)
        new_level = st.slider("Wybierz Poziom:", min_value=1, max_value=allowed_max_level, value=safe_selected_level)
    
    if new_level != st.session_state.selected_level:
        st.session_state.selected_level = new_level
        st.session_state.streak = 0 
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio"
        st.session_state.current_problem = engine.get_problem_from_db(topic_map[st.session_state.selected_topic_order]['name'], st.session_state.selected_level)
        st.session_state.topic_completed = False
        st.rerun()

st.title("🧮 Najlepszy nauczyciel matematyki")

# --- FIX 1: DYNAMIC TOPIC TITLE ---
st.subheader(f"Temat: {topic_map[st.session_state.selected_topic_order]['name']}")

# Fetch initial problem if missing
if 'current_problem' not in st.session_state:
    st.session_state.current_problem = engine.get_problem_from_db(topic_map[st.session_state.selected_topic_order]['name'], st.session_state.selected_level)

problem: dict | None = st.session_state.current_problem

# --- 2. THE MASTERY SCOREBOARD ---
stars_display = "⭐" * st.session_state.streak + "⬛" * (3 - st.session_state.streak)
st.markdown(f"### Postęp do kolejnego poziomu: {stars_display}")

# Default these to False so the engine doesn't crash if the problem fails to load!
submitted = False
admin_solve = False

if problem is None or "error" in problem:
    st.error(f"❌ Nie można załadować Poziomu {st.session_state.selected_level}. Sprawdź plik CSV.")
else:
    st.write("---")
    st.info(f"📍 {problem.get('level_display', 'Level ' + str(st.session_state.selected_level))}") 
    
    # --- FIX 2: ONLY ONE MATH PROBLEM RENDERED ---
    st.header("Zadanie:")
    st.latex(problem['question'].replace("Oblicz: ", "")) 

    # --- FIX 3: THE KEYERROR CRASH FIX ---
    if 'shuffled_options' not in st.session_state or st.session_state.get('last_id') != problem['problem_id']:
        st.session_state.shuffled_options = problem['options']
        st.session_state.last_id = problem['problem_id']
        st.session_state.problem_answered = False 

# --- THE "TRAINING WHEELS" TOGGLE (NOW A FORM) ---
    with st.form("answer_form", border=False):
        if st.session_state.current_input_mode == "radio":
            st.markdown("<style>.stRadio label { padding-bottom: 25px; padding-top: 10px; }</style>", unsafe_allow_html=True)
            
            # --- FIX 4: RAW STRING FIX (format_func makes the radio buttons render beautiful math) ---
            choice = st.radio("Wybierz wynik:", st.session_state.shuffled_options, index=None, format_func=lambda x: f"${x}$")
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
            # Always available for testing!
            admin_solve = st.form_submit_button("🪄 Auto-Solve", disabled=st.session_state.problem_answered)
            
        # --- THE FIX: Re-enable the Enter key for Radio Buttons! ---
        # We only inject this if the problem hasn't been answered yet.
        if not st.session_state.problem_answered:
            if not is_text_mode:
                inject_enter_hack("Sprawdź odpowiedź")
            else:
                # Text inputs natively trigger form submits on Enter, so we disable the hack here to prevent double-submits
                inject_enter_hack("NONE")

# --- 3. CHECK LOGIC & GAMIFICATION ---
if admin_solve or submitted:
    is_correct = False
    is_improper_but_correct = False

    # --- 1. THE AUTO-SOLVE BYPASS ---
    if admin_solve:
        is_correct = True
        st.session_state.problem_answered = True
        
    # --- 2. STANDARD GRADING LOGIC ---
    else:
        if not is_text_mode and not choice:
            st.session_state.feedback_type = "warning"
            st.session_state.feedback_msg = "Najpierw wybierz odpowiedź!"
            st.rerun()
        elif is_text_mode and not user_text:
            st.session_state.feedback_type = "warning"
            st.session_state.feedback_msg = "Wpisz swój wynik w puste pole!"
            st.rerun()
        else:
            if not is_text_mode:
                st.session_state.problem_answered = True 
                if choice == problem['correct']:
                    is_correct = True
                elif choice == problem['trap']:
                    st.session_state.feedback_type = "error"
                    st.session_state.feedback_msg = problem['trap_message']
                else:
                    st.session_state.feedback_type = "warning"
                    st.session_state.feedback_msg = problem['wrong_message']
            else:
                if check_text_answer(problem['correct'], user_text):
                    is_correct = True
                    st.session_state.problem_answered = True 
                
                elif check_text_answer(problem['trap'], user_text):
                    st.session_state.problem_answered = True
                    st.session_state.feedback_type = "error"
                    st.session_state.feedback_msg = problem['trap_message']
                    
                else:
                    student_val = parse_to_fraction(user_text)
                    correct_val = parse_to_fraction(problem['correct'])
                    
                    if student_val is None:
                        st.session_state.problem_answered = False 
                        st.session_state.feedback_type = "warning"
                        st.session_state.feedback_msg = "Niepoprawny zapis. Użyj cyfr i ukośnika (np. 3/4 lub 1 1/2)."
                    
                    elif correct_val is not None and student_val == correct_val:
                        # TOPIC 2 EXCEPTION: Prevent the "simplify" warning if they are in the expansion/simplification topic
                        if st.session_state.selected_topic_order == 2:
                            st.session_state.problem_answered = True 
                            st.session_state.feedback_type = "warning"
                            st.session_state.feedback_msg = "W tym temacie wartość matematyczna to nie wszystko. Musisz zapisać ułamek w dokładnie takiej postaci, o jaką prosi polecenie!"
                        else:
                            is_improper_but_correct = True
                            st.session_state.problem_answered = False 
                            st.session_state.feedback_type = "info"
                            st.session_state.feedback_msg = "Pamiętaj, żeby skrócić ułamki i wyłączyć całości."
                    
                    else:
                        st.session_state.problem_answered = True 
                        st.session_state.feedback_type = "warning"
                        st.session_state.feedback_msg = "Niestety, to nie jest poprawny wynik. Spróbuj przeliczyć to jeszcze raz!"
        
    # --- 3. REWARD & PROGRESSION LOGIC (Runs for BOTH Auto-Solve and Normal) ---
    if is_correct:
        xp_rewards = {1: 5, 2: 10, 3: 20, 4: 35, 5: 60}
        earned_xp = xp_rewards.get(st.session_state.selected_level, 15)
        
        st.session_state.feedback_type = "success"
        st.session_state.feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
        st.session_state.xp += earned_xp
        
        if st.session_state.streak < 3:
            st.session_state.streak += 1
        
        if st.session_state.streak == 3 and st.session_state.selected_level == st.session_state.unlocked_level:
            current_topic_max = topic_map[st.session_state.selected_topic_order]['max_level']
            
            if st.session_state.unlocked_level < current_topic_max:
                st.session_state.unlocked_level += 1
                st.session_state.show_balloons = "level"
                st.session_state.selected_level = st.session_state.unlocked_level
                st.session_state.streak = 0 
            else:
                st.session_state.topic_completed = True
                st.session_state.show_balloons = "topic"
                st.session_state.streak = 0
    
    elif not is_correct and not is_improper_but_correct and st.session_state.streak > 0:
        st.session_state.streak -= 1
    
    st.rerun()

# --- 4. PERSISTENT FEEDBACK DISPLAY ---
if st.session_state.problem_answered or st.session_state.get('feedback_type') in ["info", "warning"]:
    if st.session_state.get('feedback_type') == "success":
        st.success(st.session_state.feedback_msg)
        
        # Handle the two different types of celebrations
        if st.session_state.get('show_balloons') == "level":
            st.balloons()
            st.success(f"🎊 Poziom {st.session_state.unlocked_level} odblokowany! Zostałeś automatycznie przeniesiony na nowy poziom. 🎊")
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
    # --- THE SPEED BUMP ---
    # We disable the Enter key auto-clicker ONLY if they just beat a topic.
    # This forces them to pause, read the victory message, and manually click the button to proceed.
    if not st.session_state.get('topic_completed'):
        inject_enter_hack("Następne zadanie" if not st.session_state.get('topic_completed') else "NONE")

    # Change the button text if they beat the boss
    button_label = "Przejdź do kolejnego tematu ➡️" if st.session_state.get('topic_completed') else "Następne zadanie ➡️"

    if st.button(button_label, key="next_problem_btn"):
        
        # --- EXECUTE TOPIC JUMP ---
        if st.session_state.get('topic_completed'):
            next_topics = [t for t in topic_map.keys() if t > st.session_state.selected_topic_order]
            if next_topics:
                next_topic_id = min(next_topics)
                st.session_state.unlocked_topic_order = next_topic_id
                st.session_state.selected_topic_order = next_topic_id
                st.session_state.unlocked_level = 1
                st.session_state.selected_level = 1
                
            st.session_state.topic_completed = False
            st.session_state.streak = 0
            st.session_state.problem_answered = False
            st.session_state.current_input_mode = "radio"
            st.session_state.current_problem = engine.get_problem_from_db(topic_map[st.session_state.selected_topic_order]['name'], st.session_state.selected_level)
            st.rerun()
            
        # --- NORMAL NEXT PROBLEM LOGIC ---
        else:
            old_question = st.session_state.current_problem['question'] if st.session_state.current_problem else ""
            new_problem = engine.get_problem_from_db(topic_map[st.session_state.selected_topic_order]['name'], st.session_state.selected_level)
            
            if new_problem is None or 'question' not in new_problem:
                st.error("Błąd krytyczny: Nie można załadować bazy zadań z pliku CSV!")
                st.stop() 
            
            while new_problem['question'] == old_question:
                new_problem = engine.get_problem_from_db(topic_map[st.session_state.selected_topic_order]['name'], st.session_state.selected_level)
                if new_problem is None:
                    st.error("Błąd bazy zadań podczas losowania.")
                    st.stop()
            
            st.session_state.current_problem = new_problem
            st.session_state.problem_answered = False
            st.session_state.feedback_type = None 
            
            if st.session_state.streak >= 2 and topic_map[st.session_state.selected_topic_order]['name'] != "Porównywanie ułamków":
                st.session_state.current_input_mode = "text"
            else:
                st.session_state.current_input_mode = "radio"
                
            st.rerun()