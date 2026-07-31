"""Session state mutations for the FastAPI backend."""

import json
import time
import uuid

import backend.config as config
import backend.engine as engine
from backend.core import db
from backend.core.utils import ProblemDict
from backend.curriculum_loader import (
    TopicDict,
    TopicMeta,
    get_chapter_name_by_id,
    get_topic_name,
    get_topics_by_id,
)
from backend.engine import EvalResult
from backend.models import ChapterProgress, GameState


class StateManager:
    """Centralizes all session state mutations for the FastAPI backend."""

    # --- Private helpers ---

    @staticmethod
    def _get_first_topic_id(
        curriculum: dict[int, list[TopicDict]], chapter_id: int | None
    ) -> int:
        """Extract the first topic id for a chapter, with safe fallback."""
        if chapter_id is not None and curriculum.get(chapter_id):
            return curriculum[chapter_id][0]["topic_id"]
        return 1

    @staticmethod
    def _resolve_input_mode(
        state: GameState, topics_by_id: dict[int, TopicMeta]
    ) -> str:
        """Determine input mode respecting streak threshold and text_mode_disabled."""
        topic_id = state.selected_topic_id
        if topic_id is None:
            return "radio"
        topic_cfg = topics_by_id.get(int(topic_id), {})
        text_disabled = topic_cfg.get("text_mode_disabled", False)
        if (
            not text_disabled
            and state.streak >= config.STREAK_THRESHOLD_FOR_TEXT_MODE
        ):
            return "text"
        return "radio"

    # --- Session initialization ---

    @staticmethod
    def init_defaults(
        state: GameState,
        chapter_ids: list[int],
        curriculum: dict[int, list[TopicDict]],
    ) -> None:
        """Initialize session state with defaults. Heals broken saves from old versions."""
        if not state.session_id:
            state.session_id = str(uuid.uuid4())
        if state.xp == 0 and state.streak == 0 and not state.chapter_progress:
            state.flawless_eligible = True
            state.max_streak = config.MAX_STREAK
            state.selected_chapter_id = chapter_ids[0] if chapter_ids else None
            state.selected_topic_id = StateManager._get_first_topic_id(
                curriculum, chapter_ids[0] if chapter_ids else None
            )
            state.selected_level = 1
            state.problem_answered = False
            state.current_input_mode = "radio"
            state.topic_completed = False
            state.feedback_type = None
            state.feedback_msg = ""
            state.show_celebration = False

        for chapter_id in chapter_ids:
            first_topic_id = StateManager._get_first_topic_id(curriculum, chapter_id)
            if chapter_id not in state.chapter_progress:
                state.chapter_progress[chapter_id] = ChapterProgress(
                    unlocked_topic_id=first_topic_id,
                    unlocked_level=1,
                )
            elif state.chapter_progress[chapter_id].unlocked_topic_id < first_topic_id:
                state.chapter_progress[chapter_id].unlocked_topic_id = first_topic_id
                state.chapter_progress[chapter_id].unlocked_level = 1

        curr_chapter_id = state.selected_chapter_id
        first_curr_topic_id = StateManager._get_first_topic_id(curriculum, curr_chapter_id)
        if (
            state.selected_topic_id is None
            or state.selected_topic_id < first_curr_topic_id
        ):
            state.selected_topic_id = first_curr_topic_id

    # --- Turn lifecycle ---

    @staticmethod
    def reset_turn(
        state: GameState, topics_by_id: dict[int, TopicMeta] | None = None
    ) -> None:
        """Clears the current problem state when navigating or advancing."""
        state.streak = 0
        state.flawless_eligible = True
        state.problem_answered = False
        state.topic_completed = False
        state.feedback_type = None
        state.feedback_msg = ""
        state.current_problem = None
        if topics_by_id is not None:
            state.current_input_mode = StateManager._resolve_input_mode(
                state, topics_by_id
            )
        else:
            state.current_input_mode = "radio"

    # --- Persistence ---

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

    # --- Profile & navigation ---

    @staticmethod
    def load_profile(
        state: GameState,
        username: str,
        chapter_ids: list[int],
        curriculum: dict[int, list[TopicDict]],
    ) -> None:
        """Loads user data from DB or initializes a fresh profile."""
        state.username = username
        user_data = db.load_user(username)

        if user_data:
            state.xp = user_data["xp"]
            state.streak = user_data["streak"]
            state.selected_chapter_id = user_data["selected_chapter_id"]
            state.selected_topic_id = user_data["selected_topic_id"]
            state.selected_level = user_data["selected_level"]
            state.chapter_progress = user_data["chapter_progress"]
            topics_by_id = get_topics_by_id(state.selected_chapter_id or 0)
            StateManager.reset_turn(state, topics_by_id)
        else:
            StateManager.hard_reset(state, chapter_ids, curriculum)

    @staticmethod
    def hard_reset(
        state: GameState,
        chapter_ids: list[int],
        curriculum: dict[int, list[TopicDict]],
    ) -> None:
        """Wipes all progress and resets to initial state."""
        state.xp = 0
        state.chapter_progress = {
            chapter_id: ChapterProgress(
                unlocked_topic_id=StateManager._get_first_topic_id(curriculum, chapter_id),
                unlocked_level=1,
            )
            for chapter_id in chapter_ids
        }
        state.selected_chapter_id = chapter_ids[0] if chapter_ids else None
        state.selected_topic_id = StateManager._get_first_topic_id(
            curriculum, chapter_ids[0] if chapter_ids else None
        )
        state.selected_level = 1
        StateManager.reset_turn(state)
        StateManager.sync_to_db(state)

    @staticmethod
    def navigate_to(
        state: GameState,
        chapter_id: int | None = None,
        topic_id: int | None = None,
        level: int | None = None,
        topics_by_id: dict[int, TopicMeta] | None = None,
    ) -> None:
        """Navigate to a different chapter/topic/level, resetting turn and syncing."""
        if chapter_id is not None:
            state.selected_chapter_id = chapter_id
        if topic_id is not None:
            state.selected_topic_id = topic_id
        if level is not None:
            state.selected_level = level
        StateManager.reset_turn(state, topics_by_id)
        StateManager.sync_to_db(state)

    # --- Submission processing ---

    @classmethod
    def process_submission(
        cls,
        state: GameState,
        problem: ProblemDict,
        user_input: str,
        is_text_mode: bool,
        topics_by_id: dict[int, TopicMeta],
    ) -> EvalResult:
        """Process user submission: evaluate, log telemetry, handle rewards and progression."""
        eval_result = engine.evaluate_answer(user_input, problem, is_text_mode)
        is_correct = eval_result.get("is_correct", False)
        state.problem_answered = eval_result.get("lock_answer", False)
        state.feedback_type = eval_result.get("feedback_type", None)
        state.feedback_msg = eval_result.get("feedback_msg", "")
        trap_id_hit = eval_result.get("trap_id")

        if not is_correct and state.feedback_type != "info":
            state.flawless_eligible = False

        username = state.username
        chapter_id = state.selected_chapter_id
        topic_id = state.selected_topic_id
        if username is None or chapter_id is None or topic_id is None:
            raise RuntimeError("Session missing required context for submission")

        time_spent = None
        if state.problem_start_time is not None:
            time_spent = int(time.time() - state.problem_start_time)

        current_topic_name = topics_by_id[topic_id]["name"]
        chapter_name = get_chapter_name_by_id(chapter_id) or str(chapter_id)

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
            username=username,
            chapter_name=chapter_name,
            topic_name=current_topic_name,
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

            prog = state.chapter_progress[chapter_id]
            if (
                state.streak == config.STARS_FOR_UNLOCK
                and state.selected_level == prog.unlocked_level
            ):
                current_topic_max = topics_by_id[topic_id]["max_level"]

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

                    current_topic_id = topic_id
                    next_topic_ids = sorted(
                        int(tid) for tid in topics_by_id if int(tid) > current_topic_id
                    )
                    if next_topic_ids:
                        prog.unlocked_topic_id = next_topic_ids[0]
                        prog.unlocked_level = 1

        elif not is_correct and state.streak > 0:
            if state.feedback_type != "info":
                state.streak -= 1

        cls.sync_to_db(state)
        return eval_result
