"""Session state mutations for the FastAPI backend."""

import uuid

import backend.config as config
from backend.answer_grading import EvalResult, evaluate_answer
from backend.core import db
from backend.core.utils import ProblemDict
from backend.curriculum_loader import (
    TopicDict,
    TopicMeta,
    get_topics_by_id,
)
from backend.play_mode import PlayMode, resolve_play_mode
import backend.submission_play_mode as submission_play_mode
import backend.submission_telemetry as submission_telemetry
from backend.models import ChapterFrontier, SessionState
from backend.unlock import first_topic_id


def _get_first_topic_id(
    curriculum: dict[int, list[TopicDict]], chapter_id: int | None
) -> int:
    """Extract the first topic id for a chapter, with safe fallback."""
    if chapter_id is not None and curriculum.get(chapter_id):
        return first_topic_id(curriculum[chapter_id])
    return 1


def resolve_input_mode(
    state: SessionState, topics_by_id: dict[int, TopicMeta]
) -> str:
    """Determine input mode respecting streak threshold and radio-only topics."""
    topic_id = state.selected_topic_id
    if topic_id is None:
        return "radio"
    topic_cfg = topics_by_id.get(int(topic_id), {})
    radio_only = topic_cfg.get("radio_only", False)
    if (
        not radio_only
        and state.streak >= config.STREAK_THRESHOLD_FOR_INPUT_MODE
    ):
        return "input"
    return "radio"


def init_defaults(
    state: SessionState,
    chapter_ids: list[int],
    curriculum: dict[int, list[TopicDict]],
) -> None:
    """Initialize session state with defaults. Heals broken saves from old versions."""
    if not state.session_id:
        state.session_id = str(uuid.uuid4())
    if state.xp == 0 and state.streak == 0 and not state.chapter_frontiers:
        state.flawless_eligible = True
        state.max_streak = config.MAX_STREAK
        state.selected_chapter_id = chapter_ids[0] if chapter_ids else None
        state.selected_topic_id = _get_first_topic_id(
            curriculum, chapter_ids[0] if chapter_ids else None
        )
        state.selected_level = 1
        state.problem_answered = False
        state.current_input_mode = "radio"
        state.topic_completed = False
        state.feedback_type = None
        state.feedback_msg = ""
        state.level_completed = False

    for chapter_id in chapter_ids:
        chapter_first_topic_id = _get_first_topic_id(curriculum, chapter_id)
        if chapter_id not in state.chapter_frontiers:
            state.chapter_frontiers[chapter_id] = ChapterFrontier(
                frontier_topic_id=chapter_first_topic_id,
                frontier_level=1,
            )
        elif state.chapter_frontiers[chapter_id].frontier_topic_id < chapter_first_topic_id:
            state.chapter_frontiers[chapter_id].frontier_topic_id = chapter_first_topic_id
            state.chapter_frontiers[chapter_id].frontier_level = 1

    curr_chapter_id = state.selected_chapter_id
    first_curr_topic_id = _get_first_topic_id(curriculum, curr_chapter_id)
    if (
        state.selected_topic_id is None
        or state.selected_topic_id < first_curr_topic_id
    ):
        state.selected_topic_id = first_curr_topic_id


def reset_submission_cycle(
    state: SessionState, topics_by_id: dict[int, TopicMeta] | None = None
) -> None:
    """Clears the current problem state when navigating or advancing."""
    state.streak = 0
    state.flawless_eligible = True
    state.problem_answered = False
    state.topic_completed = False
    state.level_completed = False
    state.feedback_type = None
    state.feedback_msg = ""
    state.current_problem = None
    if topics_by_id is not None:
        state.current_input_mode = resolve_input_mode(state, topics_by_id)
    else:
        state.current_input_mode = "radio"


def sync_to_db(state: SessionState, play_mode: PlayMode | None = None) -> None:
    """Pushes current session state to the database."""
    mode = play_mode if play_mode is not None else resolve_play_mode(state.username)
    persist_state = _state_for_db_persist(state, mode)
    if persist_state.username:
        try:
            db.save_user(persist_state.username, persist_state)
        except Exception as e:
            print(f"Error syncing to database for user {persist_state.username}: {e}")
    if persist_state.session_id and persist_state.username:
        try:
            db.save_session(
                persist_state.session_id, persist_state.username, persist_state
            )
        except Exception as e:
            print(f"Error saving session {persist_state.session_id}: {e}")


def _state_for_db_persist(state: SessionState, play_mode: PlayMode) -> SessionState:
    """Return session snapshot for DB writes, preserving admin progression fields."""
    if not state.username or play_mode.persists_profile:
        return state

    persisted = db.load_user(state.username)
    if persisted is None:
        return state

    persist_state = state.model_copy(deep=True)
    persist_state.xp = persisted["xp"]
    persist_state.streak = persisted["streak"]
    persist_state.chapter_frontiers = persisted["chapter_frontiers"]
    return persist_state


def load_profile(
    state: SessionState,
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
        state.chapter_frontiers = user_data["chapter_frontiers"]
        topics_by_id = get_topics_by_id(state.selected_chapter_id or 0)
        reset_submission_cycle(state, topics_by_id)
    else:
        hard_reset(state, chapter_ids, curriculum)


def hard_reset(
    state: SessionState,
    chapter_ids: list[int],
    curriculum: dict[int, list[TopicDict]],
    play_mode: PlayMode | None = None,
) -> None:
    """Wipes all progress and resets to initial state."""
    state.xp = 0
    state.chapter_frontiers = {
        chapter_id: ChapterFrontier(
            frontier_topic_id=_get_first_topic_id(curriculum, chapter_id),
            frontier_level=1,
        )
        for chapter_id in chapter_ids
    }
    state.selected_chapter_id = chapter_ids[0] if chapter_ids else None
    state.selected_topic_id = _get_first_topic_id(
        curriculum, chapter_ids[0] if chapter_ids else None
    )
    state.selected_level = 1
    reset_submission_cycle(state)
    sync_to_db(state, play_mode)


def navigate_to(
    state: SessionState,
    chapter_id: int | None = None,
    topic_id: int | None = None,
    level: int | None = None,
    topics_by_id: dict[int, TopicMeta] | None = None,
    play_mode: PlayMode | None = None,
) -> None:
    """Navigate to a different chapter/topic/level, resetting submission cycle and syncing."""
    if chapter_id is not None:
        state.selected_chapter_id = chapter_id
    if topic_id is not None:
        state.selected_topic_id = topic_id
    if level is not None:
        state.selected_level = level
    reset_submission_cycle(state, topics_by_id)
    sync_to_db(state, play_mode)


def _grade_submission(
    state: SessionState,
    user_input: str,
    problem: ProblemDict,
    is_input_mode: bool,
) -> EvalResult:
    """Grade one submission and apply immediate feedback fields to state."""
    eval_result = evaluate_answer(user_input, problem, is_input_mode)
    state.problem_answered = eval_result.get("lock_answer", False)
    state.feedback_type = eval_result.get("feedback_type", None)
    state.feedback_msg = eval_result.get("feedback_msg", "")
    return eval_result


def process_submission(
    state: SessionState,
    problem: ProblemDict,
    user_input: str,
    is_input_mode: bool,
    topics_by_id: dict[int, TopicMeta],
    play_mode: PlayMode,
) -> EvalResult:
    """Process user submission: grade, log telemetry, apply outcome, sync."""
    if state.username is None or state.selected_chapter_id is None or state.selected_topic_id is None:
        raise RuntimeError("Session missing required context for submission")

    eval_result = _grade_submission(state, user_input, problem, is_input_mode)

    submission_telemetry.log_submission_telemetry(
        state,
        problem,
        user_input,
        is_input_mode,
        eval_result,
        topics_by_id,
    )
    submission_play_mode.apply_submission_outcome_via_play_mode(
        state, eval_result, topics_by_id, play_mode
    )
    sync_to_db(state, play_mode)
    return eval_result
