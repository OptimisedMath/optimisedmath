"""Unit tests for the session use-case layer."""

import uuid

import pytest

import backend.config as config
import backend.session as session
import backend.session_state as session_state
from backend.core import db
from backend.curriculum_loader import get_curriculum, get_topics_by_id
from backend.models import SessionState, SessionStartRequest


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    session.ACTIVE_SESSIONS.clear()
    yield
    session.ACTIVE_SESSIONS.clear()


def _curriculum_and_chapters():
    curriculum = get_curriculum()
    chapter_ids = sorted(curriculum.keys())
    return curriculum, chapter_ids


def _fresh_state() -> SessionState:
    curriculum, chapter_ids = _curriculum_and_chapters()
    state = SessionState()
    session_state.init_defaults(state, chapter_ids, curriculum)
    state.username = "session-user"
    state.session_id = str(uuid.uuid4())
    return state


# --- Session lookup ---


def test_get_session_raises_when_missing():
    with pytest.raises(session.SessionNotFoundError) as exc_info:
        session.get_session(str(uuid.uuid4()))
    assert exc_info.value.status_code == 404


def test_get_session_loads_from_memory():
    session_id = str(uuid.uuid4())
    state = SessionState(session_id=session_id)
    session.ACTIVE_SESSIONS[session_id] = state
    assert session.get_session(session_id) is state


# --- SessionError hierarchy ---


@pytest.mark.parametrize(
    "error_cls, status_code",
    [
        (session.SessionError, 400),
        (session.SessionNotFoundError, 404),
        (session.ForbiddenError, 403),
        (session.ConflictError, 409),
        (session.InternalError, 500),
    ],
)
def test_session_error_status_codes(error_cls, status_code):
    exc = error_cls("test detail")
    assert exc.detail == "test detail"
    assert exc.status_code == status_code


def test_session_not_found_default_message():
    exc = session.SessionNotFoundError()
    assert exc.detail == "Session not found"
    assert exc.status_code == 404


# --- begin_problem ---


def test_begin_problem_resets_submission_state_and_sets_problem():
    state = _fresh_state()
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)
    problem = {"problem_id": "p1", "question": "2+2", "correct": "4", "options": ["4", "5"]}

    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "wrong"
    state.show_celebration = True

    session.begin_problem(state, problem, topics_by_id)

    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.show_celebration is False
    assert state.current_problem is problem
    assert state.problem_start_time is not None


def test_begin_problem_trims_recent_fingerprints():
    state = _fresh_state()
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)
    problem = {"problem_id": "p1", "question": "q", "correct": "1", "options": ["1"]}

    fingerprints = [f"fp-{index}" for index in range(config.MAX_RETRIES_DUPLICATE_CHECK + 3)]
    session.begin_problem(
        state, problem, topics_by_id, recent_fingerprints=fingerprints
    )

    assert len(state.recent_problem_fingerprints) == config.MAX_RETRIES_DUPLICATE_CHECK
    assert state.recent_problem_fingerprints == fingerprints[-config.MAX_RETRIES_DUPLICATE_CHECK :]


def test_begin_problem_resolves_input_mode_from_streak():
    state = _fresh_state()
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)
    problem = {"problem_id": "p1", "question": "q", "correct": "1", "options": ["1"]}

    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    session.begin_problem(state, problem, topics_by_id)

    assert state.current_input_mode == "input"


# --- respond ---


def test_respond_attaches_navigation():
    state = _fresh_state()
    curriculum, _ = _curriculum_and_chapters()

    response = session.respond(state, curriculum)

    assert response.navigation is not None
    assert len(response.navigation.available_chapters) > 0
    assert response.navigation.available_topics


# --- public_problem ---


def test_public_problem_strips_unsafe_svg():
    state = _fresh_state()
    problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": "1",
        "options": ["1"],
        "image_html": '<svg><script>alert(1)</script></svg>',
    }

    public = session.public_problem(problem, state)

    assert public["image_html"] is None
    assert public["answer_options"] == ["1"]
    assert public["input_mode"] == state.current_input_mode


def test_public_problem_includes_correct_answer_when_answered():
    state = _fresh_state()
    state.problem_answered = True
    problem = {"problem_id": "p1", "question": "q", "correct": "42", "options": ["42"]}

    public = session.public_problem(problem, state)

    assert public["correct_answer"] == "42"


# --- start_session ---


def test_start_session_returns_state_with_navigation():
    response = session.start_session(
        SessionStartRequest(username=f"user-{uuid.uuid4()}")
    )

    assert response.session_id
    assert response.navigation is not None
    assert response.session_id in session.ACTIVE_SESSIONS


def test_start_session_raises_for_unknown_chapter():
    with pytest.raises(session.SessionError) as exc_info:
        session.start_session(
            SessionStartRequest(username="user", selected_chapter_id=99999)
        )
    assert exc_info.value.status_code == 400
    assert "not found" in exc_info.value.detail
