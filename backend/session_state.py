"""Session state mutations for the FastAPI backend."""

import uuid

import backend.config as config
from backend.core import db
from backend.curriculum import Curriculum
import backend.navigation as navigation
from backend.play_mode import DbWritePlan, PlayMode, resolve_play_mode
from backend.models import ChapterFrontier, SessionState
from backend.unlock import first_topic_id


def _get_first_topic_id(curriculum: Curriculum, chapter_id: int | None) -> int:
    """Extract the first topic id for a chapter, with safe fallback."""
    if chapter_id is not None:
        topics = list(curriculum.topics(chapter_id))
        if topics:
            return first_topic_id(topics)
    return 1


def resolve_input_mode(state: SessionState, curriculum: Curriculum) -> str:
    """Determine input mode respecting streak threshold and radio-only topics."""
    topic_id = state.selected_topic_id
    chapter_id = state.selected_chapter_id
    if topic_id is None or chapter_id is None:
        return "radio"
    topic_cfg = curriculum.topic(int(chapter_id), int(topic_id)) or {}
    radio_only = topic_cfg.get("radio_only", False)
    if (
        not radio_only
        and state.streak >= config.STREAK_THRESHOLD_FOR_INPUT_MODE
    ):
        return "input"
    return "radio"


def init_defaults(state: SessionState, curriculum: Curriculum) -> None:
    """Initialize session state with defaults. Heals broken saves from old versions."""
    chapter_ids = list(curriculum.chapter_ids())
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


def clear_submission_cycle_fields(
    state: SessionState, curriculum: Curriculum | None = None
) -> None:
    """Clear Submission-cycle fields on ``state`` and re-resolve input mode when possible."""
    state.streak = 0
    state.flawless_eligible = True
    state.problem_answered = False
    state.topic_completed = False
    state.level_completed = False
    state.feedback_type = None
    state.feedback_msg = ""
    state.current_problem = None
    if curriculum is not None:
        state.current_input_mode = resolve_input_mode(state, curriculum)
    else:
        state.current_input_mode = "radio"


def build_db_write_plan(state: SessionState, play_mode: PlayMode) -> DbWritePlan:
    """Produce DB write eligibility once from play mode and persisted profile."""
    full_progression = play_mode.persists_profile

    if not state.username or full_progression:
        return DbWritePlan.write_all(full_progression=full_progression)

    persisted = db.load_user(state.username)
    if persisted is None:
        return DbWritePlan.write_all(full_progression=full_progression)

    return DbWritePlan(
        write_xp=False,
        write_streak=False,
        write_flawless_eligible=True,
        write_chapter_frontiers=False,
        full_progression=False,
        profile_xp=persisted["xp"],
        profile_streak=persisted["streak"],
        profile_chapter_frontiers=persisted["chapter_frontiers"],
    )


def apply_db_write_plan(state: SessionState, write_plan: DbWritePlan) -> SessionState:
    """Return session snapshot for DB writes according to ``write_plan``."""
    if (
        write_plan.write_xp
        and write_plan.write_streak
        and write_plan.write_flawless_eligible
        and write_plan.write_chapter_frontiers
    ):
        return state

    persist_state = state.model_copy(deep=True)
    if not write_plan.write_xp and write_plan.profile_xp is not None:
        persist_state.xp = write_plan.profile_xp
    if not write_plan.write_streak and write_plan.profile_streak is not None:
        persist_state.streak = write_plan.profile_streak
    if (
        not write_plan.write_chapter_frontiers
        and write_plan.profile_chapter_frontiers is not None
    ):
        persist_state.chapter_frontiers = write_plan.profile_chapter_frontiers
    if (
        not write_plan.write_flawless_eligible
        and write_plan.profile_flawless_eligible is not None
    ):
        persist_state.flawless_eligible = write_plan.profile_flawless_eligible
    return persist_state


def sync_to_db(state: SessionState, write_plan: DbWritePlan) -> None:
    """Pushes current session state to the database."""
    persist_state = apply_db_write_plan(state, write_plan)
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


def load_profile(
    state: SessionState,
    username: str,
    curriculum: Curriculum,
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
        clear_submission_cycle_fields(state, curriculum)
    else:
        hard_reset(state, curriculum)


def hard_reset(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode | None = None,
) -> None:
    """Wipes all progress and resets to initial state."""
    chapter_ids = list(curriculum.chapter_ids())
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
    _clear_submission_cycle_fields(state, curriculum)
    sync_to_db(state, build_db_write_plan(state, play_mode or resolve_play_mode(state.username)))

