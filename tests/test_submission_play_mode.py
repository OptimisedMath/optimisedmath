"""Unit tests for submission play-mode adapter."""

import uuid

import backend.session_state as session_state
import backend.submission_play_mode as submission_play_mode
from backend.answer_grading import EvalResult
from backend.core import db
from backend.curriculum import Curriculum
from backend.models import ChapterFrontier, SessionState
from backend.play_mode import AdminPlayMode, StudentPlayMode
from tests.support.fixture_curriculum import TOPIC_MULTI

_STUDENT = StudentPlayMode()
_ADMIN = AdminPlayMode()


def _fresh_state(fixture_curriculum: Curriculum) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = "play-mode-user"
    state.session_id = str(uuid.uuid4())
    return state


def _chapter_id(state: SessionState) -> int:
    assert state.selected_chapter_id is not None
    return state.selected_chapter_id


def test_apply_submission_outcome_via_play_mode_updates_student_progress(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    chapter_id = _chapter_id(state)
    eval_result: EvalResult = {
        "is_correct": True,
        "lock_answer": True,
        "feedback_type": "success",
        "feedback_msg": "ok",
    }

    submission_play_mode.apply_submission_outcome_via_play_mode(
        state, eval_result, fixture_curriculum, _STUDENT
    )

    assert state.streak == 1
    assert state.problem_answered is False


def test_apply_submission_outcome_via_play_mode_skips_profile_writes_for_admin(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.username = "Antoni"
    chapter_id = _chapter_id(state)
    state.xp = 50
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = 2
    db.save_user(state.username, state.model_copy(update={"streak": 0}))
    eval_result: EvalResult = {
        "is_correct": True,
        "lock_answer": True,
        "feedback_type": "success",
        "feedback_msg": "ok",
    }

    submission_play_mode.apply_submission_outcome_via_play_mode(
        state, eval_result, fixture_curriculum, _ADMIN
    )

    assert state.streak == 1
    assert state.xp == 50
    assert state.chapter_frontiers[chapter_id].frontier_topic_id == TOPIC_MULTI
    assert state.chapter_frontiers[chapter_id].frontier_level == 1
