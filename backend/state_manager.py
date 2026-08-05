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
from backend.mastery_loop import TurnContext, TurnOutcome, apply_turn
from backend.models import ChapterProgress, GameState
from backend.unlock import first_topic_id


class StateManager:
    """Centralizes all session state mutations for the FastAPI backend."""

    # --- Private helpers ---

    @staticmethod
    def _get_first_topic_id(
        curriculum: dict[int, list[TopicDict]], chapter_id: int | None
    ) -> int:
        """Extract the first topic id for a chapter, with safe fallback."""
        if chapter_id is not None and curriculum.get(chapter_id):
            return first_topic_id(curriculum[chapter_id])
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

    @staticmethod
    def _build_turn_context(
        state: GameState,
        chapter_id: int,
        topic_id: int,
        topics_by_id: dict[int, TopicMeta],
    ) -> TurnContext:
        prog = state.chapter_progress[chapter_id]
        topic_meta = topics_by_id[topic_id]
        next_topic_ids = tuple(
            sorted(int(tid) for tid in topics_by_id if int(tid) > topic_id)
        )
        return TurnContext(
            chapter_id=chapter_id,
            topic_id=topic_id,
            selected_level=state.selected_level,
            current_streak=state.streak,
            flawless_eligible=state.flawless_eligible,
            unlocked_level=prog.unlocked_level,
            topic_max_level=int(topic_meta["max_level"]),
            next_topic_ids=next_topic_ids,
        )

    @staticmethod
    def _apply_turn_outcome(
        state: GameState, chapter_id: int, outcome: TurnOutcome
    ) -> None:
        state.streak = outcome.new_streak
        state.flawless_eligible = outcome.new_flawless_eligible
        state.xp += outcome.xp_earned
        if outcome.feedback_type is not None:
            state.feedback_type = outcome.feedback_type
        if outcome.feedback_msg is not None:
            state.feedback_msg = outcome.feedback_msg
        if outcome.show_celebration:
            state.show_celebration = True
        if outcome.topic_completed:
            state.topic_completed = True
        if outcome.new_selected_level is not None:
            state.selected_level = outcome.new_selected_level

        prog = state.chapter_progress[chapter_id]
        if outcome.new_unlocked_level is not None:
            prog.unlocked_level = outcome.new_unlocked_level
        if outcome.unlock_topic_id is not None:
            prog.unlocked_topic_id = outcome.unlock_topic_id

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

        turn_ctx = cls._build_turn_context(state, chapter_id, topic_id, topics_by_id)
        turn_outcome = apply_turn(eval_result, turn_ctx)
        cls._apply_turn_outcome(state, chapter_id, turn_outcome)

        cls.sync_to_db(state)
        return eval_result
