"""Unit tests for the session use-case layer."""

import json
import uuid

import pytest

import backend.config as config
import backend.session as session
import backend.session_state as session_state
from backend.curriculum import Curriculum, resolve_curriculum, set_curriculum
from backend.play_mode import resolve_play_mode
from backend.core import db
from backend.core.utils import clean_latex
from backend.models import (
    AutoSolveRequest,
    ChapterFrontier,
    ProblemSubmissionRequest,
    SessionNavigateRequest,
    SessionResponse,
    SessionState,
    SessionStartRequest,
)
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    CHAPTER_BETA,
    TOPIC_MULTI,
    TOPIC_RADIO,
)


@pytest.fixture(autouse=True)
def isolated_sessions(isolated_db):
    session.ACTIVE_SESSIONS.clear()
    yield
    session.ACTIVE_SESSIONS.clear()


@pytest.fixture(autouse=True)
def _override_curriculum(fixture_curriculum: Curriculum):
    set_curriculum(fixture_curriculum)
    yield
    set_curriculum(None)


def _fresh_state(fixture_curriculum: Curriculum) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
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


def test_begin_problem_resets_submission_state_and_sets_problem(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    problem = {"problem_id": "p1", "question": "2+2", "correct": "4", "options": ["4", "5"]}

    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "wrong"
    state.level_completed = True

    session.begin_problem(state, problem, fixture_curriculum)

    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.level_completed is False
    assert state.current_problem is problem
    assert state.problem_start_time is not None


def test_begin_problem_trims_recent_fingerprints(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    problem = {"problem_id": "p1", "question": "q", "correct": "1", "options": ["1"]}

    fingerprints = [f"fp-{index}" for index in range(config.MAX_RETRIES_DUPLICATE_CHECK + 3)]
    session.begin_problem(
        state, problem, fixture_curriculum, recent_fingerprints=fingerprints
    )

    assert len(state.recent_problem_fingerprints) == config.MAX_RETRIES_DUPLICATE_CHECK
    assert state.recent_problem_fingerprints == fingerprints[-config.MAX_RETRIES_DUPLICATE_CHECK :]


def test_begin_problem_resolves_input_mode_from_streak(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    problem = {"problem_id": "p1", "question": "q", "correct": "1", "options": ["1"]}

    state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    session.begin_problem(state, problem, fixture_curriculum)

    assert state.current_input_mode == "input"


# --- respond ---


def test_respond_attaches_navigation(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    response = session.respond(state, fixture_curriculum)

    assert response.navigation is not None
    assert len(response.navigation.available_chapters) > 0
    assert response.navigation.available_topics


def test_respond_serves_full_streak_meter_at_level_completion_feedback(
    fixture_curriculum: Curriculum,
):
    """While Level completion feedback is on screen, Streak meter stays full."""
    state = _fresh_state(fixture_curriculum)
    state.problem_answered = True
    state.level_completed = True
    state.streak = 0
    state.max_streak = 3

    response = session.respond(state, fixture_curriculum)

    assert response.streak_meter == 3
    assert "streak_meter" not in SessionState.model_fields


def test_respond_serves_streak_meter_equal_to_streak_outside_level_completion(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.problem_answered = True
    state.level_completed = False
    state.streak = 2
    state.max_streak = 3

    response = session.respond(state, fixture_curriculum)

    assert response.streak_meter == 2


def test_session_response_from_state_copies_shared_fields():
    state = SessionState(
        session_id="sid-1",
        username="alice",
        xp=100,
        streak=2,
        flawless_eligible=False,
        max_streak=5,
        selected_chapter_id=10,
        selected_topic_id=20,
        selected_level=3,
        problem_answered=True,
        current_input_mode="input",
        topic_completed=True,
        feedback_type="success",
        feedback_msg="Nice!",
        level_completed=True,
        chapter_frontiers={10: ChapterFrontier(frontier_topic_id=30, frontier_level=2)},
        problem_start_time=99.0,
        recent_problem_fingerprints=["fp1"],
    )
    derived_problem = {"problem_id": "p1", "question": "q?"}

    response = SessionResponse.from_state(
        state,
        current_problem=derived_problem,
        can_submit=False,
        can_next_problem=True,
        streak_meter=3,
        admin_mode=True,
        navigation=None,
    )

    assert response.session_id == "sid-1"
    assert response.username == "alice"
    assert response.xp == 100
    assert response.streak == 2
    assert response.flawless_eligible is False
    assert response.max_streak == 5
    assert response.selected_chapter_id == 10
    assert response.selected_topic_id == 20
    assert response.selected_level == 3
    assert response.problem_answered is True
    assert response.current_input_mode == "input"
    assert response.topic_completed is True
    assert response.feedback_type == "success"
    assert response.feedback_msg == "Nice!"
    assert response.level_completed is True
    assert response.chapter_frontiers == {10: ChapterFrontier(frontier_topic_id=30, frontier_level=2)}
    assert response.chapter_frontiers is not state.chapter_frontiers
    assert response.current_problem == derived_problem
    assert response.can_submit is False
    assert response.can_next_problem is True
    assert response.streak_meter == 3
    assert response.admin_mode is True
    assert response.navigation is None
    assert "problem_start_time" not in SessionResponse.model_fields
    assert "recent_problem_fingerprints" not in SessionResponse.model_fields


def test_respond_builds_unanswered_problem_payload_without_mutating_state(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.current_problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": "42",
        "options": ["41", "42"],
        "options_map": {"42": "correct"},
        "messages": {},
    }
    state.problem_answered = False
    state.problem_start_time = 123.0
    state.recent_problem_fingerprints = ["fp1"]

    response = session.respond(state, fixture_curriculum)

    assert isinstance(response, SessionResponse)
    assert not isinstance(state, SessionResponse)
    assert response.can_submit is True
    assert response.can_next_problem is False
    assert response.admin_mode is False
    assert not hasattr(response, "problem_start_time")
    assert not hasattr(response, "recent_problem_fingerprints")
    assert "problem_start_time" not in SessionResponse.model_fields
    assert "recent_problem_fingerprints" not in SessionResponse.model_fields
    assert response.current_problem is not None
    assert response.current_problem["answer_options"] == ["41", "42"]
    assert "correct_answer" not in response.current_problem
    assert "correct" not in response.current_problem
    assert "options_map" not in response.current_problem
    assert state.problem_start_time == 123.0
    assert state.recent_problem_fingerprints == ["fp1"]
    assert state.current_problem["correct"] == "42"
    assert "can_submit" not in SessionState.model_fields
    assert "can_next_problem" not in SessionState.model_fields
    assert "streak_meter" not in SessionState.model_fields
    assert "admin_mode" not in SessionState.model_fields
    assert "navigation" not in SessionState.model_fields
    assert not hasattr(SessionState, "for_response")


def test_respond_builds_answered_problem_payload(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.current_problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": "42",
        "options": ["42"],
    }
    state.problem_answered = True

    response = session.respond(state, fixture_curriculum)

    assert isinstance(response, SessionResponse)
    assert response.can_submit is False
    assert response.can_next_problem is True
    assert response.current_problem is not None
    assert response.current_problem["correct_answer"] == "42"


def test_respond_uses_passed_play_mode_for_admin_reveal(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.username = "not-an-admin"
    state.current_input_mode = "radio"
    state.problem_answered = False
    state.current_problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": "42",
        "options": ["41", "42"],
    }
    admin_mode = resolve_play_mode(next(iter(config.ADMIN_USERNAMES)))

    response = session.respond(state, fixture_curriculum, play_mode=admin_mode)

    assert isinstance(response, SessionResponse)
    assert response.admin_mode is True
    assert response.can_submit is True
    assert response.can_next_problem is False
    assert response.navigation is not None
    assert response.current_problem is not None
    assert response.current_problem["correct_answer"] == "42"


def test_legacy_stored_response_fields_load_and_serve_correct_payload(fixture_curriculum: Curriculum):
    """Old session rows with response-only fields still load and respond correctly."""
    state = _fresh_state(fixture_curriculum)
    state.current_problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": "42",
        "options": ["41", "42"],
    }
    state.problem_answered = False
    legacy = json.loads(state.to_storage())
    legacy.update(
        {
            "can_submit": False,
            "can_next_problem": True,
            "admin_mode": True,
            "navigation": None,
        }
    )
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, username, state_json, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (state.session_id, state.username, json.dumps(legacy)),
        )
        conn.commit()

    loaded = db.load_session(state.session_id)
    assert loaded is not None
    response = session.respond(loaded, fixture_curriculum)

    assert isinstance(response, SessionResponse)
    assert response.can_submit is True
    assert response.can_next_problem is False
    assert response.admin_mode is False
    assert response.current_problem is not None
    assert "correct_answer" not in response.current_problem


# --- public_problem ---


def test_public_problem_strips_unsafe_svg(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
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


def test_public_problem_includes_correct_answer_when_answered(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.problem_answered = True
    problem = {"problem_id": "p1", "question": "q", "correct": "42", "options": ["42"]}

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert public["correct_answer"] == "42"


def test_public_problem_includes_correct_answer_for_admin_before_answered(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.username = next(iter(config.ADMIN_USERNAMES))
    state.current_input_mode = "radio"
    problem = {"problem_id": "p1", "question": "q", "correct": "42", "options": ["41", "42"]}

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert public["correct_answer"] == "42"


def test_public_problem_hides_correct_answer_for_non_admin_before_answered(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.problem_answered = False
    problem = {"problem_id": "p1", "question": "q", "correct": "42", "options": ["42"]}

    public = session.public_problem(problem, state, resolve_play_mode(state.username))

    assert "correct_answer" not in public


def test_public_problem_includes_cleaned_correct_answer_for_admin_input_mode(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
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
    state: SessionState, problem: dict[str, object], curriculum: Curriculum
) -> None:
    session.begin_problem(state, problem, curriculum)
    session.ACTIVE_SESSIONS[state.session_id] = state


def test_manual_submit_and_auto_solve_produce_identical_state_deltas(fixture_curriculum: Curriculum):
    problem = {
        "problem_id": "p-parity",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }

    manual_state = _fresh_state(fixture_curriculum)
    manual_state.username = next(iter(config.ADMIN_USERNAMES))
    _begin_identical_problem(manual_state, dict(problem), fixture_curriculum)

    manual_response = session.submit_problem(
        ProblemSubmissionRequest(
            session_id=manual_state.session_id,
            problem_id="p-parity",
            user_input="2",
            is_input_mode=False,
        )
    )

    auto_state = _fresh_state(fixture_curriculum)
    auto_state.username = manual_state.username
    _begin_identical_problem(auto_state, dict(problem), fixture_curriculum)

    auto_response = session.auto_solve_problem(
        AutoSolveRequest(session_id=auto_state.session_id, problem_id="p-parity")
    )

    assert _submission_snapshot(manual_state) == _submission_snapshot(auto_state)
    assert manual_response.is_correct == auto_response.is_correct
    assert manual_response.feedback == auto_response.feedback


def test_manual_submit_and_auto_solve_match_in_input_mode(fixture_curriculum: Curriculum):
    problem = {
        "problem_id": "p-parity-input",
        "question": "q",
        "correct": r"\dfrac{3}{4}",
        "options": [],
        "options_map": {},
        "messages": {},
    }
    derived_input = clean_latex(problem["correct"])

    manual_state = _fresh_state(fixture_curriculum)
    manual_state.username = next(iter(config.ADMIN_USERNAMES))
    manual_state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    session.begin_problem(manual_state, dict(problem), fixture_curriculum)
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

    auto_state = _fresh_state(fixture_curriculum)
    auto_state.username = manual_state.username
    auto_state.streak = config.STREAK_THRESHOLD_FOR_INPUT_MODE
    session.begin_problem(auto_state, dict(problem), fixture_curriculum)
    session.ACTIVE_SESSIONS[auto_state.session_id] = auto_state

    auto_response = session.auto_solve_problem(
        AutoSolveRequest(
            session_id=auto_state.session_id, problem_id="p-parity-input"
        )
    )

    assert _submission_snapshot(manual_state) == _submission_snapshot(auto_state)
    assert manual_response.is_correct == auto_response.is_correct
    assert manual_response.feedback == auto_response.feedback


def test_admin_auto_solve_uses_flat_submission_rules(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
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
    session.begin_problem(state, problem, fixture_curriculum)
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


def test_admin_navigates_to_locked_topic_without_bypass(fixture_curriculum: Curriculum):
    state = _fresh_state(fixture_curriculum)
    state.username = next(iter(config.ADMIN_USERNAMES))
    session.ACTIVE_SESSIONS[state.session_id] = state
    state.chapter_frontiers[CHAPTER_ALPHA] = ChapterFrontier(
        frontier_topic_id=TOPIC_MULTI,
        frontier_level=1,
    )

    response = session.navigate_session(
        SessionNavigateRequest(
            session_id=state.session_id,
            selected_chapter_id=CHAPTER_ALPHA,
            selected_topic_id=TOPIC_RADIO,
            selected_level=1,
        )
    )

    assert response.selected_topic_id == TOPIC_RADIO
    assert response.selected_level == 1


# --- start_session ---


def test_start_session_returns_state_with_navigation():
    response = session.start_session(
        SessionStartRequest(username=f"user-{uuid.uuid4()}")
    )

    assert response.session_id
    assert response.navigation is not None
    assert response.session_id in session.ACTIVE_SESSIONS


def test_start_session_with_fixture_curriculum_lists_fixture_chapters(
    fixture_curriculum,
):
    """Provider override must reach the started session's navigation Chapters."""
    set_curriculum(fixture_curriculum)
    try:
        response = session.start_session(
            SessionStartRequest(username=f"user-{uuid.uuid4()}")
        )
    finally:
        set_curriculum(None)

    chapter_ids = [c.chapter_id for c in response.navigation.available_chapters]
    assert chapter_ids == [CHAPTER_ALPHA, CHAPTER_BETA]
    assert all(c.name != "Ułamki Zwykłe" for c in response.navigation.available_chapters)



def test_start_next_submit_cycle_with_fixture_curriculum(
    fixture_curriculum, monkeypatch
):
    """Full start → next problem → submit runs on the fixture Curriculum only."""
    import backend.problem_generation as problem_generation

    def fake_multi_1():
        return {
            "question": r"\text{fixture e2e}",
            "correct": "1",
            "options": ["1", "2", "3", "4"],
            "options_map": {"1": "correct", "2": "t1", "3": "t2", "4": "t3"},
        }

    monkeypatch.setitem(
        problem_generation.FUNCTION_REGISTRY, "fixture_multi_1", fake_multi_1
    )
    set_curriculum(fixture_curriculum)
    try:
        started = session.start_session(
            SessionStartRequest(username=f"user-{uuid.uuid4()}")
        )
        problem_response = session.next_problem(started.session_id)
        submission = session.submit_problem(
            ProblemSubmissionRequest(
                session_id=started.session_id,
                problem_id=problem_response.problem["problem_id"],
                user_input="1",
                is_input_mode=False,
            )
        )
    finally:
        set_curriculum(None)

    assert problem_response.problem["question"] == r"\text{fixture e2e}"
    assert problem_response.state.selected_chapter_id == CHAPTER_ALPHA
    assert submission.is_correct is True
    assert submission.state.streak == 1


def test_start_session_raises_for_unknown_chapter():
    with pytest.raises(session.SessionError) as exc_info:
        session.start_session(
            SessionStartRequest(username="user", selected_chapter_id=99999)
        )
    assert exc_info.value.status_code == 400
    assert "not found" in exc_info.value.detail
