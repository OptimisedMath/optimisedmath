import streamlit as st
import engine
import random
import re
import streamlit.components.v1 as components

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

problem = st.session_state.current_problem

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
                
                // 1. CLEAR THE GHOST LISTENER: Remove any old listener from previous questions
                if (doc.submitRadioListener) {
                    doc.removeEventListener('keyup', doc.submitRadioListener, true);
                }
                
                // 2. CREATE A NAMED LISTENER: So we can find it and delete it next time
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

    # --- 3. CHECK LOGIC & GAMIFICATION ---
    if submitted:
        if not is_text_mode and not choice:
            st.warning("Najpierw wybierz odpowiedź!")
        elif is_text_mode and not user_text:
            st.warning("Wpisz swój wynik w puste pole!")
        else:
            is_correct = False
            is_improper_but_correct = False # The "Blue Underline" State
            
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
                # 1. Check for perfect match
                if check_text_answer(problem['correct'], user_text):
                    is_correct = True
                    st.session_state.problem_answered = True 
                
                # 2. Check for correct calculations but improper format (The "Blue Underline")
                elif 'improper' in problem and check_text_answer(problem['improper'], user_text) and problem['correct'] != problem['improper']:
                    is_improper_but_correct = True
                    st.session_state.problem_answered = False # Keeps the form active!
                    st.session_state.feedback_type = "info"
                    st.session_state.feedback_msg = "Obliczenia są świetne! Teraz wyciągnij całości (zamień na liczbę mieszaną)."
                
                # 3. Completely wrong answer
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
    if st.session_state.problem_answered:
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
            # SAFETY CHECK: Ensure current_problem exists before asking for 'question'
            if st.session_state.current_problem and 'question' in st.session_state.current_problem:
                old_question = st.session_state.current_problem['question']
            else:
                old_question = ""
            
            new_problem = engine.get_problem_from_db("Dodawanie", st.session_state.selected_level)
            
            # SAFETY CHECK: Ensure new_problem successfully loaded from the CSV
            if new_problem and 'question' in new_problem:
                while new_problem['question'] == old_question:
                    new_problem = engine.get_problem_from_db("Dodawanie", st.session_state.selected_level)
                
                st.session_state.current_problem = new_problem
                st.session_state.problem_answered = False
                st.session_state.feedback_type = None 
                
                if st.session_state.streak >= 2:
                    st.session_state.current_input_mode = "text"
                else:
                    st.session_state.current_input_mode = "radio"
                    
                st.rerun()
            else:
                st.error("Błąd wczytywania nowego zadania. Upewnij się, że nazwy w pliku CSV są poprawne.")