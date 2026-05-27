# Pure Python state management - NO Streamlit imports
# This enables unit testing and framework-agnostic state handling

import uuid
import json
import time
import backend.config as config
import backend.engine as engine
from backend.core import db


class StateManager:
    """Centralizes all state mutations to prevent race conditions during Streamlit reruns.

    All methods accept a `state` dict (or Streamlit session_state proxy) as the first argument.
    This design allows unit testing without Streamlit and enables framework-agnostic code.
    """

    @staticmethod
    def _get_first_topic_order(curriculum, macro_topic):
        """Extract the first topic order for a given macro topic, with safe fallback."""
        if macro_topic and curriculum.get(macro_topic):
            return curriculum[macro_topic][0]["Topic_Order"]
        return 1

    @staticmethod
    def init_defaults(state, macro_topics, curriculum):
        """Initialize session state with defaults. Heals broken saves from old versions."""
        default_state = {
            "session_id": str(uuid.uuid4()),
            "xp": 0,
            "streak": 0,
            "flawless_eligible": True,
            "max_streak": config.MAX_STREAK,
            "selected_macro": macro_topics[0] if macro_topics else None,
            "selected_topic_order": StateManager._get_first_topic_order(
                curriculum, macro_topics[0] if macro_topics else None
            ),
            "selected_level": 1,
            "problem_answered": False,
            "current_input_mode": "radio",
            "topic_completed": False,
            "progress": {},
            "feedback_type": None,
            "feedback_msg": "",
            "show_balloons": False,
        }

        # Set defaults for any missing keys
        for key, value in default_state.items():
            if key not in state:
                state[key] = value

        # Ensure progress dictionary catches new macro topics AND heals old broken saves
        for mt in macro_topics:
            first_order = StateManager._get_first_topic_order(curriculum, mt)
            if (
                mt not in state["progress"]
                or state["progress"][mt]["unlocked_order"] < first_order
            ):
                state["progress"][mt] = {
                    "unlocked_order": first_order,
                    "unlocked_level": 1,
                }

        # Heal the selected topic order if it's currently broken (None or < first_order)
        curr_macro = state["selected_macro"]
        first_curr = StateManager._get_first_topic_order(curriculum, curr_macro)
        if (
            state["selected_topic_order"] is None
            or state["selected_topic_order"] < first_curr
        ):
            state["selected_topic_order"] = first_curr

    @staticmethod
    def reset_turn(state):
        """Clears the current problem state when navigating or advancing."""
        state["streak"] = 0
        state["flawless_eligible"] = (
            True  # Reset flawless eligibility when streak hits 0
        )
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
            try:
                db.save_user(state["username"], state)
            except Exception as e:
                print(
                    f"Error syncing to database for user {state.get('username')}: {e}"
                )
        if state.get("session_id") and state.get("username"):
            try:
                db.save_session(state["session_id"], state["username"], state)
            except Exception as e:
                print(f"Error saving session {state.get('session_id')}: {e}")

    @staticmethod
    def hard_reset(state, macro_topics, curriculum):
        """Wipes all progress and resets to initial state."""
        state["xp"] = 0
        state["progress"] = {
            mt: {
                "unlocked_order": StateManager._get_first_topic_order(curriculum, mt),
                "unlocked_level": 1,
            }
            for mt in macro_topics
        }
        state["selected_macro"] = macro_topics[0] if macro_topics else None
        state["selected_topic_order"] = StateManager._get_first_topic_order(
            curriculum, macro_topics[0] if macro_topics else None
        )
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

    @staticmethod
    def get_macro_progress(state, macro_topic, curriculum_map):
        """Calculate the completion progress of a macro topic based on unlocked_order.

        Counts completed micro-topics: a micro-topic is completed if its order < unlocked_order.

        Args:
            state: Session state object containing progress dictionary
            macro_topic: The macro topic to check progress for
            curriculum_map: Mapping of macro_topic -> {order: {topic_info}} (order-keyed dict)

        Returns:
            tuple: (completion_percentage (0.0-1.0), completed_micro, total_micro)
            Returns (0.0, 0, 1) if macro_topic not found or no micro-topics exist
        """
        # Handle edge cases
        if not macro_topic or macro_topic not in curriculum_map:
            return 0.0, 0, 1

        topics_dict = curriculum_map.get(macro_topic, {})

        # Handle legacy list format gracefully
        if isinstance(topics_dict, list):
            total_micro = len(topics_dict)
            if total_micro == 0:
                return 0.0, 0, 1
            # Fall back to simple counting if structure is unexpected
            return 0.0, 0, total_micro

        # Extract topic orders from the dictionary
        if not isinstance(topics_dict, dict):
            return 0.0, 0, 1

        topic_orders = sorted(
            [order for order in topics_dict.keys() if isinstance(order, int)]
        )
        total_micro = len(topic_orders)

        if total_micro == 0:
            return 0.0, 0, 1

        # Get unlocked_order from progress dictionary
        progress = state.get("progress", {})
        macro_progress = progress.get(macro_topic, {})
        unlocked_order = macro_progress.get("unlocked_order", 1)

        # Count completed micro-topics: those with order < unlocked_order
        completed_micro = sum(1 for order in topic_orders if order < unlocked_order)

        # Ensure bounds safety
        completed_micro = max(0, min(completed_micro, total_micro))

        # If topic is fully completed, override to total_micro
        if state.get("topic_completed") == True:
            completed_micro = total_micro

        # Calculate percentage
        percentage = completed_micro / total_micro

        return percentage, completed_micro, total_micro

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

        # Mark flawless as False if answer is incorrect or trap is hit
        if not is_correct or trap_id_hit:
            state["flawless_eligible"] = False

        # Calculate time spent
        time_spent = None
        if "problem_start_time" in state:
            time_spent = int(time.time() - state["problem_start_time"])

        current_micro_topic = topic_map[state["selected_topic_order"]]["name"]

        # Clean equation state for telemetry
        keys_to_remove = [
            "image_html",
            "messages",
            "options",
            "options_map",
            "level",
            "level_name",
            "level_display",
            "problem_id",
        ]
        clean_problem_state = {
            k: v for k, v in problem.items() if k not in keys_to_remove
        }
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
            equation_state=problem_state,
        )

        # Handle gamification & rewards
        if is_correct:
            earned_xp = config.XP_REWARDS.get(
                state["selected_level"], config.DEFAULT_XP_REWARD
            )

            state["feedback_type"] = "success"
            state["feedback_msg"] = (
                f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
            )
            state["xp"] += earned_xp

            if state["streak"] < config.MAX_STREAK:
                state["streak"] += 1

            prog = state["progress"][state["selected_macro"]]
            if (
                state["streak"] == config.STARS_FOR_UNLOCK
                and state["selected_level"] == prog["unlocked_level"]
            ):
                current_topic_max = topic_map[state["selected_topic_order"]][
                    "max_level"
                ]

                if prog["unlocked_level"] < current_topic_max:
                    # Check for flawless bonus when leveling up
                    if state.get("flawless_eligible", False):
                        flawless_bonus = config.FLAWLESS_LEVEL_BONUS
                        state["xp"] += flawless_bonus
                        state[
                            "feedback_msg"
                        ] += f" ✨ +{flawless_bonus} Flawless Bonus!"

                    prog["unlocked_level"] += 1
                    state["show_balloons"] = True
                    state["selected_level"] = prog["unlocked_level"]
                    state["streak"] = 0
                    state["flawless_eligible"] = True  # Reset for new level
                else:
                    # Check for flawless bonus when completing topic
                    if state.get("flawless_eligible", False):
                        flawless_bonus = config.FLAWLESS_LEVEL_BONUS
                        state["xp"] += flawless_bonus
                        state[
                            "feedback_msg"
                        ] += f" ✨ +{flawless_bonus} Flawless Bonus!"

                    state["topic_completed"] = True
                    state["show_balloons"] = True
                    state["streak"] = 0
                    state["flawless_eligible"] = True

                    # Unlock the next micro-topic so the frontend can navigate to it
                    current_order = int(state["selected_topic_order"])
                    next_topics = sorted(
                        int(o) for o in topic_map if int(o) > current_order
                    )
                    if next_topics:
                        prog["unlocked_order"] = next_topics[0]
                        prog["unlocked_level"] = 1

        elif not is_correct and state["streak"] > 0:
            if state["feedback_type"] != "info":
                state["streak"] -= 1

        # Update input mode based on current streak (per Structure.md: streak 0 → radio, streak ≥1 → text)
        state["current_input_mode"] = "text" if state["streak"] >= 1 else "radio"

        # Sync to database
        cls.sync_to_db(state)
