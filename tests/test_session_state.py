"""Unit tests for the session state layer."""

import sqlite3
import uuid

import pytest

import backend.config as config
import backend.session_state as session_state
from backend.core import db
from backend.curriculum_loader import get_curriculum, get_topics_by_id
from backend.models import ChapterProgress, SessionState
from backend.unlock import first_topic_id


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    yield


def _curriculum_and_chapters():
    curriculum = get_curriculum()
    chapter_ids = sorted(curriculum.keys())
    return curriculum, chapter_ids


def _fresh_state() -> SessionState:
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = SessionState()
    session_state.init_defaults(state, chapter_ids, curriculum)
    state.username = "session-state-user"
    state.session_id = str(uuid.uuid4())
    return state


def test_init_defaults_sets_session_and_chapter_progress():
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = SessionState()

    session_state.init_defaults(state, chapter_ids, curriculum)

    assert state.session_id
    assert state.selected_chapter_id == chapter_ids[0]
    assert state.selected_topic_id is not None
    assert state.selected_level == 1
    assert state.current_input_mode == "radio"
    for chapter_id in chapter_ids:
        assert chapter_id in state.chapter_progress
        assert state.chapter_progress[chapter_id].unlocked_level == 1


def test_reset_submission_cycle_clears_problem_and_feedback():
    state = _fresh_state()
    state.streak = 2
    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "oops"
    state.current_problem = {"problem_id": "p1"}

    session_state.reset_submission_cycle(state)

    assert state.streak == 0
    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.current_problem is None
    assert state.current_input_mode == "radio"


def test_resolve_input_mode_switches_to_input_after_streak_threshold():
    state = _fresh_state()
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)

    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    assert session_state.resolve_input_mode(state, topics_by_id) == "input"

    state.streak = 0
    assert session_state.resolve_input_mode(state, topics_by_id) == "radio"


def test_resolve_input_mode_stays_radio_for_radio_only_topics():
    curriculum, chapter_ids = _curriculum_and_chapters()
    radio_only_chapter = None
    radio_only_topic = None
    for chapter_id in chapter_ids:
        for topic in curriculum[chapter_id]:
            if topic.get("radio_only"):
                radio_only_chapter = chapter_id
                radio_only_topic = int(topic["topic_id"])
                break
        if radio_only_chapter is not None:
            break

    assert radio_only_chapter is not None
    state = _fresh_state()
    state.selected_chapter_id = radio_only_chapter
    state.selected_topic_id = radio_only_topic
    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE

    topics_by_id = get_topics_by_id(radio_only_chapter)
    assert session_state.resolve_input_mode(state, topics_by_id) == "radio"


def test_navigate_to_updates_selection_and_resets_submission_cycle():
    state = _fresh_state()
    curriculum, _ = _curriculum_and_chapters()
    chapter_id = state.selected_chapter_id
    topics = curriculum[chapter_id]
    target_topic_id = int(topics[1]["topic_id"]) if len(topics) > 1 else int(topics[0]["topic_id"])
    topics_by_id = get_topics_by_id(chapter_id)

    state.streak = 2
    state.problem_answered = True
    state.current_problem = {"problem_id": "p1"}

    session_state.navigate_to(
        state,
        topic_id=target_topic_id,
        level=2,
        topics_by_id=topics_by_id,
    )

    assert state.selected_topic_id == target_topic_id
    assert state.selected_level == 2
    assert state.streak == 0
    assert state.problem_answered is False
    assert state.current_problem is None


def test_hard_reset_wipes_progress_and_persists():
    state = _fresh_state()
    curriculum, chapter_ids = _curriculum_and_chapters()
    state.xp = 100
    state.streak = 2
    state.chapter_progress[state.selected_chapter_id] = ChapterProgress(
        unlocked_topic_id=999,
        unlocked_level=3,
    )

    session_state.hard_reset(state, chapter_ids, curriculum)

    assert state.xp == 0
    assert state.streak == 0
    assert state.problem_answered is False
    for chapter_id in chapter_ids:
        expected_first = first_topic_id(curriculum[chapter_id])
        assert state.chapter_progress[chapter_id].unlocked_topic_id == expected_first
        assert state.chapter_progress[chapter_id].unlocked_level == 1

    loaded = db.load_user(state.username)
    assert loaded is not None
    assert loaded["xp"] == 0


def test_load_profile_hydrates_existing_user():
    curriculum, chapter_ids = _curriculum_and_chapters()
    username = "existing-user"
    saved = SessionState(
        username=username,
        xp=42,
        streak=1,
        selected_chapter_id=chapter_ids[0],
        selected_topic_id=int(curriculum[chapter_ids[0]][0]["topic_id"]),
        selected_level=2,
        chapter_progress={
            chapter_id: ChapterProgress(unlocked_topic_id=10, unlocked_level=2)
            for chapter_id in chapter_ids
        },
    )
    db.save_user(username, saved)

    state = SessionState()
    session_state.load_profile(state, username, chapter_ids, curriculum)

    assert state.username == username
    assert state.xp == 42
    assert state.selected_level == 2
    assert state.streak == 0
    assert state.problem_answered is False


def test_load_profile_hard_resets_new_user():
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = SessionState()

    session_state.load_profile(state, "brand-new-user", chapter_ids, curriculum)

    assert state.username == "brand-new-user"
    assert state.xp == 0
    assert state.streak == 0


def test_process_submission_grades_and_persists():
    state = _fresh_state()
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)
    problem = {
        "problem_id": "p-correct",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
    }
    state.current_problem = problem
    session_state.sync_to_db(state)

    result = session_state.process_submission(
        state, problem, "2", False, topics_by_id
    )

    assert result["is_correct"] is True
    assert state.streak == 1
    assert state.problem_answered is True
    assert state.feedback_type == "success"

    loaded = db.load_user(state.username)
    assert loaded is not None
    assert loaded["streak"] == 1


def _correct_problem() -> dict:
    return {
        "problem_id": "p-correct",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
    }


def _telemetry_count(session_id: str) -> int:
    with sqlite3.connect(db.DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM telemetry_logs WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return int(row[0])


def _admin_state_at(
    *,
    unlocked_topic_id: int,
    unlocked_level: int,
    selected_topic_id: int,
    selected_level: int,
    xp: int = 0,
    streak: int = 0,
    flawless_eligible: bool = True,
) -> SessionState:
    state = _fresh_state()
    state.username = "Antoni"
    chapter_id = state.selected_chapter_id
    state.chapter_progress[chapter_id] = ChapterProgress(
        unlocked_topic_id=unlocked_topic_id,
        unlocked_level=unlocked_level,
    )
    state.selected_topic_id = selected_topic_id
    state.selected_level = selected_level
    state.xp = xp
    state.streak = streak
    state.flawless_eligible = flawless_eligible
    state.level_completed = False
    state.topic_completed = False
    baseline = state.model_copy(deep=True)
    baseline.streak = 0
    db.save_user(state.username, baseline)
    db.save_session(state.session_id, state.username, baseline)
    return state


def _wrong_problem() -> dict:
    return {
        "problem_id": "p-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
    }


def _assert_admin_profile_unchanged(
    state: SessionState,
    *,
    xp: int,
    unlocked_topic_id: int,
    unlocked_level: int,
) -> None:
    chapter_id = state.selected_chapter_id
    assert state.xp == xp
    assert state.flawless_eligible is True
    assert state.level_completed is False
    assert state.topic_completed is False
    assert state.chapter_progress[chapter_id].unlocked_topic_id == unlocked_topic_id
    assert state.chapter_progress[chapter_id].unlocked_level == unlocked_level

    loaded = db.load_user(state.username)
    assert loaded is not None
    assert loaded["xp"] == xp
    assert loaded["streak"] == 0
    assert loaded["chapter_progress"][chapter_id] == ChapterProgress(
        unlocked_topic_id=unlocked_topic_id,
        unlocked_level=unlocked_level,
    )


@pytest.mark.parametrize(
    (
        "selected_topic_id",
        "selected_level",
        "initial_streak",
        "expect_streak",
    ),
    [
        (10, 2, 0, 1),
        (20, 1, 0, 1),
        (10, 1, 1, 2),
    ],
)
def test_admin_correct_increments_session_streak_without_profile_writes(
    selected_topic_id,
    selected_level,
    initial_streak,
    expect_streak,
):
    state = _admin_state_at(
        unlocked_topic_id=10,
        unlocked_level=1,
        selected_topic_id=selected_topic_id,
        selected_level=selected_level,
        xp=50,
        streak=initial_streak,
    )
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)
    telemetry_before = _telemetry_count(state.session_id)

    result = session_state.process_submission(
        state, _correct_problem(), "2", False, topics_by_id
    )

    assert result["is_correct"] is True
    assert state.feedback_type == "success"
    assert state.problem_answered is True
    assert "XP" not in state.feedback_msg
    assert _telemetry_count(state.session_id) == telemetry_before + 1
    assert state.streak == expect_streak
    _assert_admin_profile_unchanged(
        state, xp=50, unlocked_topic_id=10, unlocked_level=1
    )


def test_admin_wrong_decrements_session_streak_without_profile_writes():
    state = _admin_state_at(
        unlocked_topic_id=10,
        unlocked_level=1,
        selected_topic_id=10,
        selected_level=2,
        streak=2,
    )
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)

    session_state.process_submission(
        state, _wrong_problem(), "3", False, topics_by_id
    )

    assert state.streak == 1
    assert state.feedback_type == "warning"
    _assert_admin_profile_unchanged(
        state, xp=0, unlocked_topic_id=10, unlocked_level=1
    )


def test_admin_ahead_of_unlock_reaches_input_mode_after_streak_threshold():
    state = _admin_state_at(
        unlocked_topic_id=10,
        unlocked_level=1,
        selected_topic_id=10,
        selected_level=2,
        streak=0,
    )
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)

    session_state.process_submission(
        state, _correct_problem(), "2", False, topics_by_id
    )

    assert session_state.resolve_input_mode(state, topics_by_id) == "input"


def test_admin_ahead_by_topic_keeps_streak_through_unlock_threshold():
    state = _admin_state_at(
        unlocked_topic_id=10,
        unlocked_level=1,
        selected_topic_id=20,
        selected_level=1,
        streak=2,
    )
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)

    session_state.process_submission(
        state, _correct_problem(), "2", False, topics_by_id
    )

    assert state.streak == 3
    _assert_admin_profile_unchanged(
        state, xp=0, unlocked_topic_id=10, unlocked_level=1
    )
