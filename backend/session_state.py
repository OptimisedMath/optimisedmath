"""Session state mutations for the FastAPI backend."""

import uuid

import backend.config as config
from backend.core import db
from backend.curriculum import Curriculum
from backend.play_mode import DbWritePlan, PlayMode, resolve_play_mode
from backend.models import ChapterFrontier, SessionState
from backend.unlock import first_topic_id


def _get_first_topic_id(curriculum: Curriculum, chapter_id: int | None) -> int:
    if chapter_id is not None:
        topics = list(curriculum.topics(chapter_id))
        if topics:
            return first_topic_id(topics)
    return 1


def resolve_input_mode(state: SessionState, curriculum: Curriculum) -> str:
    topic_id = state.selected_topic_id
    chapter_id = state.selected_chapter_id
    if topic_id is None or chapter_id is None:
        return "radio"
    topic_cfg = curriculum.topic_by_id(int(chapter_id), int(topic_id)) or {}
    radio_only = topic_cfg.get("radio_only", False)
    if not radio_only and state.streak >= config.STREAK_THRESHOLD_FOR_INPUT_MODE:
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
        elif (
            state.chapter_frontiers[chapter_id].frontier_topic_id
            < chapter_first_topic_id
        ):
            state.chapter_frontiers[chapter_id].frontier_topic_id = (
                chapter_first_topic_id
            )
            state.chapter_frontiers[chapter_id].frontier_level = 1

    curr_chapter_id = state.selected_chapter_id
    first_curr_topic_id = _get_first_topic_id(curriculum, curr_chapter_id)
    if state.selected_topic_id is None or state.selected_topic_id < first_curr_topic_id:
        state.selected_topic_id = first_curr_topic_id


def reset_submission_cycle(
    state: SessionState,
    curriculum: Curriculum | None = None,
    *,
    reset_streak: bool = True,
) -> None:
    """Clear Submission-cycle fields on ``state`` and re-resolve input mode when possible.

    Sole owner of clearing these fields — ``reset_streak=False`` is the begin-problem
    variant that keeps the running streak, used when serving the next Problem within
    the same cycle rather than navigating away from it.
    """
    if reset_streak:
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


def lift_answer_lock(state: SessionState, curriculum: Curriculum | None = None) -> None:
    """Reopen the triggering Problem for the discounted retry a completed
    Deconstruction earns — CONTEXT.md's Answer lock, "lifted once, exceptionally".

    Delegates to `reset_submission_cycle` (keeping the running streak, mirroring
    `begin_problem`) rather than writing the cycle flags directly, then restores
    `current_problem` to the same instance so the Student answers the Problem
    they were on rather than a freshly generated one.
    """
    problem = state.current_problem
    reset_submission_cycle(state, curriculum, reset_streak=False)
    state.current_problem = problem


def mark_level_and_topic_completion(
    state: SessionState, *, level_completed: bool, topic_completed: bool
) -> None:
    if level_completed:
        state.level_completed = True
    if topic_completed:
        state.topic_completed = True


def build_db_write_plan(state: SessionState, play_mode: PlayMode) -> DbWritePlan:
    if not state.username or play_mode.persists_profile:
        return DbWritePlan.write_all()

    persisted = db.load_user(state.username)
    if persisted is None:
        return DbWritePlan.write_all()

    return DbWritePlan(
        write_xp=False,
        write_streak=False,
        write_flawless_eligible=True,
        write_chapter_frontiers=False,
        profile_xp=persisted["xp"],
        profile_streak=persisted["streak"],
        profile_chapter_frontiers=persisted["chapter_frontiers"],
    )


def overlay_db_write_plan(state: SessionState, write_plan: DbWritePlan) -> SessionState:
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
    return persist_state


def write_state_to_db(state: SessionState, write_plan: DbWritePlan) -> None:
    persist_state = overlay_db_write_plan(state, write_plan)
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


def persist(state: SessionState, play_mode: PlayMode) -> None:
    write_state_to_db(state, build_db_write_plan(state, play_mode))


def load_profile(
    state: SessionState,
    username: str,
    curriculum: Curriculum,
    *,
    should_persist: bool = True,
) -> None:
    """Loads user data from DB or initializes a fresh profile.

    ``should_persist=False`` lets a caller that persists once for a larger unit
    of work (e.g. Session start) skip the write ``hard_reset`` would otherwise
    make for a brand-new user. Sets ``state.username`` before resolving play
    mode, so a brand-new profile's hard reset always reflects the requesting
    username's play mode.
    """
    state.username = username
    user_data = db.load_user(username)

    if user_data:
        state.xp = user_data["xp"]
        state.streak = user_data["streak"]
        state.selected_chapter_id = user_data["selected_chapter_id"]
        state.selected_topic_id = user_data["selected_topic_id"]
        state.selected_level = user_data["selected_level"]
        state.chapter_frontiers = user_data["chapter_frontiers"]
        reset_submission_cycle(state, curriculum)
    else:
        hard_reset(
            state,
            curriculum,
            resolve_play_mode(state.username),
            should_persist=should_persist,
        )


def hard_reset(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode,
    *,
    should_persist: bool = True,
) -> None:
    """Wipes all progress and resets to initial state.

    ``should_persist=False`` lets a caller that persists once for a larger unit
    of work (e.g. ``load_profile`` during Session start) skip the write here.
    """
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
    reset_submission_cycle(state, curriculum)
    if should_persist:
        persist(state, play_mode)
