"""Unit tests for the session state layer."""

import uuid

import pytest

import backend.config as config
import backend.session_state as session_state
import backend.submission_cycle as submission_cycle
from backend.curriculum import Curriculum
from backend.core import db
from backend.models import ChapterFrontier, SessionState
from backend.play_mode import AdminPlayMode, DbWritePlan, StudentPlayMode
from backend.unlock import first_topic_id
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    CHAPTER_BETA,
    TOPIC_MULTI,
    TOPIC_RADIO,
    TOPIC_SINGLE,
)


def _fresh_state(fixture_curriculum: Curriculum) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = "session-state-user"
    state.session_id = str(uuid.uuid4())
    return state


def _username(state: SessionState) -> str:
    assert state.username is not None
    return state.username


def test_init_defaults_sets_session_and_chapter_frontiers(
    fixture_curriculum: Curriculum,
):
    state = SessionState()

    session_state.init_defaults(state, fixture_curriculum)

    chapter_ids = list(fixture_curriculum.chapter_ids())
    assert state.session_id
    assert state.selected_chapter_id == CHAPTER_ALPHA
    assert state.selected_topic_id == TOPIC_MULTI
    assert state.selected_level == 1
    assert state.current_input_mode == "radio"
    for chapter_id in chapter_ids:
        assert chapter_id in state.chapter_frontiers
        assert state.chapter_frontiers[chapter_id].frontier_level == 1


def test_resolve_input_mode_switches_to_input_after_streak_threshold(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI

    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    assert session_state.resolve_input_mode(state, fixture_curriculum) == "input"

    state.streak = 0
    assert session_state.resolve_input_mode(state, fixture_curriculum) == "radio"


def test_resolve_input_mode_stays_radio_for_radio_only_topics(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_RADIO
    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE

    assert session_state.resolve_input_mode(state, fixture_curriculum) == "radio"


@pytest.mark.parametrize(
    "streak", [0, 1, config.STREAK_THRESHOLD_FOR_INPUT_MODE, config.MAX_STREAK]
)
def test_radio_only_topic_serves_radio_mode_regardless_of_streak_for_student(
    fixture_curriculum: Curriculum, streak
):
    state = _fresh_state(fixture_curriculum)
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_RADIO
    state.streak = streak

    assert session_state.resolve_input_mode(state, fixture_curriculum) == "radio"


def test_hard_reset_wipes_progress_and_persists(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.xp = 100
    state.streak = 2
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=999,
        frontier_level=3,
    )

    session_state.hard_reset(state, fixture_curriculum, StudentPlayMode())

    assert state.xp == 0
    assert state.streak == 0
    assert state.problem_answered is False
    for chapter_id in fixture_curriculum.chapter_ids():
        expected_first = first_topic_id(list(fixture_curriculum.topics(chapter_id)))
        assert state.chapter_frontiers[chapter_id].frontier_topic_id == expected_first
        assert state.chapter_frontiers[chapter_id].frontier_level == 1

    loaded = db.load_user(_username(state))
    assert loaded is not None
    assert loaded["xp"] == 0


def test_load_profile_hydrates_existing_user(fixture_curriculum: Curriculum):
    username = "existing-user"
    saved = SessionState(
        username=username,
        xp=42,
        streak=1,
        selected_chapter_id=CHAPTER_ALPHA,
        selected_topic_id=TOPIC_MULTI,
        selected_level=2,
        chapter_frontiers={
            CHAPTER_ALPHA: ChapterFrontier(
                frontier_topic_id=TOPIC_MULTI, frontier_level=2
            ),
            CHAPTER_BETA: ChapterFrontier(
                frontier_topic_id=TOPIC_SINGLE, frontier_level=1
            ),
        },
    )
    db.save_user(username, saved)

    state = SessionState()
    session_state.load_profile(state, username, fixture_curriculum)

    assert state.username == username
    assert state.xp == 42
    assert state.selected_level == 2
    assert state.streak == 0
    assert state.problem_answered is False


def test_load_profile_hard_resets_new_user(fixture_curriculum: Curriculum):
    state = SessionState()

    session_state.load_profile(state, "brand-new-user", fixture_curriculum)

    assert state.username == "brand-new-user"
    assert state.xp == 0
    assert state.streak == 0
    assert state.selected_chapter_id == CHAPTER_ALPHA
    assert state.selected_topic_id == TOPIC_MULTI


def _polluted_submission_cycle_state(
    state: SessionState, fixture_curriculum: Curriculum
) -> None:
    """Fill cycle fields so a clear is observable."""
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    state.flawless_eligible = False
    state.problem_answered = True
    state.topic_completed = True
    state.level_completed = True
    state.feedback_type = "error"
    state.feedback_msg = "wrong"
    state.current_problem = {"problem_id": "p1"}
    state.current_input_mode = "input"
    assert session_state.resolve_input_mode(state, fixture_curriculum) == "input"


def _submission_cycle_field_snapshot(state: SessionState) -> dict[str, object]:
    """Capture the Submission-cycle fields owned by clear_submission_cycle_fields."""
    return {
        "streak": state.streak,
        "flawless_eligible": state.flawless_eligible,
        "problem_answered": state.problem_answered,
        "topic_completed": state.topic_completed,
        "level_completed": state.level_completed,
        "feedback_type": state.feedback_type,
        "feedback_msg": state.feedback_msg,
        "current_problem": state.current_problem,
        "current_input_mode": state.current_input_mode,
    }


def _reference_cleared_cycle_snapshot(
    fixture_curriculum: Curriculum,
) -> dict[str, object]:
    reference = _fresh_state(fixture_curriculum)
    _polluted_submission_cycle_state(reference, fixture_curriculum)
    session_state.clear_submission_cycle_fields(reference, fixture_curriculum)
    return _submission_cycle_field_snapshot(reference)


@pytest.mark.parametrize(
    "entry_point",
    ["navigate_to", "load_profile", "hard_reset"],
)
def test_submission_cycle_clear_entry_points_match_public_helper(
    fixture_curriculum: Curriculum,
    entry_point: str,
):
    """All three entry points clear the same cycle fields, including input mode."""
    username = f"cycle-clear-{entry_point}-user"
    expected = _reference_cleared_cycle_snapshot(fixture_curriculum)

    if entry_point == "load_profile":
        saved = SessionState(
            username=username,
            xp=10,
            streak=config.STREAK_THRESHOLD_FOR_INPUT_MODE,
            selected_chapter_id=CHAPTER_ALPHA,
            selected_topic_id=TOPIC_MULTI,
            selected_level=1,
            chapter_frontiers={
                CHAPTER_ALPHA: ChapterFrontier(
                    frontier_topic_id=TOPIC_MULTI, frontier_level=1
                ),
            },
        )
        db.save_user(username, saved)
        state = SessionState()
        session_state.load_profile(state, username, fixture_curriculum)
    else:
        state = _fresh_state(fixture_curriculum)
        _polluted_submission_cycle_state(state, fixture_curriculum)
        if entry_point == "navigate_to":
            submission_cycle.navigate_to(
                state, StudentPlayMode(), curriculum=fixture_curriculum
            )
        else:
            session_state.hard_reset(state, fixture_curriculum, StudentPlayMode())

    assert _submission_cycle_field_snapshot(state) == expected


def test_build_db_write_plan_student_writes_all_fields(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.xp = 99
    state.streak = 3

    plan = session_state.build_db_write_plan(state, StudentPlayMode())

    assert plan == DbWritePlan.write_all()
    persisted = session_state.apply_db_write_plan(state, plan)
    assert persisted is state
    assert persisted.xp == 99
    assert persisted.streak == 3


def test_build_db_write_plan_admin_preserves_profile_progression_fields(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.username = "Antoni"
    state.xp = 200
    state.streak = 4
    state.flawless_eligible = False
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_RADIO,
        frontier_level=2,
    )
    db.save_user(
        state.username,
        SessionState(
            username=state.username,
            xp=50,
            streak=0,
            chapter_frontiers={
                CHAPTER_ALPHA: ChapterFrontier(
                    frontier_topic_id=TOPIC_MULTI,
                    frontier_level=1,
                )
            },
        ),
    )

    plan = session_state.build_db_write_plan(state, AdminPlayMode())

    assert plan.write_xp is False
    assert plan.write_streak is False
    assert plan.write_chapter_frontiers is False
    assert plan.write_flawless_eligible is True
    assert plan.profile_xp == 50
    assert plan.profile_streak == 0
    assert plan.profile_chapter_frontiers[CHAPTER_ALPHA] == ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )

    persisted = session_state.apply_db_write_plan(state, plan)
    assert persisted.xp == 50
    assert persisted.streak == 0
    assert persisted.flawless_eligible is False
    assert persisted.chapter_frontiers[CHAPTER_ALPHA] == ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )


def test_persist_round_trips_flawless_eligible_for_student(
    fixture_curriculum: Curriculum,
):
    """A Flawless-eligible profile survives a real persist and re-read."""
    state = _fresh_state(fixture_curriculum)
    state.flawless_eligible = False

    session_state.persist(state, StudentPlayMode())

    reloaded = db.load_session(state.session_id)
    assert reloaded is not None
    assert reloaded.flawless_eligible is False


def test_persist_round_trips_flawless_eligible_and_preserved_profile_for_admin(
    fixture_curriculum: Curriculum,
):
    """The non-write-all build_db_write_plan path preserves the profile and flawless_eligible."""
    state = _fresh_state(fixture_curriculum)
    state.username = "admin-round-trip-user"
    state.flawless_eligible = False
    db.save_user(
        state.username,
        SessionState(
            username=state.username,
            xp=50,
            streak=0,
            chapter_frontiers={
                CHAPTER_ALPHA: ChapterFrontier(
                    frontier_topic_id=TOPIC_MULTI,
                    frontier_level=1,
                )
            },
        ),
    )

    session_state.persist(state, AdminPlayMode())

    reloaded = db.load_session(state.session_id)
    assert reloaded is not None
    assert reloaded.xp == 50
    assert reloaded.streak == 0
    assert reloaded.flawless_eligible is False
    assert reloaded.chapter_frontiers[CHAPTER_ALPHA] == ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )


def test_persist_matches_manual_build_and_sync_sequence_for_student_and_admin(
    fixture_curriculum: Curriculum,
):
    cases: list[tuple[StudentPlayMode | AdminPlayMode, str, SessionState | None]] = [
        (StudentPlayMode(), "persist-student", None),
        (
            AdminPlayMode(),
            "Antonio",
            SessionState(
                username="Antonio",
                xp=50,
                streak=0,
                chapter_frontiers={
                    CHAPTER_ALPHA: ChapterFrontier(
                        frontier_topic_id=TOPIC_MULTI,
                        frontier_level=1,
                    )
                },
            ),
        ),
    ]
    for mode, username, existing_profile in cases:
        if existing_profile is not None:
            db.save_user(username, existing_profile)

        state_via_persist = _fresh_state(fixture_curriculum)
        state_via_persist.username = username
        state_via_persist.xp = 42
        state_via_persist.streak = 2

        state_via_manual = state_via_persist.model_copy(deep=True)
        state_via_manual.session_id = str(uuid.uuid4())

        session_state.persist(state_via_persist, mode)
        session_state.sync_to_db(
            state_via_manual,
            session_state.build_db_write_plan(state_via_manual, mode),
        )

        loaded_via_persist = db.load_session(state_via_persist.session_id)
        loaded_via_manual = db.load_session(state_via_manual.session_id)
        assert loaded_via_persist is not None
        assert loaded_via_manual is not None
        assert loaded_via_persist.xp == loaded_via_manual.xp
        assert loaded_via_persist.streak == loaded_via_manual.streak
        assert (
            loaded_via_persist.chapter_frontiers == loaded_via_manual.chapter_frontiers
        )
