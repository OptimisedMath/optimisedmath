import streamlit as st
from state_manager import StateManager


def render_sidebar(state, macro_topics, curriculum, topic_map, admin_mode):
    """Renders the sidebar with navigation, profile controls, and topic/level selection.
    
    Args:
        state: Session state object (not st.session_state directly)
        macro_topics: List of available macro topics
        curriculum: Curriculum data dictionary
        topic_map: Mapping of topic orders to topic details
        admin_mode: Initial admin mode toggle value
    """
    with st.sidebar:
        st.write(f"Witaj, **{state.username}**!")

        st.markdown("---")
        st.title("🏆 Twój Profil")
        st.metric(label="Punkty Doświadczenia (XP)", value=state.xp)
        admin_mode_toggle = st.toggle("🛠️ Tryb Admina (Odblokuj wszystko)", value=admin_mode)

        if st.button("🔄 Zresetuj Postęp"):
            StateManager.hard_reset(state, macro_topics, curriculum)
            st.rerun()

        st.markdown("---")
        st.title("⚙️ Ustawienia")

        # Macro Topic Selector
        new_macro = st.selectbox("Wybierz Dział:", macro_topics, index=macro_topics.index(state.selected_macro))
        if new_macro != state.selected_macro:
            prog = state.progress[new_macro]
            StateManager.navigate_to(state, macro=new_macro, topic_order=prog["unlocked_order"], level=prog["unlocked_level"])
            st.rerun()

        # Micro Topic Selector
        prog = state.progress[state.selected_macro]
        first_key = list(topic_map.keys())[0] if topic_map else 1
        unlocked_order = prog.get("unlocked_order", first_key)

        available_orders = list(topic_map.keys()) if admin_mode_toggle else [order for order in topic_map.keys() if order <= unlocked_order]
        if not available_orders: available_orders = [first_key]

        def format_topic(order):
            visual_number = list(topic_map.keys()).index(order) + 1 if order in topic_map else 1
            topic_name = topic_map.get(order, {"name": "Nieznany"})["name"]
            return f"{visual_number}. {topic_name}"

        safe_index = available_orders.index(state.selected_topic_order) if state.selected_topic_order in available_orders else len(available_orders) - 1
        new_topic_order = st.selectbox("Wybierz Temat:", options=available_orders, format_func=format_topic, index=safe_index)

        if new_topic_order and new_topic_order != state.selected_topic_order:
            StateManager.navigate_to(state, topic_order=new_topic_order, level=1)
            st.rerun()

        # Level Selector
        current_topic_max_level = topic_map.get(state.selected_topic_order, {"max_level": 1}).get("max_level", 1)
        unlocked_lvl = prog.get("unlocked_level", 1)

        allowed_max_level = current_topic_max_level if admin_mode_toggle else (current_topic_max_level if state.selected_topic_order < unlocked_order else min(unlocked_lvl, current_topic_max_level))

        if allowed_max_level == 1 and current_topic_max_level > 1:
            st.info(f"🔒 Aktywny: Poziom 1\n\n*(Zdobądź 3 gwiazdki, aby odblokować kolejne poziomy!)*")
            new_level = 1
        elif current_topic_max_level == 1:
            st.info("Ten temat ma tylko jeden poziom.")
            new_level = 1
        else:
            new_level = st.slider("Wybierz Poziom:", min_value=1, max_value=allowed_max_level, value=min(state.selected_level, allowed_max_level))

        if new_level != state.selected_level:
            StateManager.navigate_to(state, level=new_level)
            st.rerun()
