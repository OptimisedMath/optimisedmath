# Pure Python state management - NO Streamlit imports
# This enables unit testing and framework-agnostic state handling

import uuid
import json
import time
import config
import engine
from core import db


class StateManager:
    """Centralizes all state mutations to prevent race conditions during Streamlit reruns.
    
    All methods accept a `state` dict (or Streamlit session_state proxy) as the first argument.
    This design allows unit testing without Streamlit and enables framework-agnostic code.
    """

    @staticmethod
    def init_defaults(state, macro_topics, curriculum):
        """Initialize session state with defaults. Heals broken saves from old versions."""
        default_state = {
            "session_id": str(uuid.uuid4()),
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

        # Set defaults for any missing keys
        for key, value in default_state.items():
            if key not in state:
                state[key] = value

        # Ensure progress dictionary catches new macro topics AND heals old broken saves
        for mt in macro_topics:
            first_order = curriculum[mt][0]["Topic_Order"] if curriculum[mt] else 1
            if mt not in state["progress"] or state["progress"][mt]["unlocked_order"] < first_order:
                state["progress"][mt] = {
                    "unlocked_order": first_order,
                    "unlocked_level": 1,
                }

        # Heal the selected topic order if it's currently broken (None or < first_order)
        curr_macro = state["selected_macro"]
        first_curr = curriculum[curr_macro][0]["Topic_Order"] if curr_macro and curriculum[curr_macro] else 1
        if state["selected_topic_order"] is None or state["selected_topic_order"] < first_curr:
            state["selected_topic_order"] = first_curr

    @staticmethod
    def reset_turn(state):
        """Clears the current problem state when navigating or advancing."""
        state["streak"] = 0
        state["problem_answered"] = False
        state["topic_completed"] = False
        state["feedback_type"] = None
        state["feedback_msg"] = ""
        state["current_input_mode"] = "radio"
        if "current_problem" in state:
            del state["current_problem"]

    @staticmethod
    def load_profile(state, username, macro_topics, curriculum):
        """Loads user data from DB or initializes a fresh profile."""
        state["username"] = username
        user_data = db.load_user(username)

        if user_data:
            state["xp"] = user_data["xp"]
            state["streak"] = user_data["streak"]
            state["selected_macro"] = user_data["selected_macro"]
            state["selected_topic_order"] = user_data["selected_topic_order"]
            state["selected_level"] = user_data["selected_level"]
            state["progress"] = user_data["progress"]
            StateManager.reset_turn(state)
        else:
            # If it's a new user, reset to level 1 and save immediately
            StateManager.hard_reset(state, macro_topics, curriculum)

    @staticmethod
    def sync_to_db(state):
        """Pushes current session state to the database."""
        if state.get("username"):
            db.save_user(state["username"], state)

    @staticmethod
    def hard_reset(state, macro_topics, curriculum):
        """Wipes all progress and resets to initial state."""
        state["xp"] = 0
        state["progress"] = {
            mt: {"unlocked_order": curriculum[mt][0]["Topic_Order"] if curriculum[mt] else 1, "unlocked_level": 1}
            for mt in macro_topics
        }
        state["selected_macro"] = macro_topics[0] if macro_topics else None
        state["selected_topic_order"] = curriculum[macro_topics[0]][0]["Topic_Order"] if macro_topics and curriculum[macro_topics[0]] else 1
        state["selected_level"] = 1
        StateManager.reset_turn(state)
        StateManager.sync_to_db(state)

    @staticmethod
    def navigate_to(state, macro=None, topic_order=None, level=None):
        """Navigate to a different macro/topic/level, resetting turn and syncing."""
        if macro is not None:
            state["selected_macro"] = macro
        if topic_order is not None:
            state["selected_topic_order"] = topic_order
        if level is not None:
            state["selected_level"] = level
        StateManager.reset_turn(state)
        StateManager.sync_to_db(state)

    @classmethod
    def process_submission(cls, state, problem, user_input, is_text_mode, topic_map):
        """Process user submission: evaluate, log telemetry, handle rewards and progression.
        
        Args:
            state: Session state object (dict or Streamlit session_state proxy)
            problem: Current problem dict from engine
            user_input: User's answer (string or radio choice)
            is_text_mode: Boolean indicating if input was text-based
            topic_map: Mapping of topic orders to topic details
        """
        # Evaluate the answer
        eval_result = engine.evaluate_answer(user_input, problem, is_text_mode)
        is_correct = eval_result.get("is_correct", False)
        state["problem_answered"] = eval_result.get("lock_answer", False)
        state["feedback_type"] = eval_result.get("feedback_type", None)
        state["feedback_msg"] = eval_result.get("feedback_msg", "")
        trap_id_hit = eval_result.get("trap_id")

        # Calculate time spent
        time_spent = None
        if "problem_start_time" in state:
            time_spent = int(time.time() - state["problem_start_time"])
        
        current_micro_topic = topic_map[state["selected_topic_order"]]["name"]

        # Clean equation state for telemetry
        keys_to_remove = [
            "image_html", "messages", "options", "options_map", 
            "level", "level_name", "level_display", "problem_id" 
        ]
        clean_problem_state = {k: v for k, v in problem.items() if k not in keys_to_remove}
        problem_state = json.dumps(clean_problem_state)

        # Log telemetry
        db.log_telemetry(
            session_id=state["session_id"],
            username=state["username"],
            macro_topic=state["selected_macro"],
            micro_topic=current_micro_topic,
            level_number=state["selected_level"],
            is_text_mode=is_text_mode,              
            is_correct=is_correct,
            user_input=user_input,                  
            trap_id=trap_id_hit,
            time_spent_seconds=time_spent,
            equation_state=problem_state 
        )
        
        # Handle gamification & rewards
        if is_correct:
            earned_xp = config.XP_REWARDS.get(state["selected_level"], config.DEFAULT_XP_REWARD)
            
            state["feedback_type"] = "success"
            state["feedback_msg"] = f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
            state["xp"] += earned_xp

            if state["streak"] < config.MAX_STREAK:
                state["streak"] += 1

            prog = state["progress"][state["selected_macro"]]
            if state["streak"] == config.STARS_FOR_UNLOCK and state["selected_level"] == prog["unlocked_level"]:
                current_topic_max = topic_map[state["selected_topic_order"]]["max_level"]

                if prog["unlocked_level"] < current_topic_max:
                    prog["unlocked_level"] += 1
                    state["show_balloons"] = "level"
                    state["selected_level"] = prog["unlocked_level"]
                    state["streak"] = 0
                else:
                    state["topic_completed"] = True
                    state["show_balloons"] = "topic"
                    state["streak"] = 0

        elif not is_correct and state["streak"] > 0:
            if state["feedback_type"] != "info": 
                state["streak"] -= 1

        # Sync to database
        cls.sync_to_db(state)
