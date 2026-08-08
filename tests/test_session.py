"""Unit tests for the session use-case layer."""

import uuid

import pytest

import backend.config as config
import backend.session as session
import backend.session_state as session_state
from backend.play_mode import resolve_play_mode
from backend.core import db
from backend.curriculum_loader import get_curriculum, get_topics_by_id
from backend.core.utils import clean_latex
from backend.models import (
    AutoSolveRequest,
    ChapterFrontier,
    ProblemSubmissionRequest,
    SessionNavigateRequest,
    SessionState,
    SessionStartRequest,
)


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


def _chapter_id(state: SessionState) -> int:
    assert state.selected_chapter_id is not None
    return state.selected_chapter_id


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
    chapter_id = _chapter_id(state)
    topics_by_id = get_topics_by_id(chapter_id)
    problem = {"problem_id": "p1", "question": "2+2", "correct": "4", "options": ["4", "5"]}

    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "wrong"
    state.level_completed = True

    session.begin_problem(state, problem, topics_by_id)

    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.level_completed is False
    assert state.current_problem is problem
    assert state.problem_start_time is not None


def test_begin_problem_trims_recent_fingerprints():
    state = _fresh_state()
    chapter_id = _chapter_id(state)
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
    chapter_id = _chapter_id(state)
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

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert public["image_html"] is None
    assert public["answer_options"] == ["1"]
    assert public["input_mode"] == state.current_input_mode


def test_public_problem_includes_correct_answer_when_answered():
    state = _fresh_state()
    state.problem_answered = True
    problem = {"problem_id": "p1", "question": "q", "correct": "42", "options": ["42"]}

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert public["correct_answer"] == "42"


def test_public_problem_includes_correct_answer_for_admin_before_answered():
    state = _fresh_state()
    state.username = next(iter(config.ADMIN_USERNAMES))
    state.current_input_mode = "radio"
    problem = {"problem_id": "p1", "question": "q", "correct": "42", "options": ["41", "42"]}

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert public["correct_answer"] == "42"


def test_public_problem_hides_correct_answer_for_non_admin_before_answered():
    state = _fresh_state()
    state.problem_answered = False
    problem = {"problem_id": "p1", "question": "q", "correct": "42", "options": ["42"]}

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert "correct_answer" not in public


def test_public_problem_includes_cleaned_correct_answer_for_admin_input_mode():
    state = _fresh_state()
    state.username = next(iter(config.ADMIN_USERNAMES))
    state.current_input_mode = "input"
    problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": r"\dfrac{3}{4}",
        "options": [],
    }

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert public["correct_answer"] == "3/4"


def _submission_snapshot(state: SessionState) -> dict[str, object]:
    chapter_id = _chapter_id(state)
    prog = state.chapter_frontiers[chapter_id]
    return {
        "streak": state.streak,
        "xp": state.xp,
        "flawless_eligible": state.flawless_eligible,
        "problem_answered": state.problem_answered,
        "feedback_type": state.feedback_type,
        "feedback_msg": state.feedback_msg,
        "level_completed": state.level_completed,
        "topic_completed": state.topic_completed,
        "selected_level": state.selected_level,
        "frontier_topic_id": prog.frontier_topic_id,
        "frontier_level": prog.frontier_level,
        "current_input_mode": state.current_input_mode,
    }


def _begin_identical_problem(
    state: SessionState, problem: dict[str, object]
) -> None:
    chapter_id = _chapter_id(state)
    session.begin_problem(state, problem, get_topics_by_id(chapter_id))
    session.ACTIVE_SESSIONS[state.session_id] = state


def test_manual_submit_and_auto_solve_produce_identical_state_deltas():
    problem = {
        "problem_id": "p-parity",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }

    manual_state = _fresh_state()
    manual_state.username = next(iter(config.ADMIN_USERNAMES))
    _begin_identical_problem(manual_state, dict(problem))

    manual_response = session.submit_problem(
        ProblemSubmissionRequest(
            session_id=manual_state.session_id,
            problem_id="p-parity",
            user_input="2",
            is_input_mode=False,
        )
    )

    auto_state = _fresh_state()
    auto_state.username = manual_state.username
    _begin_identical_problem(auto_state, dict(problem))

    auto_response = session.auto_solve_problem(
        AutoSolveRequest(session_id=auto_state.session_id, problem_id="p-parity")
    )

    assert _submission_snapshot(manual_state) == _submission_snapshot(auto_state)
    assert manual_response.is_correct == auto_response.is_correct
    assert manual_response.feedback == auto_response.feedback


def test_manual_submit_and_auto_solve_match_in_input_mode():
    problem = {
        "problem_id": "p-parity-input",
        "question": "q",
        "correct": r"\dfrac{3}{4}",
        "options": [],
        "options_map": {},
        "messages": {},
    }
    derived_input = clean_latex(problem["correct"])

    manual_state = _fresh_state()
    manual_state.username = next(iter(config.ADMIN_USERNAMES))
    manual_state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    chapter_id = _chapter_id(manual_state)
    session.begin_problem(manual_state, dict(problem), get_topics_by_id(chapter_id))
    session.ACTIVE_SESSIONS[manual_state.session_id] = manual_state
    assert manual_state.current_input_mode == "input"

    manual_response = session.submit_problem(
        ProblemSubmissionRequest(
            session_id=manual_state.session_id,
            problem_id="p-parity-input",
            user_input=derived_input,
            is_input_mode=True,
        )
    )

    auto_state = _fresh_state()
    auto_state.username = manual_state.username
    auto_state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    session.begin_problem(auto_state, dict(problem), get_topics_by_id(chapter_id))
    session.ACTIVE_SESSIONS[auto_state.session_id] = auto_state

    auto_response = session.auto_solve_problem(
        AutoSolveRequest(
            session_id=auto_state.session_id, problem_id="p-parity-input"
        )
    )

    assert _submission_snapshot(manual_state) == _submission_snapshot(auto_state)
    assert manual_response.is_correct == auto_response.is_correct
    assert manual_response.feedback == auto_response.feedback


def test_admin_auto_solve_uses_flat_submission_rules():
    state = _fresh_state()
    state.username = next(iter(config.ADMIN_USERNAMES))
    state.xp = 40
    chapter_id = _chapter_id(state)
    state.chapter_frontiers[chapter_id].frontier_level = 1
    state.selected_level = 2
    state.streak = 0
    problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }
    session.begin_problem(state, problem, get_topics_by_id(chapter_id))
    session.ACTIVE_SESSIONS[state.session_id] = state
    db.save_user(state.username, state.model_copy(update={"streak": 0}))

    response = session.auto_solve_problem(
        AutoSolveRequest(session_id=state.session_id, problem_id="p1")
    )

    assert response.is_correct is True
    assert state.streak == 1
    assert "XP" not in response.feedback
    loaded = db.load_user(state.username)
    assert loaded is not None
    assert loaded["xp"] == 40
    assert loaded["streak"] == 0


def test_admin_navigates_to_locked_topic_without_bypass():
    state = _fresh_state()
    state.username = next(iter(config.ADMIN_USERNAMES))
    session.ACTIVE_SESSIONS[state.session_id] = state
    curriculum, _ = _curriculum_and_chapters()
    chapter_id = _chapter_id(state)
    chapter_topics = curriculum[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    locked_topic = chapter_topics[-1]
    locked_topic_id = int(locked_topic["topic_id"])
    max_level = int(locked_topic["max_level"])
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=int(chapter_topics[0]["topic_id"]),
        frontier_level=1,
    )

    response = session.navigate_session(
        SessionNavigateRequest(
            session_id=state.session_id,
            selected_chapter_id=chapter_id,
            selected_topic_id=locked_topic_id,
            selected_level=max_level,
        )
    )

    assert response.selected_topic_id == locked_topic_id
    assert response.selected_level == max_level


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
