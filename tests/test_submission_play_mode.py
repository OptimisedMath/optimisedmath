"""Unit tests for submission play-mode adapter."""

import uuid

import pytest

import backend.session_state as session_state
import backend.submission_play_mode as submission_play_mode
from backend.answer_grading import EvalResult
from backend.core import db
from backend.curriculum_loader import get_curriculum, get_topics_by_id
from backend.models import ChapterFrontier, SessionState
from backend.play_mode import AdminPlayMode, StudentPlayMode

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    yield


def _fresh_state() -> SessionState:
    curriculum = get_curriculum()
    chapter_ids = sorted(curriculum.keys())
    state = SessionState()
    session_state.init_defaults(state, chapter_ids, curriculum)
    state.username = "play-mode-user"
    state.session_id = str(uuid.uuid4())
    return state


def _chapter_id(state: SessionState) -> int:
    assert state.selected_chapter_id is not None
    return state.selected_chapter_id


def test_apply_submission_outcome_via_play_mode_updates_student_progress():
    state = _fresh_state()
    chapter_id = _chapter_id(state)
    topics_by_id = get_topics_by_id(chapter_id)
    eval_result: EvalResult = {
        "is_correct": True,
        "lock_answer": True,
        "feedback_type": "success",
        "feedback_msg": "ok",
    }

    submission_play_mode.apply_submission_outcome_via_play_mode(
        state, eval_result, topics_by_id, _STUDENT
    )

    assert state.streak == 1
    assert state.problem_answered is False


def test_apply_submission_outcome_via_play_mode_skips_profile_writes_for_admin():
    state = _fresh_state()
    state.username = "Antoni"
    chapter_id = _chapter_id(state)
    state.xp = 50
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=10,
        frontier_level=1,
    )
    state.selected_topic_id = 10
    state.selected_level = 2
    db.save_user(state.username, state.model_copy(update={"streak": 0}))
    topics_by_id = get_topics_by_id(chapter_id)
    eval_result: EvalResult = {
        "is_correct": True,
        "lock_answer": True,
        "feedback_type": "success",
        "feedback_msg": "ok",
    }

    submission_play_mode.apply_submission_outcome_via_play_mode(
        state, eval_result, topics_by_id, _ADMIN
    )

    assert state.streak == 1
    assert state.xp == 50
    assert state.chapter_frontiers[chapter_id].frontier_topic_id == 10
    assert state.chapter_frontiers[chapter_id].frontier_level == 1
