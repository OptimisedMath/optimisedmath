"""Unit tests for the session state layer."""

import uuid

import pytest

import backend.config as config
import backend.session_state as session_state
from backend.curriculum import Curriculum
from backend.core import db
from backend.models import ChapterFrontier, SessionState
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


@pytest.mark.parametrize("streak", [0, 1, config.STREAK_THRESHOLD_FOR_INPUT_MODE, config.MAX_STREAK])
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

    session_state.hard_reset(state, fixture_curriculum)

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

