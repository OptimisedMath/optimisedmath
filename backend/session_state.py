"""Session state mutations for the FastAPI backend."""

import json
import time
import uuid

import backend.config as config
from backend.answer_grading import EvalResult, evaluate_answer
from backend.core import db
from backend.core.utils import ProblemDict
from backend.curriculum_loader import (
    TopicDict,
    TopicMeta,
    get_chapter_name_by_id,
    get_topics_by_id,
)
from backend.progression import SubmissionContext, SubmissionOutcome, apply_submission
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


def sync_to_db(state: SessionState) -> None:
    """Pushes current session state to the database."""
    persist_state = _state_for_db_persist(state)
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


def _state_for_db_persist(state: SessionState) -> SessionState:
    """Return session snapshot for DB writes, preserving admin progression fields."""
    if not state.username or not config.is_admin_user(state.username):
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
    sync_to_db(state)


def navigate_to(
    state: SessionState,
    chapter_id: int | None = None,
    topic_id: int | None = None,
    level: int | None = None,
    topics_by_id: dict[int, TopicMeta] | None = None,
) -> None:
    """Navigate to a different chapter/topic/level, resetting submission cycle and syncing."""
    if chapter_id is not None:
        state.selected_chapter_id = chapter_id
    if topic_id is not None:
        state.selected_topic_id = topic_id
    if level is not None:
        state.selected_level = level
    reset_submission_cycle(state, topics_by_id)
    sync_to_db(state)


def _build_submission_context(
    state: SessionState,
    chapter_id: int,
    topic_id: int,
    topics_by_id: dict[int, TopicMeta],
) -> SubmissionContext:
    prog = state.chapter_frontiers[chapter_id]
    topic_meta = topics_by_id[topic_id]
    next_topic_ids = tuple(
        sorted(int(tid) for tid in topics_by_id if int(tid) > topic_id)
    )
    return SubmissionContext(
        chapter_id=chapter_id,
        topic_id=topic_id,
        selected_level=state.selected_level,
        current_streak=state.streak,
        flawless_eligible=state.flawless_eligible,
        frontier_level=prog.frontier_level,
        topic_max_level=int(topic_meta["max_level"]),
        next_topic_ids=next_topic_ids,
    )


def _apply_submission_outcome(
    state: SessionState, chapter_id: int, outcome: SubmissionOutcome
) -> None:
    state.streak = outcome.new_streak
    state.flawless_eligible = outcome.new_flawless_eligible
    state.xp += outcome.xp_earned
    if outcome.feedback_type is not None:
        state.feedback_type = outcome.feedback_type
    if outcome.feedback_msg is not None:
        state.feedback_msg = outcome.feedback_msg
    if outcome.level_completed:
        state.level_completed = True
    if outcome.topic_completed:
        state.topic_completed = True
    if outcome.new_selected_level is not None:
        state.selected_level = outcome.new_selected_level

    prog = state.chapter_frontiers[chapter_id]
    if outcome.new_frontier_level is not None:
        prog.frontier_level = outcome.new_frontier_level
    if outcome.unlock_topic_id is not None:
        prog.frontier_topic_id = outcome.unlock_topic_id


def _apply_admin_session_streak(
    state: SessionState, chapter_id: int, eval_result: EvalResult
) -> None:
    """Apply in-cycle streak rules for admin QA without profile progression."""
    is_correct = eval_result.get("is_correct", False)
    feedback_type = eval_result.get("feedback_type")
    is_soft_error = feedback_type == "info"

    if is_correct:
        new_streak = state.streak
        if new_streak < config.MAX_STREAK:
            new_streak += 1

        prog = state.chapter_frontiers[chapter_id]
        at_boundary = (
            state.selected_topic_id == prog.frontier_topic_id
            and state.selected_level == prog.frontier_level
        )
        if new_streak == config.STARS_FOR_UNLOCK and at_boundary:
            new_streak = 0

        state.streak = new_streak
        if state.feedback_type is None:
            state.feedback_type = "success"
            state.feedback_msg = "Brawo! To poprawna odpowiedź. 🎉"
        return

    if state.streak > 0 and not is_soft_error:
        state.streak -= 1


def process_submission(
    state: SessionState,
    problem: ProblemDict,
    user_input: str,
    is_input_mode: bool,
    topics_by_id: dict[int, TopicMeta],
) -> EvalResult:
    """Process user submission: evaluate, log telemetry, handle rewards and progression."""
    eval_result = evaluate_answer(user_input, problem, is_input_mode)
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
        is_input_mode=is_input_mode,
        is_correct=is_correct,
        user_input=user_input,
        trap_id=trap_id_hit,
        time_spent_seconds=time_spent,
        equation_state=problem_state,
    )

    prog = state.chapter_frontiers[chapter_id]
    admin_mode = config.is_admin_user(username)
    if admin_mode:
        _apply_admin_session_streak(state, chapter_id, eval_result)
        sync_to_db(state)
        return eval_result

    submission_ctx = _build_submission_context(
        state, chapter_id, topic_id, topics_by_id
    )
    submission_outcome = apply_submission(eval_result, submission_ctx)
    _apply_submission_outcome(state, chapter_id, submission_outcome)

    sync_to_db(state)
    return eval_result
