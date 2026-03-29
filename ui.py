import streamlit as st
import engine
import random
import re
import streamlit.components.v1 as components
from fractions import Fraction

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
if 'current_input_mode' not in st.session_state:
    st.session_state.current_input_mode = "radio" # NEW: Default to multiple choice

# --- SIDEBAR: Player Profile & Level Selector ---
with st.sidebar:
    st.title("🏆 Twój Profil")
    st.metric(label="Punkty Doświadczenia (XP)", value=st.session_state.xp)
    
    # [RESET BUTTON CODE HERE...]
    if st.button("🔄 Zresetuj Postęp"):
        st.session_state.xp = 0
        st.session_state.streak = 0
        st.session_state.unlocked_level = 1
        st.session_state.selected_level = 1
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio" # NEW: Reset format
        st.session_state.current_problem = engine.get_problem_from_db("Dodawanie", 1)
        st.rerun()

    st.markdown("---")
    st.title("Ustawienia")
    
    if st.session_state.unlocked_level == 1:
        st.info("🔒 Aktywny: Poziom 1\n\n*(Zdobądź 3 gwiazdki, aby odblokować wybór poziomów!)*")
        new_level = 1 
    else:
        new_level = st.slider("Wybierz Poziom:", min_value=1, max_value=st.session_state.unlocked_level, value=st.session_state.selected_level)
    
    if new_level != st.session_state.selected_level:
        st.session_state.selected_level = new_level
        st.session_state.streak = 0 
        st.session_state.problem_answered = False
        st.session_state.current_input_mode = "radio" # NEW: Reset format when changing levels manually
        st.session_state.current_problem = engine.get_problem_from_db("Dodawanie", st.session_state.selected_level)
        st.rerun()

st.title("🧮 Najlepszy nauczyciel matematyki")
st.subheader("Temat: Dodawanie Ułamków")

# Fetch initial problem if missing
if 'current_problem' not in st.session_state:
    st.session_state.current_problem = engine.get_problem_from_db("Dodawanie", st.session_state.selected_level)

problem: dict | None = st.session_state.current_problem

# --- 2. THE MASTERY SCOREBOARD ---
stars_display = "⭐" * st.session_state.streak + "⬛" * (3 - st.session_state.streak)
st.markdown(f"### Postęp do kolejnego poziomu: {stars_display}")

if problem is None or "error" in problem:
    st.error(f"❌ Nie można załadować Poziomu {st.session_state.selected_level}. Sprawdź plik CSV.")
else:
    st.write("---")
    st.info(f"📍 {problem.get('level_display', 'Level ' + str(st.session_state.selected_level))}") 
    st.header("Zadanie:")
    st.latex(problem['question'].replace("Oblicz: ", "")) 

    raw_options = [problem['correct'], problem['trap'], problem['wrong']]
    if 'shuffled_options' not in st.session_state or st.session_state.get('last_id') != problem['problem_id']:
        shuffled = raw_options.copy()
        random.shuffle(shuffled)
        st.session_state.shuffled_options = shuffled
        st.session_state.last_id = problem['problem_id']
        st.session_state.problem_answered = False 

# --- THE "TRAINING WHEELS" TOGGLE (NOW A FORM) ---
    # We use border=False so it stays visually clean and invisible to the user
    with st.form("answer_form", border=False):
        if st.session_state.current_input_mode == "radio":
            st.markdown("<style>.stRadio label { padding-bottom: 25px; padding-top: 10px; }</style>", unsafe_allow_html=True)
            choice = st.radio("Wybierz wynik:", st.session_state.shuffled_options, index=None)
            is_text_mode = False
        else:
            st.info("Wpisz wynik samodzielnie bez podpowiedzi.")
            st.markdown("*(Format wprowadzania: wpisz **3/4**, a dla liczb mieszanych **1 1/2**)*")
            user_text = st.text_input("Twoja odpowiedź:", key=f"text_input_{st.session_state.last_id}")
            is_text_mode = True
        
        # The form natively binds the "Enter" key to this specific button!
        submitted = st.form_submit_button("Sprawdź odpowiedź", disabled=st.session_state.problem_answered)
        
# --- THE AGGRESSIVE "ENTER KEY" JAVASCRIPT HACK ---
        if st.session_state.current_input_mode == "radio":
            components.html(
                """
                <script>
                const doc = window.parent.document;
                
                // 1. CLEAR THE GHOST LISTENER
                if (doc.submitRadioListener) {
                    doc.removeEventListener('keyup', doc.submitRadioListener, true);
                }
                
                // 2. CREATE A NAMED LISTENER
                doc.submitRadioListener = function(e) {
                    if (e.key === 'Enter') {
                        const allButtons = Array.from(doc.querySelectorAll('button'));
                        const submitBtn = allButtons.find(b => b.innerText.includes('Sprawdź odpowiedź'));
                        
                        if (submitBtn) {
                            submitBtn.click();
                        }
                    }
                };
                
                // 3. ATTACH IT
                doc.addEventListener('keyup', doc.submitRadioListener, true);
                </script>
                """,
                height=0, width=0
            )
        else:
            # TEXT MODE: The text box natively submits on Enter. 
            # We MUST delete the radio listener so it doesn't double-click the button!
            components.html(
                """
                <script>
                const doc = window.parent.document;
                if (doc.submitRadioListener) {
                    doc.removeEventListener('keyup', doc.submitRadioListener, true);
                }
                </script>
                """,
                height=0, width=0
            )

# --- STRING MATCHER HELPER FUNCTION ---
    def check_text_answer(latex_answer, student_input):
        engine_text = latex_answer.replace("$\\displaystyle ", "").replace("$", "")
        engine_text = engine_text.replace("\\frac{", " ").replace("}{", "/").replace("}", "")
        engine_text = " ".join(engine_text.split()) 
        
        # AGGRESSIVE SANITIZATION: Replace EVERYTHING that isn't a digit or a slash with a space
        # This instantly fixes hyphens, underscores, and Polish characters (e.g., "1 cała 1/2" -> "1 1/2")
        student_clean = re.sub(r'[^\d/]', ' ', student_input) 
        
        # Remove accidental spaces around the slash
        student_clean = student_clean.replace(" / ", "/").replace("/ ", "/").replace(" /", "/")
        student_clean = " ".join(student_clean.split())
        
        return engine_text == student_clean
    
    def parse_to_fraction(latex_or_text):
        """Converts latex strings like '1\\frac{1}{2}' or crazy user inputs like '44/32' into pure Math."""
        text = latex_or_text.replace("$\\displaystyle ", "").replace("$", "")
        text = text.replace("\\frac{", " ").replace("}{", "/").replace("}", "")
        
        clean = re.sub(r'[^\d/]', ' ', text)
        clean = clean.replace(" / ", "/").replace("/ ", "/").replace(" /", "/")
        clean = " ".join(clean.split())
        
        try:
            if ' ' in clean: # Mixed number e.g., "1 3/8"
                parts = clean.split()
                if len(parts) == 2:
                    return int(parts[0]) + Fraction(parts[1])
            else: # Fraction e.g., "44/32" or whole number "2"
                return Fraction(clean)
        except:
            return None

    # --- 3. CHECK LOGIC & GAMIFICATION ---
    if submitted:
        if not is_text_mode and not choice:
            st.session_state.feedback_type = "warning"
            st.session_state.feedback_msg = "Najpierw wybierz odpowiedź!"
            st.rerun()
        elif is_text_mode and not user_text:
            st.session_state.feedback_type = "warning"
            st.session_state.feedback_msg = "Wpisz swój wynik w puste pole!"
            st.rerun()
        else:
            is_correct = False
            is_improper_but_correct = False
            
            # --- Grading Mode Split ---
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
                # 1. PERFECT MATCH: Check if they typed the fully simplified, perfect string
                if check_text_answer(problem['correct'], user_text):
                    is_correct = True
                    st.session_state.problem_answered = True 
                
                else:
                    # Extract the pure mathematical DNA
                    student_val = parse_to_fraction(user_text)
                    correct_val = parse_to_fraction(problem['correct'])
                    
                    # 2. TYPO ARMOR: The engine couldn't understand the text at all
                    if student_val is None:
                        st.session_state.problem_answered = False 
                        st.session_state.feedback_type = "warning"
                        st.session_state.feedback_msg = "Niepoprawny zapis. Użyj cyfr i ukośnika (np. 3/4 lub 1 1/2)."
                    
                    # 3. THE BLUE UNDERLINE: The math matches perfectly, but the string didn't!
                    elif correct_val is not None and student_val == correct_val:
                        is_improper_but_correct = True
                        st.session_state.problem_answered = False 
                        st.session_state.feedback_type = "info"
                        st.session_state.feedback_msg = "Pamiętaj, żeby skrócić ułamki i wyłączyć całości."
                    
                    # 4. COMPLETELY WRONG
                    else:
                        st.session_state.problem_answered = True 
                        st.session_state.feedback_type = "warning"
                        st.session_state.feedback_msg = "Niestety, to nie jest poprawny wynik. Spróbuj przeliczyć to jeszcze raz!"
            
            # --- Reward & Progression Logic ---
            if is_correct:
                xp_rewards = {1: 5, 2: 10, 3: 20, 4: 35, 5: 60}
                earned_xp = xp_rewards.get(st.session_state.selected_level, 15)
                
                st.session_state.feedback_type = "success"
                st.session_state.feedback_msg = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
                st.session_state.xp += earned_xp
                
                if st.session_state.streak < 3:
                    st.session_state.streak += 1
                
                if st.session_state.streak == 3 and st.session_state.selected_level == st.session_state.unlocked_level:
                    if st.session_state.unlocked_level < 5:
                        st.session_state.unlocked_level += 1
                        st.session_state.show_balloons = True
                        st.session_state.selected_level = st.session_state.unlocked_level
                        st.session_state.streak = 0 
            
            # Penalize only if it is entirely wrong (not if it just needs regrouping)
            elif not is_correct and not is_improper_but_correct and st.session_state.streak > 0:
                st.session_state.streak -= 1
            
            st.rerun()

# --- 4. PERSISTENT FEEDBACK DISPLAY ---
    # Show feedback if the problem is fully answered, OR if they triggered an "info" or "warning" ticket
    if st.session_state.problem_answered or st.session_state.get('feedback_type') in ["info", "warning"]:
        if st.session_state.get('feedback_type') == "success":
            st.success(st.session_state.feedback_msg)
            if st.session_state.get('show_balloons'):
                st.balloons()
                st.success(f"🎊 Poziom {st.session_state.unlocked_level} odblokowany! Zostałeś automatycznie przeniesiony na nowy poziom. 🎊")
                st.session_state.show_balloons = False
        elif st.session_state.get('feedback_type') == "error":
            st.error(st.session_state.feedback_msg)
        elif st.session_state.get('feedback_type') == "warning":
            st.warning(st.session_state.feedback_msg)
        elif st.session_state.get('feedback_type') == "info":
            st.info(st.session_state.feedback_msg) # The blue underline box!

    # We indent the Next Problem button so it ONLY appears when the problem is fully finished
    if st.session_state.problem_answered:
        # --- THE "ENTER KEY" HACK FOR NEXT PROBLEM ---
        components.html(
            """
            <script>
            const doc = window.parent.document;
            
            // We clear any old listeners first so they don't pile up when the page refreshes
            doc.removeEventListener('keyup', doc.nextProblemListener, true);
            
            doc.nextProblemListener = function(e) {
                if (e.key === 'Enter') {
                    const allButtons = Array.from(doc.querySelectorAll('button'));
                    const nextBtn = allButtons.find(b => b.innerText.includes('Następne zadanie'));
                    
                    if (nextBtn) {
                        nextBtn.click();
                    }
                }
            };
            
            doc.addEventListener('keyup', doc.nextProblemListener, true);
            </script>
            """,
            height=0, width=0
        )

        if st.button("Następne zadanie ➡️", key="next_problem_btn"):
            
            old_question = st.session_state.current_problem['question'] if st.session_state.current_problem else ""
            
            # Let Python naturally infer the type here
            new_problem = engine.get_problem_from_db("Dodawanie", st.session_state.selected_level)
            
            # --- THE GUARD CLAUSE (The Bouncer) ---
            if new_problem is None or 'question' not in new_problem:
                st.error("Błąd krytyczny: Nie można załadować bazy zadań z pliku CSV!")
                st.stop() # Halts the script gracefully here. No crash!
            
            # --- SAFE ZONE ---
            # The linter now knows 100% that new_problem is a valid dictionary.
            while new_problem['question'] == old_question:
                new_problem = engine.get_problem_from_db("Dodawanie", st.session_state.selected_level)
                if new_problem is None:
                    st.error("Błąd bazy zadań podczas losowania.")
                    st.stop()
            
            st.session_state.current_problem = new_problem
            st.session_state.problem_answered = False
            st.session_state.feedback_type = None 
            
            if st.session_state.streak >= 2:
                st.session_state.current_input_mode = "text"
            else:
                st.session_state.current_input_mode = "radio"
                
            st.rerun()