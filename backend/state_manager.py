import json
import time
import uuid

import backend.config as config
import backend.engine as engine
from backend.core import db
from backend.models import GameState, TopicProgress


class StateManager:
    """Centralizes all session state mutations for the FastAPI backend."""

    @staticmethod
    def _get_first_micro_topic_order(curriculum, macro_topic):
        """Extract the first micro-topic order for a macro topic, with safe fallback."""
        if macro_topic and curriculum.get(macro_topic):
            return curriculum[macro_topic][0]["micro_topic_order"]
        return 1

    @staticmethod
    def _resolve_input_mode(state: GameState, topic_map: dict) -> str:
        """Determine input mode respecting streak threshold and text_mode_disabled."""
        micro_order = state.selected_micro_topic_order
        if micro_order is None:
            return "radio"
        topic_cfg = topic_map.get(int(micro_order), {})
        text_disabled = topic_cfg.get("text_mode_disabled", False)
        if (
            not text_disabled
            and state.streak >= config.STREAK_THRESHOLD_FOR_TEXT_MODE
        ):
            return "text"
        return "radio"

    @staticmethod
    def init_defaults(state: GameState, macro_topics, curriculum) -> None:
        """Initialize session state with defaults. Heals broken saves from old versions."""
        if not state.session_id:
            state.session_id = str(uuid.uuid4())
        if state.xp == 0 and state.streak == 0 and not state.progress:
            state.flawless_eligible = True
            state.max_streak = config.MAX_STREAK
            state.selected_macro = macro_topics[0] if macro_topics else None
            state.selected_micro_topic_order = StateManager._get_first_micro_topic_order(
                curriculum, macro_topics[0] if macro_topics else None
            )
            state.selected_level = 1
            state.problem_answered = False
            state.current_input_mode = "radio"
            state.topic_completed = False
            state.feedback_type = None
            state.feedback_msg = ""
            state.show_celebration = False

        for mt in macro_topics:
            first_order = StateManager._get_first_micro_topic_order(curriculum, mt)
            if mt not in state.progress:
                state.progress[mt] = TopicProgress(
                    unlocked_micro_topic_order=first_order,
                    unlocked_level=1,
                )
            elif state.progress[mt].unlocked_micro_topic_order < first_order:
                state.progress[mt].unlocked_micro_topic_order = first_order
                state.progress[mt].unlocked_level = 1

        curr_macro = state.selected_macro
        first_curr = StateManager._get_first_micro_topic_order(curriculum, curr_macro)
        if (
            state.selected_micro_topic_order is None
            or state.selected_micro_topic_order < first_curr
        ):
            state.selected_micro_topic_order = first_curr

    @staticmethod
    def reset_turn(state: GameState, topic_map: dict | None = None) -> None:
        """Clears the current problem state when navigating or advancing."""
        state.streak = 0
        state.flawless_eligible = True
        state.problem_answered = False
        state.topic_completed = False
        state.feedback_type = None
        state.feedback_msg = ""
        state.current_problem = None
        if topic_map is not None:
            state.current_input_mode = StateManager._resolve_input_mode(
                state, topic_map
            )
        else:
            state.current_input_mode = "radio"

    @staticmethod
    def load_profile(state: GameState, username, macro_topics, curriculum) -> None:
        """Loads user data from DB or initializes a fresh profile."""
        state.username = username
        user_data = db.load_user(username)

        if user_data:
            state.xp = user_data["xp"]
            state.streak = user_data["streak"]
            state.selected_macro = user_data["selected_macro"]
            state.selected_micro_topic_order = user_data["selected_micro_topic_order"]
            state.selected_level = user_data["selected_level"]
            state.progress = user_data["progress"]
            topic_map = engine.build_topic_map(curriculum, state.selected_macro or "")
            StateManager.reset_turn(state, topic_map)
        else:
            StateManager.hard_reset(state, macro_topics, curriculum)

    @staticmethod
    def sync_to_db(state: GameState) -> None:
        """Pushes current session state to the database."""
        if state.username:
            try:
                db.save_user(state.username, state)
            except Exception as e:
                print(f"Error syncing to database for user {state.username}: {e}")
        if state.session_id and state.username:
            try:
                db.save_session(state.session_id, state.username, state)
            except Exception as e:
                print(f"Error saving session {state.session_id}: {e}")

    @staticmethod
    def hard_reset(state: GameState, macro_topics, curriculum) -> None:
        """Wipes all progress and resets to initial state."""
        state.xp = 0
        state.progress = {
            mt: TopicProgress(
                unlocked_micro_topic_order=StateManager._get_first_micro_topic_order(
                    curriculum, mt
                ),
                unlocked_level=1,
            )
            for mt in macro_topics
        }
        state.selected_macro = macro_topics[0] if macro_topics else None
        state.selected_micro_topic_order = StateManager._get_first_micro_topic_order(
            curriculum, macro_topics[0] if macro_topics else None
        )
        state.selected_level = 1
        StateManager.reset_turn(state)
        StateManager.sync_to_db(state)

    @staticmethod
    def navigate_to(
        state: GameState,
        macro=None,
        micro_topic_order=None,
        level=None,
        topic_map: dict | None = None,
    ) -> None:
        """Navigate to a different macro/micro-topic/level, resetting turn and syncing."""
        if macro is not None:
            state.selected_macro = macro
        if micro_topic_order is not None:
            state.selected_micro_topic_order = micro_topic_order
        if level is not None:
            state.selected_level = level
        StateManager.reset_turn(state, topic_map)
        StateManager.sync_to_db(state)

    @staticmethod
    def get_macro_progress(state: GameState, macro_topic, curriculum_map):
        """Calculate macro-topic completion based on unlocked_micro_topic_order."""
        if not macro_topic or macro_topic not in curriculum_map:
            return 0.0, 0, 1

        topics_dict = curriculum_map.get(macro_topic, {})

        if isinstance(topics_dict, list):
            total_micro = len(topics_dict)
            if total_micro == 0:
                return 0.0, 0, 1
            return 0.0, 0, total_micro

        if not isinstance(topics_dict, dict):
            return 0.0, 0, 1

        topic_orders = sorted(
            [order for order in topics_dict.keys() if isinstance(order, int)]
        )
        total_micro = len(topic_orders)

        if total_micro == 0:
            return 0.0, 0, 1

        macro_progress = state.progress.get(macro_topic)
        unlocked_order = (
            macro_progress.unlocked_micro_topic_order if macro_progress else 1
        )

        completed_micro = sum(1 for order in topic_orders if order < unlocked_order)
        completed_micro = max(0, min(completed_micro, total_micro))

        if state.topic_completed:
            completed_micro = total_micro

        percentage = completed_micro / total_micro
        return percentage, completed_micro, total_micro

    @classmethod
    def process_submission(cls, state: GameState, problem, user_input, is_text_mode, topic_map):
        """Process user submission: evaluate, log telemetry, handle rewards and progression."""
        eval_result = engine.evaluate_answer(user_input, problem, is_text_mode)
        is_correct = eval_result.get("is_correct", False)
        state.problem_answered = eval_result.get("lock_answer", False)
        state.feedback_type = eval_result.get("feedback_type", None)
        state.feedback_msg = eval_result.get("feedback_msg", "")
        trap_id_hit = eval_result.get("trap_id")

        if not is_correct or trap_id_hit:
            state.flawless_eligible = False

        time_spent = None
        if state.problem_start_time is not None:
            time_spent = int(time.time() - state.problem_start_time)

        micro_order = int(state.selected_micro_topic_order)
        current_micro_topic = topic_map[micro_order]["name"]

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

        db.log_telemetry(
            session_id=state.session_id,
            username=state.username,
            macro_topic=state.selected_macro,
            micro_topic=current_micro_topic,
            level_number=state.selected_level,
            is_text_mode=is_text_mode,
            is_correct=is_correct,
            user_input=user_input,
            trap_id=trap_id_hit,
            time_spent_seconds=time_spent,
            equation_state=problem_state,
        )

        if is_correct:
            earned_xp = config.XP_REWARDS.get(
                state.selected_level, config.DEFAULT_XP_REWARD
            )

            state.feedback_type = "success"
            state.feedback_msg = (
                f"Brawo! To poprawna odpowiedź. 🎉 (+{earned_xp} XP)"
            )
            state.xp += earned_xp

            if state.streak < config.MAX_STREAK:
                state.streak += 1

            prog = state.progress[state.selected_macro]
            if (
                state.streak == config.STARS_FOR_UNLOCK
                and state.selected_level == prog.unlocked_level
            ):
                current_topic_max = topic_map[micro_order]["max_level"]

                if prog.unlocked_level < current_topic_max:
                    if state.flawless_eligible:
                        flawless_bonus = config.FLAWLESS_LEVEL_BONUS
                        state.xp += flawless_bonus
                        state.feedback_msg += f" ✨ +{flawless_bonus} Flawless Bonus!"

                    prog.unlocked_level += 1
                    state.show_celebration = True
                    state.selected_level = prog.unlocked_level
                    state.streak = 0
                    state.flawless_eligible = True
                else:
                    if state.flawless_eligible:
                        flawless_bonus = config.FLAWLESS_LEVEL_BONUS
                        state.xp += flawless_bonus
                        state.feedback_msg += f" ✨ +{flawless_bonus} Flawless Bonus!"

                    state.topic_completed = True
                    state.show_celebration = True
                    state.streak = 0
                    state.flawless_eligible = True

                    current_order = int(state.selected_micro_topic_order)
                    next_topics = sorted(
                        int(o) for o in topic_map if int(o) > current_order
                    )
                    if next_topics:
                        prog.unlocked_micro_topic_order = next_topics[0]
                        prog.unlocked_level = 1

        elif not is_correct and state.streak > 0:
            if state.feedback_type != "info":
                state.streak -= 1

        state.current_input_mode = cls._resolve_input_mode(state, topic_map)
        cls.sync_to_db(state)
        return eval_result
