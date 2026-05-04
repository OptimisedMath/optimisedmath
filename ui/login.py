import streamlit as st
from state_manager import StateManager


def render_login_gate(macro_topics, curriculum):
    """Renders a clean, main-screen login UI for mobile accessibility."""
    st.markdown("## 🧮 Optymalna nauka matematyki :D")
    
    # Center the login box
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login_form"):
            st.subheader("Zaloguj się")
            username_input = st.text_input("Twoje imię:", placeholder="np. Janek")
            submit = st.form_submit_button("Rozpocznij naukę", use_container_width=True)
            
            if submit:
                if username_input.strip():
                    # Load from SQLite
                    StateManager.load_profile(st.session_state, username_input.strip(), macro_topics, curriculum)
                    st.rerun()
                else:
                    st.error("Proszę podać imię!")
