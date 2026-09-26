"""FastAPI integration tests for session flow, grading, and API contract."""

import asyncio
import json
import sqlite3
import uuid

import pytest
from fastapi import HTTPException

import backend.config as config
import backend.main as main
import backend.session as session
import backend.submission as submission
from backend.answer_grading import grade
from backend.core import db
from backend.curriculum import resolve_curriculum
from backend.deconstruction import build_steps
from backend.models import (
    ChapterFrontier,
    DeconstructionState,
    DeconstructionStep,
    SessionState,
)
from backend.play_mode import AdminPlayMode, StudentPlayMode
from backend.step_grading import ORDERING_ANSWER_SEPARATOR


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def isolated_state(isolated_db):
    main.ACTIVE_SESSIONS.clear()
    yield
    main.ACTIVE_SESSIONS.clear()


def make_state(
    problem,
    *,
    streak=0,
    input_mode="radio",
    selected_topic_id=None,
    selected_level=1,
    frontier_topic_id=None,
    frontier_level=1,
    play_mode=StudentPlayMode(),
):
    """Build a SessionState with an active problem and register it in ACTIVE_SESSIONS.

    A ``frontier_topic_id`` replaces the seeded Chapter Frontier before the profile
    is persisted, so the stored profile holds that Frontier too. ``play_mode``
    picks the Username the profile is written under, and the mode it is written
    through — see `make_admin_state`.
    """
    curriculum = resolve_curriculum()
    chapter_ids = list(curriculum.chapter_ids())
    chapter_id = chapter_ids[0]
    if selected_topic_id is None:
        selected_topic_id = int(curriculum.topics(chapter_id)[0]["topic_id"])
    session_id = str(uuid.uuid4())
    state = SessionState()
    main.session_state.init_defaults(state, curriculum)
    state.session_id = session_id
    if play_mode.is_admin:
        state.username = next(iter(config.ADMIN_USERNAMES))
    else:
        state.username = f"test-{session_id}"
    state.selected_chapter_id = chapter_id
    state.selected_topic_id = selected_topic_id
    state.selected_level = selected_level
    state.streak = streak
    state.current_input_mode = input_mode
    state.problem_answered = False
    state.current_problem = problem
    state.problem_start_time = 0
    if frontier_topic_id is not None:
        state.chapter_frontiers[chapter_id] = ChapterFrontier(
            frontier_topic_id=frontier_topic_id,
            frontier_level=frontier_level,
        )
    main.ACTIVE_SESSIONS[session_id] = state
    main.session_state.persist(state, play_mode)
    return state


def make_admin_state(problem, *, selected_topic_id, selected_level=1, streak=0):
    """Build an Admin SessionState with an active problem, via `make_state`.

    Leaves the seeded Chapter Frontier at its default (first Topic, Level 1), so
    a ``selected_topic_id``/``selected_level`` elsewhere in the Chapter is "away
    from the Admin's stored Frontier" without any extra setup — Admin mode never
    reads that record for progression (ADR-0013).
    """
    return make_state(
        problem,
        streak=streak,
        selected_topic_id=selected_topic_id,
        selected_level=selected_level,
        play_mode=AdminPlayMode(),
    )


# Every (method, path) pair `frontend/lib/session/httpSessionClient.ts` hardcodes.
# Keep this list in step with that file — it is the pair's other half.
FRONTEND_HARDCODED_ROUTES = {
    ("POST", "/session/start"),
    ("POST", "/session/navigate"),
    ("POST", "/session/reset"),
    ("GET", "/problem/next"),
    ("POST", "/problem/submit"),
    ("GET", "/deconstruction/next"),
    ("POST", "/deconstruction/submit"),
    ("POST", "/deconstruction/abandon"),
}


def test_route_table_contains_every_frontend_hardcoded_path():
    """Issue #354: the frontend's session client hardcodes routes, and nothing
    else pins them against the running app — a rename here would leave both
    the frontend's mocked-client tests and this suite's coroutine-level tests
    green while the deployed app breaks."""
    app_routes = {
        (method, route.path)
        for route in main.app.routes
        for method in getattr(route, "methods", set())
    }

    assert FRONTEND_HARDCODED_ROUTES <= app_routes


def test_wrong_radio_submit_reveals_correct_answer():
    problem = {
        "problem_id": "p-radio-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {"t1": "Try again"},
    }
    state = make_state(problem, input_mode="radio")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-radio-wrong",
                user_input="3",
            )
        )
    )

    assert response.is_correct is False
    revealed = response.state.current_problem
    assert revealed is not None
    assert revealed["correct_answer"] == "2"
    assert "correct" not in revealed
    assert "options_map" not in revealed


def test_wrong_unit_submit_reveals_a_united_answer_that_then_grades_correct():
    """Issue #290: a Student who omits the Unit sees a revealed answer that
    carries the Unit, and retyping exactly what was revealed grades Correct —
    the reveal and the grader must never contradict each other."""
    problem = {
        "problem_id": "p-unit-reveal",
        "question": "q",
        "correct": "84",
        "expected_unit": "cm²",
    }
    state = make_state(problem, input_mode="typing")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-unit-reveal",
                user_input="84",
            )
        )
    )

    assert response.is_correct is False
    revealed = response.state.current_problem
    assert revealed is not None
    assert revealed["correct_answer"] == "84 cm²"

    retyped = grade(revealed["correct_answer"], problem, input_mode="typing")

    assert retyped.get("answer_outcome") == "correct"


def test_wrong_text_submit_reveals_correct_answer():
    problem = {
        "problem_id": "p-text-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="typing")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-text-wrong",
                user_input="99",
            )
        )
    )

    assert response.is_correct is False
    revealed = response.state.current_problem
    assert revealed is not None
    assert revealed["correct_answer"] == "2"
    assert "correct" not in revealed
    assert "options_map" not in revealed


def test_next_problem_hides_answer_contract_fields():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="contract-user", selected_chapter_id=None)
        )
    )

    response = run(main.problem_next(state.session_id))
    problem = response.problem

    assert "answer_options" in problem
    assert "correct" not in problem
    assert "options_map" not in problem
    assert "messages" not in problem
    assert response.state.can_submit is True


def test_typing_submit_uses_mobile_sanitizer_and_keeps_typing_mode():
    problem = {
        "problem_id": "p-mobile",
        "question": "q",
        "correct": "1 \\frac{1}{2}",
        "options": ["1 \\frac{1}{2}", "1", "2"],
        "options_map": {"1 \\frac{1}{2}": "correct", "1": "t1", "2": "w2"},
        "messages": {},
    }
    state = make_state(problem, input_mode="typing")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-mobile",
                user_input="1-1/2",
            )
        )
    )

    assert response.is_correct is True
    assert response.state.streak == 1
    assert response.state.current_input_mode == "typing"


def test_level_completing_submit_serves_full_streak_meter():
    problem = {
        "problem_id": "p-level-complete",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(problem, streak=2, input_mode="typing")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-level-complete",
                user_input="2",
            )
        )
    )

    assert response.is_correct is True
    assert response.state.level_completed is True
    assert response.state.problem_answered is True
    assert response.state.streak == 0
    assert response.state.streak_meter == 3


def test_non_completing_submit_serves_streak_meter_equal_to_streak():
    problem = {
        "problem_id": "p-streak-meter",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(problem, streak=1, input_mode="typing")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-streak-meter",
                user_input="2",
            )
        )
    )

    assert response.is_correct is True
    assert response.state.level_completed is False
    assert response.state.streak == 2
    assert response.state.streak_meter == 2


def test_replay_at_frontier_level_but_behind_frontier_topic_does_not_move_frontier():
    """#300: a Replay whose Level equals the Frontier Level must not move the Frontier."""
    chapter_id = 10
    # The scenario only exercises #300 if Topic 30 sits one Topic behind Topic 40
    # and both Topics reach Level 2.
    curriculum = resolve_curriculum()
    chapter_topic_ids = [int(t["topic_id"]) for t in curriculum.topics(chapter_id)]
    assert curriculum.topic_by_id(chapter_id, 30)["max_level"] == 2
    assert chapter_topic_ids[chapter_topic_ids.index(30) + 1] == 40
    assert curriculum.topic_by_id(chapter_id, 40)["max_level"] >= 2

    problem = {
        "problem_id": "p-replay-regression",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(
        problem,
        streak=2,
        input_mode="typing",
        selected_topic_id=30,
        selected_level=2,
        frontier_topic_id=40,
        frontier_level=2,
    )
    xp_before = state.xp

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-replay-regression",
                user_input="2",
            )
        )
    )

    assert response.is_correct is True
    frontier = response.state.chapter_frontiers[chapter_id]
    assert frontier.frontier_topic_id == 40
    assert frontier.frontier_level == 2
    assert response.state.level_completed is False
    assert response.state.topic_completed is False
    assert response.state.streak == 3
    assert response.state.streak_meter == 3
    assert response.state.selected_topic_id == 30
    assert response.state.selected_level == 2
    assert response.state.xp - xp_before == config.XP_REWARDS[2]
    assert "Flawless Bonus" not in response.state.feedback_msg

    persisted_frontier = db.load_user(state.username)["chapter_frontiers"][chapter_id]
    assert persisted_frontier.frontier_topic_id == 40
    assert persisted_frontier.frontier_level == 2

    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.selected_topic_id == 30


def test_replay_at_frontier_level_but_behind_frontier_topic_does_not_unlock_next_level():
    """#300: a Replay must not unlock a Level of a Frontier Topic never played yet."""
    chapter_id = 10
    problem = {
        "problem_id": "p-replay-unearned",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(
        problem,
        streak=2,
        input_mode="typing",
        selected_topic_id=30,
        selected_level=1,
        frontier_topic_id=40,
        frontier_level=1,
    )
    xp_before = state.xp

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-replay-unearned",
                user_input="2",
            )
        )
    )

    assert response.is_correct is True
    frontier = response.state.chapter_frontiers[chapter_id]
    assert frontier.frontier_topic_id == 40
    assert frontier.frontier_level == 1
    assert response.state.level_completed is False
    assert response.state.topic_completed is False
    assert response.state.streak == 3
    assert response.state.selected_level == 1
    assert response.state.xp - xp_before == config.XP_REWARDS[1]

    persisted_frontier = db.load_user(state.username)["chapter_frontiers"][chapter_id]
    assert persisted_frontier.frontier_topic_id == 40
    assert persisted_frontier.frontier_level == 1


def test_admin_mirrors_student_progression_end_to_end():
    """#333: an Admin QAing any Topic and Level sees exactly what a Student At
    the Frontier sees, wherever they are in the Curriculum — Admin's answer to
    "At the Frontier?" is unconditional (ADR-0013)."""
    chapter_id = 10
    # Topic 30 (max_level 2) sits one Topic ahead of Topic 40 in the real
    # Curriculum — see the Replay regression tests above for the same pair.
    curriculum = resolve_curriculum()
    assert curriculum.topic_by_id(chapter_id, 30)["max_level"] == 2
    last_topic_id = int(curriculum.topics(chapter_id)[-1]["topic_id"])
    assert last_topic_id != 40

    correct_problem = {
        "problem_id": "p-admin-mirror-correct",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    trap_problem = {
        "problem_id": "p-admin-mirror-trap",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {"t1": "Try again"},
    }

    # Selected Topic/Level (30, 2) is away from the Admin's stored Frontier,
    # which `make_admin_state` leaves seeded at the Chapter's first Topic.
    state = make_admin_state(
        correct_problem, streak=2, selected_topic_id=30, selected_level=1
    )
    username = state.username

    # --- Level completion: full stars, XP + Flawless bonus, Selected level up ---
    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-admin-mirror-correct",
                user_input="2",
            )
        )
    )

    assert response.is_correct is True
    assert response.state.streak_meter == 3
    assert response.state.level_completed is True
    expected_xp = config.XP_REWARDS[1] + config.FLAWLESS_LEVEL_BONUS
    assert response.state.xp == expected_xp
    assert f"+{config.XP_REWARDS[1]} XP" in response.state.feedback_msg
    assert "Flawless Bonus" in response.state.feedback_msg
    assert response.state.selected_level == 2

    # --- A penalized mistake forfeits the Flawless badge ---
    state.current_problem = trap_problem
    state.problem_answered = False
    wrong_response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-admin-mirror-trap",
                user_input="3",
            )
        )
    )
    assert wrong_response.is_correct is False
    assert wrong_response.state.flawless_eligible is False

    # --- Topic completion: last Level of the Topic, no Flawless bonus this time ---
    state.current_problem = correct_problem
    state.problem_answered = False
    state.streak = 2
    final_response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-admin-mirror-correct",
                user_input="2",
            )
        )
    )

    assert final_response.is_correct is True
    assert final_response.state.level_completed is True
    assert final_response.state.topic_completed is True
    assert final_response.state.xp == expected_xp + config.XP_REWARDS[2]
    assert "Flawless Bonus" not in final_response.state.feedback_msg

    # --- Next problem lands on the next Topic in the Chapter — not the last ---
    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.selected_topic_id == 40
    assert next_response.state.selected_topic_id != last_topic_id

    # --- None of it reached the profile ---
    loaded = db.load_user(username)
    assert loaded is not None
    assert loaded["xp"] == 0
    seeded_frontier = loaded["chapter_frontiers"][chapter_id]
    assert seeded_frontier.frontier_topic_id == 10
    assert seeded_frontier.frontier_level == 1


def test_input_mode_defers_radio_to_typing_until_next_problem():
    problem = {
        "problem_id": "p-radio-defer",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(problem, streak=0, input_mode="radio")

    submit_response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-radio-defer",
                user_input="2",
            )
        )
    )

    assert submit_response.is_correct is True
    assert submit_response.state.streak == 1
    assert submit_response.state.current_input_mode == "radio"

    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.current_input_mode == "typing"
    assert "input_mode" not in next_response.problem


def test_input_mode_defers_typing_to_radio_until_next_problem():
    problem = {
        "problem_id": "p-text-defer",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(problem, streak=1, input_mode="typing")

    submit_response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-text-defer",
                user_input="3",
            )
        )
    )

    assert submit_response.is_correct is False
    assert submit_response.state.streak == 0
    assert submit_response.state.current_input_mode == "typing"

    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.current_input_mode == "radio"
    assert "input_mode" not in next_response.problem


def test_soft_syntax_error_does_not_lock_problem_or_forfeit_flawless():
    problem = {
        "problem_id": "p-soft",
        "question": "q",
        "correct": "3/4",
        "options": ["3/4", "1/2"],
        "options_map": {"3/4": "correct", "1/2": "t1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="typing")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-soft",
                user_input="abc",
            )
        )
    )

    assert response.is_correct is False
    assert response.state.problem_answered is False
    assert response.state.can_submit is True
    assert response.state.flawless_eligible is True


def test_unsimplified_fraction_preserves_flawless_eligible():
    problem = {
        "problem_id": "p-unsimplified",
        "question": "q",
        "correct": "1/2",
        "options": ["1/2", "2/4"],
        "options_map": {"1/2": "correct", "2/4": "t1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="typing")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-unsimplified",
                user_input="2/4",
            )
        )
    )

    assert response.is_correct is False
    assert response.state.flawless_eligible is True


def test_wrong_answer_forfeits_flawless_eligible():
    problem = {
        "problem_id": "p-flawless-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(problem)

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-flawless-wrong",
                user_input="3",
            )
        )
    )

    assert response.is_correct is False
    assert response.state.flawless_eligible is False


def test_stale_and_duplicate_submissions_are_rejected():
    problem = {
        "problem_id": "p-lock",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {},
    }
    state = make_state(problem)

    with pytest.raises(HTTPException) as stale:
        run(
            main.problem_submit(
                main.ProblemSubmissionRequest(
                    session_id=state.session_id,
                    problem_id="wrong-id",
                    user_input="2",
                )
            )
        )
    assert stale.value.status_code == 409

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-lock",
                user_input="2",
            )
        )
    )

    with pytest.raises(HTTPException) as duplicate:
        run(
            main.problem_submit(
                main.ProblemSubmissionRequest(
                    session_id=state.session_id,
                    problem_id="p-lock",
                    user_input="2",
                )
            )
        )
    assert duplicate.value.status_code == 409


def test_locked_navigation_is_rejected():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="locked-user", selected_chapter_id=None)
        )
    )
    chapter_id = state.selected_chapter_id
    assert chapter_id is not None
    chapter_topics = resolve_curriculum().topics(chapter_id)
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics for locked navigation test")

    locked_topic_id = int(chapter_topics[1]["topic_id"])
    with pytest.raises(HTTPException) as exc:
        run(
            main.session_navigate(
                main.SessionNavigateRequest(
                    session_id=state.session_id,
                    selected_chapter_id=chapter_id,
                    selected_topic_id=locked_topic_id,
                    selected_level=1,
                )
            )
        )

    assert exc.value.status_code == 403


def test_accepted_navigation_toolbar_agrees_with_target():
    """The value that validates a Navigation intent and the value that renders the
    toolbar in the same response must agree: an accepted target must show up as
    Selected and Reachable in that response, not just accepted."""
    import backend.config as config

    admin_username = next(iter(config.ADMIN_USERNAMES))
    state = run(main.session_start(main.SessionStartRequest(username=admin_username)))
    chapter_id = state.selected_chapter_id
    assert chapter_id is not None
    chapter_topics = resolve_curriculum().topics(chapter_id)
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics for navigation agreement test")

    target_topic_id = int(chapter_topics[1]["topic_id"])

    response = run(
        main.session_navigate(
            main.SessionNavigateRequest(
                session_id=state.session_id,
                selected_chapter_id=chapter_id,
                selected_topic_id=target_topic_id,
                selected_level=1,
            )
        )
    )

    assert response.selected_topic_id == target_topic_id
    assert response.navigation is not None
    available_topic_ids = [t.topic_id for t in response.navigation.available_topics]
    assert target_topic_id in available_topic_ids


def test_start_session_admin_and_student_diverge_on_effective_frontier(
    fixture_curriculum,
):
    """An admin's effective full unlock must apply from the first served state,
    never a Student-mode default carried over from an unresolved play mode."""
    import backend.config as config
    from backend.curriculum import set_curriculum
    from tests.support.fixture_curriculum import CHAPTER_ALPHA, TOPIC_MULTI, TOPIC_RADIO

    set_curriculum(fixture_curriculum)
    try:
        admin_username = next(iter(config.ADMIN_USERNAMES))
        admin_response = run(
            main.session_start(main.SessionStartRequest(username=admin_username))
        )
        student_response = run(
            main.session_start(
                main.SessionStartRequest(username=f"student-{uuid.uuid4()}")
            )
        )
    finally:
        set_curriculum(None)

    assert admin_response.selected_chapter_id == CHAPTER_ALPHA
    assert student_response.selected_chapter_id == CHAPTER_ALPHA

    assert admin_response.admin_mode is True
    admin_topic_ids = {
        topic.topic_id for topic in admin_response.navigation.available_topics
    }
    assert admin_topic_ids == {TOPIC_MULTI, TOPIC_RADIO}

    assert student_response.admin_mode is False
    student_topic_ids = {
        topic.topic_id for topic in student_response.navigation.available_topics
    }
    assert student_topic_ids == {TOPIC_MULTI}


def test_radio_only_topic_keeps_radio_input():
    curriculum = resolve_curriculum()
    disabled_topic = None
    disabled_chapter_id = None
    for chapter_id_key in curriculum.chapter_ids():
        for topic_entry in curriculum.topics(chapter_id_key):
            if topic_entry.get("radio_only"):
                disabled_topic = topic_entry
                disabled_chapter_id = chapter_id_key
                break
        if disabled_topic:
            break

    if not disabled_topic:
        pytest.skip("No radio_only topic in curriculum")

    assert disabled_chapter_id is not None

    problem = {
        "problem_id": "p-radio-only",
        "question": "q",
        "correct": disabled_topic["name"],
        "options": ["a", "b"],
        "options_map": {"a": "correct", "b": "t1"},
        "messages": {},
    }
    state = make_state(problem, streak=0, input_mode="radio")
    state.selected_chapter_id = disabled_chapter_id
    state.selected_topic_id = disabled_topic["topic_id"]
    submission.run_submission_cycle(
        state, problem, "a", "radio", resolve_curriculum(), StudentPlayMode()
    )

    assert state.streak == 1
    assert state.current_input_mode == "radio"


def _make_problem_next_state():
    """Register a session selected at the first chapter/topic on Level 1, no active problem."""
    curriculum = resolve_curriculum()
    chapter_id = list(curriculum.chapter_ids())[0]
    topic_entry = curriculum.topics(chapter_id)[0]
    session_id = str(uuid.uuid4())
    state = SessionState()
    main.session_state.init_defaults(state, curriculum)
    state.session_id = session_id
    state.username = f"test-{session_id}"
    state.selected_chapter_id = chapter_id
    state.selected_topic_id = int(topic_entry["topic_id"])
    state.selected_level = 1
    main.ACTIVE_SESSIONS[session_id] = state
    return state


def _make_generated_problem(question, problem_id=None):
    """Build a minimal generated problem whose fingerprint varies only with ``question``."""
    return {
        "problem_id": problem_id or question,
        "question": question,
        "correct": "1",
        "options": ["1", "2"],
        "options_map": {"1": "correct", "2": "t1"},
        "messages": {},
        "level": 1,
        "level_name": "Test",
        "level_display": "Test (Lvl 1)",
        "keyboard_type": "default",
    }


def test_problem_next_avoids_recent_duplicate_instances(monkeypatch):
    """Serving retries generation while the candidate's fingerprint sits in the recent window."""
    import backend.problem_generation as problem_generation
    import backend.submission_cycle as submission_cycle

    state = _make_problem_next_state()
    duplicate_problem = _make_generated_problem("same question", problem_id="dup-1")
    duplicate_fingerprint = problem_generation.problem_fingerprint(duplicate_problem)
    state.recent_problem_fingerprints = [duplicate_fingerprint]

    unique_problem = _make_generated_problem(
        "different question", problem_id="unique-1"
    )
    call_count = {"value": 0}

    def fake_generate_with_unique_second(_curriculum, _chapter_id, _topic_id, _level):
        call_count["value"] += 1
        if call_count["value"] == 1:
            return {
                **duplicate_problem,
                "problem_id": "dup-attempt",
            }
        return unique_problem

    monkeypatch.setattr(
        submission_cycle, "generate_level_problem", fake_generate_with_unique_second
    )

    response = run(main.problem_next(state.session_id))

    assert call_count["value"] == 2
    assert response.problem["question"] == "different question"
    assert duplicate_fingerprint in state.recent_problem_fingerprints
    assert (
        problem_generation.problem_fingerprint(unique_problem)
        in state.recent_problem_fingerprints
    )


def test_problem_next_rotates_window_when_every_retry_collides(monkeypatch):
    """A full fingerprint window keeps rotating even when no candidate is fresh.

    Regression test for #316: the served fingerprint used to be appended only on
    the "found something new" path, so once every retry collided the window froze
    forever and dedupe silently turned off.
    """
    import backend.problem_generation as problem_generation
    import backend.submission_cycle as submission_cycle

    state = _make_problem_next_state()
    window_fingerprints = [
        problem_generation.problem_fingerprint(_make_generated_problem(f"q{index}"))
        for index in range(config.RECENT_FINGERPRINT_HISTORY_SIZE)
    ]
    state.recent_problem_fingerprints = list(window_fingerprints)

    colliding_problem = _make_generated_problem("q0")
    colliding_fingerprint = problem_generation.problem_fingerprint(colliding_problem)
    assert colliding_fingerprint == window_fingerprints[0]

    def fake_generate_always_colliding(_curriculum, _chapter_id, _topic_id, _level):
        return dict(colliding_problem)

    monkeypatch.setattr(
        submission_cycle, "generate_level_problem", fake_generate_always_colliding
    )

    run(main.problem_next(state.session_id))

    assert state.recent_problem_fingerprints == [
        *window_fingerprints[1:],
        colliding_fingerprint,
    ]


def _make_topic_completed_state(
    *,
    chapter_id: int,
    completed_topic_id: int,
    completed_level: int,
    frontier_topic_id: int,
    frontier_level: int = 1,
) -> SessionState:
    """Build a session ready for next problem after topic completion."""
    curriculum = resolve_curriculum()
    session_id = str(uuid.uuid4())
    state = SessionState()
    main.session_state.init_defaults(state, curriculum)
    state.session_id = session_id
    state.username = f"test-{session_id}"
    state.selected_chapter_id = chapter_id
    state.selected_topic_id = completed_topic_id
    state.selected_level = completed_level
    state.problem_answered = True
    state.topic_completed = True
    state.level_completed = True
    state.feedback_type = "success"
    state.feedback_msg = "Topic complete!"
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=frontier_topic_id,
        frontier_level=frontier_level,
    )
    state.current_problem = {
        "problem_id": "p-topic-complete",
        "question": "q",
        "correct": "1",
        "options": ["1", "2"],
        "options_map": {"1": "correct", "2": "t1"},
        "messages": {},
    }
    state.problem_start_time = 0
    main.ACTIVE_SESSIONS[session_id] = state
    main.session_state.persist(state, StudentPlayMode())
    return state


def test_next_problem_moves_to_frontier_topic_after_topic_completion():
    state = _make_topic_completed_state(
        chapter_id=10,
        completed_topic_id=10,
        completed_level=1,
        frontier_topic_id=20,
    )

    response = run(main.problem_next(state.session_id))

    assert response.state.selected_topic_id == 20
    assert response.state.selected_level == 1
    assert response.state.topic_completed is False
    assert response.state.level_completed is False
    assert response.state.problem_answered is False
    assert response.state.can_submit is True
    assert response.problem["problem_id"]
    assert response.state.navigation is not None


def test_next_problem_reachable_set_includes_topic_unlocked_by_completion():
    """The Navigation snapshot behind Next problem's response must be built after
    auto-navigation moves the Session, not before — otherwise the just-unlocked
    Topic would be missing from the toolbar it renders in the same response."""
    state = _make_topic_completed_state(
        chapter_id=10,
        completed_topic_id=10,
        completed_level=1,
        frontier_topic_id=20,
    )

    response = run(main.problem_next(state.session_id))

    assert response.state.navigation is not None
    available_topic_ids = [
        t.topic_id for t in response.state.navigation.available_topics
    ]
    assert available_topic_ids.count(20) == 1


def test_next_problem_serves_unlocked_level_within_topic():
    curriculum = resolve_curriculum()
    chapter_id = 10
    topic_id = 20
    session_id = str(uuid.uuid4())
    state = SessionState()
    main.session_state.init_defaults(state, curriculum)
    state.session_id = session_id
    state.username = f"test-{session_id}"
    state.selected_chapter_id = chapter_id
    state.selected_topic_id = topic_id
    state.selected_level = 2
    state.problem_answered = True
    state.topic_completed = False
    state.level_completed = True
    state.chapter_frontiers[chapter_id] = ChapterFrontier(
        frontier_topic_id=topic_id,
        frontier_level=2,
    )
    state.current_problem = {
        "problem_id": "p-level-unlock",
        "question": "q",
        "correct": "1",
        "options": ["1", "2"],
        "options_map": {"1": "correct", "2": "t1"},
        "messages": {},
    }
    state.problem_start_time = 0
    main.ACTIVE_SESSIONS[session_id] = state

    response = run(main.problem_next(session_id))

    assert response.state.selected_topic_id == topic_id
    assert response.state.selected_level == 2
    assert response.state.topic_completed is False
    assert response.state.level_completed is False
    assert response.state.can_submit is True
    assert response.problem["level"] == 2


def test_next_problem_at_chapter_end_returns_without_error():
    curriculum = resolve_curriculum()
    chapter_id = 10
    last_topic = curriculum.topics(chapter_id)[-1]
    last_topic_id = int(last_topic["topic_id"])
    last_level = int(last_topic["max_level"])
    state = _make_topic_completed_state(
        chapter_id=chapter_id,
        completed_topic_id=last_topic_id,
        completed_level=last_level,
        frontier_topic_id=last_topic_id,
        frontier_level=last_level,
    )

    response = run(main.problem_next(state.session_id))

    assert response.state.selected_topic_id == last_topic_id
    assert response.state.selected_level == last_level
    assert response.state.topic_completed is True
    assert response.state.can_next_problem is True
    assert response.state.navigation is not None
    assert response.state.navigation.has_next_unlocked_topic is False
    assert response.problem["problem_id"] == "p-topic-complete"


def test_next_problem_after_topic_completion_reports_empty_streak_meter():
    state = _make_topic_completed_state(
        chapter_id=10,
        completed_topic_id=10,
        completed_level=1,
        frontier_topic_id=20,
    )

    response = run(main.problem_next(state.session_id))

    assert response.state.selected_topic_id == 20
    assert response.state.streak == 0
    assert response.state.streak_meter == 0


def test_wrong_submit_after_topic_completion_does_not_refire_navigation():
    state = _make_topic_completed_state(
        chapter_id=10,
        completed_topic_id=10,
        completed_level=1,
        frontier_topic_id=20,
    )

    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.selected_topic_id == 20
    assert next_response.state.topic_completed is False

    active_state = main.ACTIVE_SESSIONS[state.session_id]
    served_problem = active_state.current_problem
    correct = served_problem["correct"]
    wrong_option = next(
        option for option in served_problem["options"] if option != correct
    )

    submit_response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id=served_problem["problem_id"],
                user_input=wrong_option,
            )
        )
    )

    assert submit_response.is_correct is False
    assert submit_response.state.topic_completed is False
    assert submit_response.state.selected_chapter_id == 10
    assert submit_response.state.selected_topic_id == 20


def test_generator_messages_override_yaml_traps(monkeypatch):
    from backend.core.utils import build_problem_dict
    import backend.problem_generation as problem_generation
    from backend.answer_grading import grade

    branch_message = "branch-specific trap feedback"

    def fake_compare():
        problem = build_problem_dict(
            r"\text{q}",
            "<",
            traps={
                "compares_by_the_lower_place_digit": ">",
                "reads_unequal_decimals_as_equal": "=",
            },
            parameters={},
        )
        assert problem is not None
        problem["messages"] = {"compares_by_the_lower_place_digit": branch_message}
        return problem

    monkeypatch.setitem(
        problem_generation.FUNCTION_REGISTRY, "dec_compare_1", fake_compare
    )

    from backend.curriculum import resolve_curriculum

    problem = problem_generation.generate_level_problem(resolve_curriculum(), 20, 20, 1)
    assert problem is not None
    assert problem["messages"]["compares_by_the_lower_place_digit"] == branch_message
    assert (
        problem["messages"]["reads_unequal_decimals_as_equal"]
        == "Liczby nie są równe — nie wybieraj znaku równości!"
    )

    eval_result = grade(">", problem, input_mode="radio")
    assert eval_result.get("answer_outcome") == "trap"
    assert eval_result.get("trap_slug") == "compares_by_the_lower_place_digit"
    assert eval_result.get("feedback_msg") == branch_message


def test_start_session_survives_recovery_from_db():
    """A Session recovered from SQLite after the in-memory cache drops keeps its start clock."""
    response = run(
        main.session_start(
            main.SessionStartRequest(username=f"start-user-{uuid.uuid4()}")
        )
    )
    original_start_time = main.ACTIVE_SESSIONS[response.session_id].problem_start_time
    assert original_start_time is not None

    main.ACTIVE_SESSIONS.clear()
    recovered = session.get_session(response.session_id)

    assert recovered.problem_start_time == original_start_time


def test_start_next_submit_logs_time_spent_telemetry():
    """Submitting right after start and Next problem must log a populated time_spent field."""
    response = run(
        main.session_start(
            main.SessionStartRequest(username=f"start-user-{uuid.uuid4()}")
        )
    )
    problem_response = run(main.problem_next(response.session_id))
    answer = problem_response.problem["answer_options"][0]

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=response.session_id,
                problem_id=problem_response.problem["problem_id"],
                user_input=answer,
            )
        )
    )

    with sqlite3.connect(main.db.DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT time_spent_ms FROM telemetry_logs
            WHERE session_id = ?
            ORDER BY log_id DESC
            LIMIT 1
            """,
            (response.session_id,),
        ).fetchone()

    assert row is not None
    assert row[0] is not None


def test_parameters_never_reaches_public_problem_payload():
    """Issue #189: `parameters` is server-side only, withheld by public_problem's allowlist."""
    problem = {
        "problem_id": "p-parameters-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {"t1": "Try again"},
        "parameters": {"n": 1, "d": 2, "op": "+"},
    }
    state = make_state(problem, input_mode="radio")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-parameters-wrong",
                user_input="3",
            )
        )
    )

    revealed = response.state.current_problem
    assert revealed is not None
    assert "parameters" not in revealed


def test_submission_telemetry_records_parameters_when_present():
    """Issue #189: `parameters` rides through problem_snapshot, which strips nothing new."""
    problem = {
        "problem_id": "p-parameters-telemetry",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {"t1": "Try again"},
        "parameters": {"n": 1, "d": 2, "op": "+"},
    }
    state = make_state(problem, input_mode="radio")

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-parameters-telemetry",
                user_input="2",
            )
        )
    )

    with sqlite3.connect(main.db.DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT problem_snapshot FROM telemetry_logs
            WHERE session_id = ?
            ORDER BY log_id DESC
            LIMIT 1
            """,
            (state.session_id,),
        ).fetchone()

    assert row is not None
    assert row[0] is not None
    problem_snapshot = json.loads(row[0])
    assert problem_snapshot["parameters"] == {"n": 1, "d": 2, "op": "+"}


def _fetch_last_telemetry_row(session_id):
    with sqlite3.connect(main.db.DB_PATH) as conn:
        return conn.execute(
            """
            SELECT answer_outcome, misconception_slug, trap_slug, trap_source, problem_id
            FROM telemetry_logs
            WHERE session_id = ?
            ORDER BY log_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()


def test_mapped_trap_submission_writes_outcome_misconception_and_slug(monkeypatch):
    """Issue #188: a Trap whose slug maps to the catalogue writes trap + both new columns."""
    import dataclasses

    from backend.curriculum import Curriculum

    original_level_config = Curriculum.level_config

    def fake_level_config(self, chapter_id, topic_id, level):
        config = original_level_config(self, chapter_id, topic_id, level)
        if config is None:
            return config
        return dataclasses.replace(
            config,
            trap_misconceptions={
                **config.trap_misconceptions,
                "t1": "test_misconception",
            },
        )

    monkeypatch.setattr(Curriculum, "level_config", fake_level_config)

    problem = {
        "problem_id": "p-mapped-trap",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {"t1": "Try again"},
    }
    state = make_state(problem, input_mode="radio")

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-mapped-trap",
                user_input="3",
            )
        )
    )

    row = _fetch_last_telemetry_row(state.session_id)
    assert row == ("trap", "test_misconception", "t1", "authored", "p-mapped-trap")


def test_unmapped_trap_submission_writes_trap_slug_with_null_misconception():
    """Issue #188: a Trap whose slug is un-mapped writes trap + trap_slug + NULL misconception_slug."""
    problem = {
        "problem_id": "p-unmapped-trap",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "t1"},
        "messages": {"t1": "Try again"},
    }
    state = make_state(problem, input_mode="radio")

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-unmapped-trap",
                user_input="3",
            )
        )
    )

    row = _fetch_last_telemetry_row(state.session_id)
    assert row == ("trap", None, "t1", "authored", "p-unmapped-trap")


def test_filler_submission_writes_wrong_with_null_misconception_and_slug():
    """Issue #215: a Filler pick collapses into wrong + NULL misconception_slug + NULL trap_slug."""
    problem = {
        "problem_id": "p-filler",
        "question": "q",
        "correct": "2",
        "options": ["2", "3", "4"],
        "options_map": {"2": "correct", "3": "t1", "4": "filler"},
        "messages": {"t1": "Try again", "filler": "Nope"},
    }
    state = make_state(problem, input_mode="radio")

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-filler",
                user_input="4",
            )
        )
    )

    row = _fetch_last_telemetry_row(state.session_id)
    assert row == ("wrong", None, None, None, "p-filler")


def test_synthesized_unit_trap_writes_trap_source_synthesized():
    """Issue #257: a grader-synthesized Trap (ADR-0005 unit grading) writes
    trap_source=synthesized, distinguishing it from an authored Trap."""
    problem = {
        "problem_id": "p-wrong-dimension",
        "question": "q",
        "correct": "84",
        "expected_unit": "cm²",
    }
    state = make_state(problem, input_mode="typing")

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-wrong-dimension",
                user_input="84 cm",
            )
        )
    )

    row = _fetch_last_telemetry_row(state.session_id)
    assert row == (
        "trap",
        config.UNIT_DIMENSION_MISCONCEPTION,
        config.UNIT_DIMENSION_TRAP_SLUG,
        "synthesized",
        "p-wrong-dimension",
    )


def test_telemetry_problem_id_column_is_indexed():
    """Issue #188: problem_id is present on telemetry rows and is indexed."""
    with sqlite3.connect(main.db.DB_PATH) as conn:
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(telemetry_logs)")}
        index_columns = set()
        for index_name in indexes:
            index_columns.update(
                row[2] for row in conn.execute(f"PRAGMA index_info({index_name})")
            )

    assert "problem_id" in index_columns


# --- Deconstruction trigger (#194) ---

_UNLIKE_FRACTIONS_PARAMETERS = {"n1": 1, "d1": 2, "n2": 1, "d2": 3, "operation": "+"}
_UNLIKE_FRACTIONS_MISCONCEPTION = "operates_on_unlike_fractions_directly"


def _map_traps_to_misconceptions(monkeypatch, mapping):
    """Monkeypatch `Curriculum.level_config` so each trap slug maps to a Misconception."""
    import dataclasses

    from backend.curriculum import Curriculum

    original_level_config = Curriculum.level_config

    def fake_level_config(self, chapter_id, topic_id, level):
        cfg = original_level_config(self, chapter_id, topic_id, level)
        if cfg is None:
            return cfg
        return dataclasses.replace(
            cfg, trap_misconceptions={**cfg.trap_misconceptions, **mapping}
        )

    monkeypatch.setattr(Curriculum, "level_config", fake_level_config)


def _trap_problem(problem_id, *, trap_slug="t1", parameters=None):
    return {
        "problem_id": problem_id,
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": trap_slug},
        "messages": {trap_slug: "Try again"},
        "parameters": (
            _UNLIKE_FRACTIONS_PARAMETERS if parameters is None else parameters
        ),
    }


def _submit_trap(state, problem_id, *, trap_slug="t1", parameters=None):
    """Re-arm `state` with a fresh wrong-answer Problem and submit it, like a Next-problem cycle."""
    state.current_problem = _trap_problem(
        problem_id, trap_slug=trap_slug, parameters=parameters
    )
    state.problem_answered = False
    state.problem_start_time = 0
    return run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id=problem_id,
                user_input="3",
            )
        )
    )


def _fetch_last_deconstruction_row(session_id):
    with sqlite3.connect(main.db.DB_PATH) as conn:
        return conn.execute(
            """
            SELECT session_id, username, problem_id, misconception_slug,
                   chapter, topic, level_number, outcome
            FROM deconstructions
            WHERE session_id = ?
            ORDER BY deconstruction_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()


def test_first_hit_of_misconception_does_not_trigger_deconstruction(monkeypatch):
    """Issue #194: the first hit only grades normally — it does not arm a Deconstruction."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")

    _submit_trap(state, "p-first-hit")

    assert state.deconstruction is None
    assert _fetch_last_deconstruction_row(state.session_id) is None


def test_second_hit_of_same_misconception_triggers_deconstruction(monkeypatch):
    """Issue #194: the second hit of the same Misconception arms `state.deconstruction`
    with steps computed from the triggering Problem's `parameters`."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    assert state.deconstruction is None

    _submit_trap(state, "p-second-hit")

    assert state.deconstruction is not None
    assert state.deconstruction.misconception_slug == _UNLIKE_FRACTIONS_MISCONCEPTION
    assert state.deconstruction.step_index == 0
    assert state.deconstruction.step_attempts == 0
    assert state.deconstruction.step_revealed is False
    expected_steps = build_steps(
        _UNLIKE_FRACTIONS_MISCONCEPTION, _UNLIKE_FRACTIONS_PARAMETERS
    )
    assert [s.question for s in state.deconstruction.steps] == [
        s.question for s in expected_steps
    ]
    assert [s.working_line for s in state.deconstruction.steps] == [
        s.working_line for s in expected_steps
    ]
    assert [s.answer for s in state.deconstruction.steps] == [
        s.answer for s in expected_steps
    ]


def _topic_with_a_published_level(chapter_id, level, *, other_than=None):
    """First Topic id in `chapter_id` publishing `level`, skipping `other_than`."""
    curriculum = resolve_curriculum()
    for topic in curriculum.topics(chapter_id):
        topic_id = int(topic["topic_id"])
        if topic_id == other_than:
            continue
        if curriculum.level_config(chapter_id, topic_id, level) is not None:
            return topic_id
    return None


def test_two_hits_at_different_topics_triggers_deconstruction(monkeypatch):
    """Issue #340: the count is keyed on the Misconception slug alone — no
    Chapter, Topic or Level — so two hits anywhere in the Curriculum accumulate
    toward the same trigger."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    chapter_id = state.selected_chapter_id
    other_topic_id = _topic_with_a_published_level(
        chapter_id, 1, other_than=state.selected_topic_id
    )
    if other_topic_id is None:
        pytest.skip("Need a second Topic publishing Level 1")

    _submit_trap(state, "p-first-hit")
    assert state.deconstruction is None

    state.selected_topic_id = other_topic_id
    _submit_trap(state, "p-second-hit")

    assert state.deconstruction is not None
    assert state.deconstruction.misconception_slug == _UNLIKE_FRACTIONS_MISCONCEPTION


def test_contract_violation_skips_the_deconstruction_without_erroring(monkeypatch):
    """Issue #224: curriculum drift costs the Student help, never their Problem.

    `tests/test_deconstruction_contracts.py` is what keeps this from happening; this
    is what happens if it ever does anyway. The Submission grades normally, the Trap's
    own prose still fires, the request does not error, and nothing is written to
    `deconstructions` — so telemetry never shows a Deconstruction that never ran.
    """
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    incomplete = {"n1": 1, "d1": 2, "n2": 1, "d2": 3}  # no `operation`
    state = make_state(
        _trap_problem("p-first-hit", parameters=incomplete), input_mode="radio"
    )
    _submit_trap(state, "p-first-hit", parameters=incomplete)

    response = _submit_trap(state, "p-second-hit", parameters=incomplete)

    assert state.deconstruction is None
    assert response.state.deconstruction_running is False
    assert response.state.feedback_msg == "Try again"
    assert _fetch_last_deconstruction_row(state.session_id) is None


def test_repeated_failure_across_different_misconceptions_does_not_trigger(monkeypatch):
    """Issue #194: generic repeated failure — different Misconceptions — is not a trigger."""
    _map_traps_to_misconceptions(
        monkeypatch, {"t1": "misconception_a", "w2": "misconception_b"}
    )
    state = make_state(_trap_problem("p-a", trap_slug="t1"), input_mode="radio")

    _submit_trap(state, "p-a", trap_slug="t1")
    _submit_trap(state, "p-b", trap_slug="w2")

    assert state.deconstruction is None


def test_misconception_without_walkthrough_does_not_trigger_or_crash(monkeypatch):
    """Only a Misconception with an authored walkthrough can ever fire a Deconstruction —
    hitting the threshold on one of the other 50 must not raise."""
    _map_traps_to_misconceptions(
        monkeypatch, {"t1": "misconception_without_walkthrough"}
    )
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")

    _submit_trap(state, "p-second-hit")

    assert state.deconstruction is None


def test_trigger_count_is_config_tunable(monkeypatch):
    """Issue #194: the trigger count is read from config, beside MAX_STREAK."""
    monkeypatch.setattr(config, "DECONSTRUCTION_TRIGGER_COUNT", 1)
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-only-hit"), input_mode="radio")

    _submit_trap(state, "p-only-hit")

    assert state.deconstruction is not None


def test_triggering_submission_grades_streak_xp_flawless_normally(monkeypatch):
    """Issue #194: the triggering Submission is graded exactly like any other wrong Trap."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), streak=2, input_mode="radio")
    _submit_trap(state, "p-first-hit")
    assert state.streak == 1
    assert state.flawless_eligible is False

    response = _submit_trap(state, "p-second-hit")

    assert state.deconstruction is not None
    assert response.is_correct is False
    assert state.streak == 0
    assert state.flawless_eligible is False
    assert state.xp == 0
    assert state.problem_answered is True


def test_correct_answer_withheld_only_on_triggering_submission(monkeypatch):
    """Issue #194: correct_answer is withheld on a triggering Submission and present on
    every other Submission — the premise-level spoiler bug fixed here."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")

    first_response = _submit_trap(state, "p-first-hit")
    assert first_response.state.current_problem["correct_answer"] == "2"

    second_response = _submit_trap(state, "p-second-hit")

    assert state.deconstruction is not None
    assert "correct_answer" not in second_response.state.current_problem


def test_deconstruction_running_flag_tracks_the_running_deconstruction(monkeypatch):
    """`SessionResponse.deconstruction_running` is the client's takeover trigger, so it
    must name `state.deconstruction` exactly — not the withheld `correct_answer`, which
    is a spoiler rule the client must never have to infer from."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")

    first_response = _submit_trap(state, "p-first-hit")
    assert first_response.state.deconstruction_running is False

    second_response = _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None
    assert second_response.state.deconstruction_running is True

    abandoned = run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=state.session_id)
        )
    )
    assert state.deconstruction is None
    assert abandoned.deconstruction_running is False


def test_deconstructions_row_written_at_trigger_detection_with_null_outcome(
    monkeypatch,
):
    """Issue #194: the `deconstructions` header row exists after trigger detection,
    before the pause, with `outcome` NULL."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    assert _fetch_last_deconstruction_row(state.session_id) is None

    _submit_trap(state, "p-second-hit")

    row = _fetch_last_deconstruction_row(state.session_id)
    assert row is not None
    (
        session_id,
        username,
        problem_id,
        misconception_slug,
        chapter,
        topic,
        level_number,
        outcome,
    ) = row
    assert session_id == state.session_id
    assert username == state.username
    assert problem_id == "p-second-hit"
    assert misconception_slug == _UNLIKE_FRACTIONS_MISCONCEPTION
    assert level_number == 1
    assert outcome is None


def test_deconstruction_survives_sqlite_reload(monkeypatch):
    """Issue #194: `state.deconstruction` survives re-reading the Session from SQLite."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None

    main.ACTIVE_SESSIONS.clear()
    recovered = session.get_session(state.session_id)

    assert recovered.deconstruction is not None
    assert (
        recovered.deconstruction.misconception_slug == _UNLIKE_FRACTIONS_MISCONCEPTION
    )
    assert recovered.deconstruction.step_index == 0
    assert recovered.deconstruction.step_attempts == 0
    assert recovered.deconstruction.step_revealed is False
    assert [s.answer for s in recovered.deconstruction.steps] == [
        s.answer for s in state.deconstruction.steps
    ]


def test_misconception_hit_count_survives_sqlite_reload(monkeypatch):
    """Issue #339: a Session's Misconception hit count survives re-reading it from
    SQLite, so a first hit before reload plus a second hit after still triggers."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    assert state.deconstruction is None

    main.ACTIVE_SESSIONS.clear()
    recovered = session.get_session(state.session_id)
    assert recovered.deconstruction is None

    _submit_trap(recovered, "p-second-hit")

    assert recovered.deconstruction is not None
    assert (
        recovered.deconstruction.misconception_slug == _UNLIKE_FRACTIONS_MISCONCEPTION
    )


def test_problem_start_time_not_paused_by_trigger(monkeypatch):
    """Issue #194: problem_start_time keeps running unpaused through trigger detection."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")

    state.current_problem = _trap_problem("p-second-hit")
    state.problem_answered = False
    state.problem_start_time = 12345.0

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-second-hit",
                user_input="3",
            )
        )
    )

    assert state.deconstruction is not None
    assert state.problem_start_time == 12345.0


# --- Deconstruction step routes, grading, and the Reveal (#195) ---


def _arm_deconstruction(
    state, steps, *, misconception_slug=None, deconstruction_id=None
):
    """Directly arm `state.deconstruction`, bypassing the trigger — mirrors `make_state`
    setting `current_problem` directly rather than driving a whole Submission cycle."""
    state.deconstruction = DeconstructionState(
        misconception_slug=misconception_slug or _UNLIKE_FRACTIONS_MISCONCEPTION,
        steps=steps,
        deconstruction_id=deconstruction_id,
    )
    main.session_state.persist(state, StudentPlayMode())
    return state.deconstruction


def _submit_step(state, user_input):
    return run(
        main.deconstruction_submit(
            main.DeconstructionSubmissionRequest(
                session_id=state.session_id, user_input=user_input
            )
        )
    )


def _fetch_deconstruction_step_rows(deconstruction_id):
    """Every step row for one Deconstruction, in step order."""
    with sqlite3.connect(main.db.DB_PATH) as conn:
        return conn.execute(
            """
            SELECT step_index, revealed FROM deconstruction_steps
            WHERE deconstruction_id = ?
            ORDER BY step_index
            """,
            (deconstruction_id,),
        ).fetchall()


def _fetch_deconstruction_attempt_rows(deconstruction_id):
    """Every attempt row for one Deconstruction, keyed by column name.

    Keyed rather than positional: the row is too wide for positional reads to
    stay legible.
    """
    with sqlite3.connect(main.db.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT step_index, attempt_index, user_input, answer_form,
                       answer_value_num, answer_value_den, outcome, time_spent_ms
                FROM deconstruction_attempts
                WHERE deconstruction_id = ?
                ORDER BY step_index, attempt_index
                """,
                (deconstruction_id,),
            )
        ]


def test_deconstruction_next_returns_full_step_payload_with_null_working_line():
    """Issue #195: `working_line: null` is load-bearing — some walkthroughs author none."""
    problem = _trap_problem("p-step-payload")
    state = make_state(problem, input_mode="radio")
    _arm_deconstruction(
        state,
        [DeconstructionStep(question="Ile to jest?", working_line=None, answer="5")],
    )

    response = run(main.deconstruction_next(state.session_id))

    assert response.question == "Ile to jest?"
    assert response.working_line is None
    assert response.step_index == 0
    assert response.total_steps == 1
    assert response.misconception_name == resolve_curriculum().misconception_name(
        _UNLIKE_FRACTIONS_MISCONCEPTION
    )
    assert response.revealed_answer is None


def test_deconstruction_next_returns_authored_working_line():
    state = make_state(_trap_problem("p-working-line"), input_mode="radio")
    _arm_deconstruction(
        state,
        [DeconstructionStep(question="q", working_line=r"\frac{1}{2}", answer="5")],
    )

    response = run(main.deconstruction_next(state.session_id))

    assert response.working_line == r"\frac{1}{2}"


def test_no_attempt_counter_on_the_wire():
    """Issue #195: no attempt count appears anywhere on the wire — ADR-0004."""
    state = make_state(_trap_problem("p-no-counter"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )

    step_response = run(main.deconstruction_next(state.session_id))
    submit_response = _submit_step(state, "wrong")

    assert "attempts" not in step_response.model_dump()
    assert "attempts" not in submit_response.model_dump()


def test_wrong_answer_leaves_step_index_unchanged():
    state = make_state(_trap_problem("p-wrong-step"), input_mode="radio")
    _arm_deconstruction(
        state,
        [
            DeconstructionStep(question="q1", working_line=None, answer="5"),
            DeconstructionStep(question="q2", working_line=None, answer="7"),
        ],
    )

    response = _submit_step(state, "999")

    assert response.is_correct is False
    assert state.deconstruction.step_index == 0
    assert state.deconstruction.step_attempts == 1


def test_correct_answer_advances_step_index_and_resets_attempts():
    state = make_state(_trap_problem("p-correct-step"), input_mode="radio")
    _arm_deconstruction(
        state,
        [
            DeconstructionStep(question="q1", working_line=None, answer="5"),
            DeconstructionStep(question="q2", working_line=None, answer="7"),
        ],
    )
    _submit_step(state, "999")
    assert state.deconstruction.step_attempts == 1

    response = _submit_step(state, "5")

    assert response.is_correct is True
    assert state.deconstruction.step_index == 1
    assert state.deconstruction.step_attempts == 0
    assert state.deconstruction.step_revealed is False


def test_soft_error_does_not_count_toward_the_reveal():
    """Issue #195: a mistyped or wrongly-notated answer costs nothing toward the Reveal."""
    state = make_state(_trap_problem("p-soft-error"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )

    response = _submit_step(state, "not a number")

    assert response.is_correct is False
    assert response.feedback_msg
    assert state.deconstruction.step_index == 0
    assert state.deconstruction.step_attempts == 0
    assert state.deconstruction.step_revealed is False


def test_reveal_fires_at_threshold_without_advancing_the_step(monkeypatch):
    monkeypatch.setattr(config, "DECONSTRUCTION_REVEAL_THRESHOLD", 3)
    state = make_state(_trap_problem("p-reveal"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )

    _submit_step(state, "999")
    _submit_step(state, "999")
    assert state.deconstruction.step_revealed is False

    response = _submit_step(state, "999")

    assert response.is_correct is False
    assert state.deconstruction.step_index == 0
    assert state.deconstruction.step_revealed is True

    step_response = run(main.deconstruction_next(state.session_id))
    assert step_response.revealed_answer == "5"


def test_entering_the_revealed_answer_advances_the_step(monkeypatch):
    monkeypatch.setattr(config, "DECONSTRUCTION_REVEAL_THRESHOLD", 3)
    state = make_state(_trap_problem("p-reveal-enter"), input_mode="radio")
    _arm_deconstruction(
        state,
        [
            DeconstructionStep(question="q1", working_line=None, answer="5"),
            DeconstructionStep(question="q2", working_line=None, answer="7"),
        ],
    )
    for _ in range(3):
        _submit_step(state, "999")
    assert state.deconstruction.step_revealed is True

    response = _submit_step(state, "5")

    assert response.is_correct is True
    assert state.deconstruction.step_index == 1
    assert state.deconstruction.step_revealed is False
    assert state.deconstruction.step_attempts == 0


def test_post_reveal_wrong_answers_retry_indefinitely(monkeypatch):
    monkeypatch.setattr(config, "DECONSTRUCTION_REVEAL_THRESHOLD", 3)
    state = make_state(_trap_problem("p-reveal-retry"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )
    for _ in range(3):
        _submit_step(state, "999")
    assert state.deconstruction.step_revealed is True

    for _ in range(5):
        response = _submit_step(state, "999")
        assert response.is_correct is False
        assert state.deconstruction.step_index == 0
        assert state.deconstruction.step_revealed is True


def test_step_revealed_survives_sqlite_reload(monkeypatch):
    monkeypatch.setattr(config, "DECONSTRUCTION_REVEAL_THRESHOLD", 3)
    state = make_state(_trap_problem("p-reveal-reload"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )
    for _ in range(3):
        _submit_step(state, "999")
    assert state.deconstruction.step_revealed is True

    main.ACTIVE_SESSIONS.clear()
    recovered = session.get_session(state.session_id)

    assert recovered.deconstruction is not None
    assert recovered.deconstruction.step_revealed is True
    assert recovered.deconstruction.step_index == 0


# --- Ordering-input step type (#198) ---
#
# The wire contract and control only, so these use stand-in items rather than
# the real priority-ladder labels of `ignores_the_order_of_operations` (#186).

_ORDERING_ITEMS = ["a", "b", "c", "d"]
_ORDERING_ANSWER = ORDERING_ANSWER_SEPARATOR.join(_ORDERING_ITEMS)


def _ordering_step(question="q"):
    return DeconstructionStep(
        question=question,
        working_line=None,
        answer=_ORDERING_ANSWER,
        input_type="ordering",
        items=_ORDERING_ITEMS,
    )


def test_deconstruction_next_returns_ordering_step_payload():
    state = make_state(_trap_problem("p-ordering-payload"), input_mode="radio")
    _arm_deconstruction(state, [_ordering_step("Ułóż w kolejności.")])

    response = run(main.deconstruction_next(state.session_id))

    assert response.input_type == "ordering"
    assert response.items == _ORDERING_ITEMS


def test_deconstruction_next_defaults_to_typed_input():
    state = make_state(_trap_problem("p-typed-default"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )

    response = run(main.deconstruction_next(state.session_id))

    assert response.input_type == "typed"
    assert response.items is None


def test_ordering_step_grades_correct_and_incorrect_order():
    state = make_state(_trap_problem("p-ordering-grade"), input_mode="radio")
    _arm_deconstruction(
        state,
        [
            _ordering_step("q1"),
            DeconstructionStep(question="q2", working_line=None, answer="5"),
        ],
    )

    wrong = _submit_step(state, "b|a|c|d")
    assert wrong.is_correct is False
    assert state.deconstruction.step_index == 0
    assert state.deconstruction.step_attempts == 1

    correct = _submit_step(state, "a|b|c|d")
    assert correct.is_correct is True
    assert state.deconstruction.step_index == 1
    assert state.deconstruction.step_attempts == 0


def test_reveal_fires_on_an_ordering_step_same_as_typed(monkeypatch):
    monkeypatch.setattr(config, "DECONSTRUCTION_REVEAL_THRESHOLD", 3)
    state = make_state(_trap_problem("p-ordering-reveal"), input_mode="radio")
    _arm_deconstruction(
        state,
        [
            _ordering_step(),
            DeconstructionStep(question="q2", working_line=None, answer="5"),
        ],
    )

    _submit_step(state, "d|c|b|a")
    _submit_step(state, "d|c|b|a")
    assert state.deconstruction.step_revealed is False

    response = _submit_step(state, "d|c|b|a")
    assert response.is_correct is False
    assert state.deconstruction.step_revealed is True

    step_response = run(main.deconstruction_next(state.session_id))
    assert step_response.revealed_answer == _ORDERING_ANSWER

    response = _submit_step(state, _ORDERING_ANSWER)
    assert response.is_correct is True
    assert state.deconstruction.step_index == 1


def _ordering_step_with_accepted_orders(accepted_orders, question="q"):
    return DeconstructionStep(
        question=question,
        working_line=None,
        answer=_ORDERING_ANSWER,
        input_type="ordering",
        items=_ORDERING_ITEMS,
        accepted_orders=accepted_orders,
    )


def test_ordering_step_grades_an_accepted_order_other_than_answer_correct():
    swapped = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "d", "c"])
    state = make_state(_trap_problem("p-ordering-accepted"), input_mode="radio")
    _arm_deconstruction(
        state,
        [
            _ordering_step_with_accepted_orders([swapped]),
            DeconstructionStep(question="q2", working_line=None, answer="5"),
        ],
    )

    response = _submit_step(state, swapped)

    assert response.is_correct is True
    assert state.deconstruction.step_index == 1


def test_ordering_step_still_rejects_a_non_member_order():
    swapped = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "d", "c"])
    state = make_state(_trap_problem("p-ordering-non-member"), input_mode="radio")
    _arm_deconstruction(state, [_ordering_step_with_accepted_orders([swapped])])

    response = _submit_step(state, "d|c|b|a")

    assert response.is_correct is False
    assert state.deconstruction.step_index == 0


def test_ordering_step_response_never_exposes_accepted_orders():
    swapped = ORDERING_ANSWER_SEPARATOR.join(["a", "b", "d", "c"])
    state = make_state(_trap_problem("p-ordering-hidden"), input_mode="radio")
    _arm_deconstruction(state, [_ordering_step_with_accepted_orders([swapped])])

    response = run(main.deconstruction_next(state.session_id))

    assert not hasattr(response, "accepted_orders")


def test_deconstruction_steps_row_tracks_revealed_only(monkeypatch):
    """Issue #258: `deconstruction_steps` carries step_index and revealed — `attempts`
    is gone, derivable from `deconstruction_attempts` excluding soft_error rows."""
    monkeypatch.setattr(config, "DECONSTRUCTION_REVEAL_THRESHOLD", 3)
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None
    deconstruction_id = state.deconstruction.deconstruction_id
    assert deconstruction_id is not None

    rows = _fetch_deconstruction_step_rows(deconstruction_id)
    assert len(rows) == len(state.deconstruction.steps)
    assert all(row == (index, 0) for index, row in enumerate(rows))

    _submit_step(state, "999")
    _submit_step(state, "999")
    _submit_step(state, "999")

    rows = _fetch_deconstruction_step_rows(deconstruction_id)
    assert rows[0] == (0, 1)
    assert rows[1] == (1, 0)


def test_deconstruction_attempt_row_written_per_step_submit(monkeypatch):
    """Issue #258: each step submit writes one `deconstruction_attempts` row, keyed
    by Deconstruction, step index and attempt index within the step, carrying the
    raw input, Answer form, Answer value, Outcome and time_spent_ms."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-attempt-row")
    assert state.deconstruction is not None
    deconstruction_id = state.deconstruction.deconstruction_id
    assert deconstruction_id is not None

    run(main.deconstruction_next(state.session_id))
    response = _submit_step(state, "999")
    assert response.is_correct is False

    rows = _fetch_deconstruction_attempt_rows(deconstruction_id)
    assert len(rows) == 1
    row = rows[0]
    assert row["step_index"] == 0
    assert row["attempt_index"] == 1
    assert row["user_input"] == "999"
    assert row["answer_form"] == "999"
    assert (row["answer_value_num"], row["answer_value_den"]) == (999, 1)
    assert row["outcome"] == "wrong"
    assert row["time_spent_ms"] is not None and row["time_spent_ms"] >= 0

    run(main.deconstruction_next(state.session_id))
    _submit_step(state, "999")

    rows = _fetch_deconstruction_attempt_rows(deconstruction_id)
    assert [(row["step_index"], row["attempt_index"]) for row in rows] == [
        (0, 1),
        (0, 2),
    ]


def test_deconstruction_attempt_outcome_uses_the_four_value_vocabulary(monkeypatch):
    """Issue #258: attempt outcomes are `correct`/`trap`/`wrong`/`soft_error`, the
    same domain the Submission table uses — no narrower one."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-outcome-vocab")
    assert state.deconstruction is not None
    deconstruction_id = state.deconstruction.deconstruction_id
    assert deconstruction_id is not None

    _submit_step(state, "not a number")
    _submit_step(state, "999")

    rows = _fetch_deconstruction_attempt_rows(deconstruction_id)
    assert [row["outcome"] for row in rows] == ["soft_error", "wrong"]


def test_soft_error_attempt_writes_a_row_but_does_not_count_toward_reveal(
    monkeypatch,
):
    """Issue #258: a soft-error attempt is recorded, and still costs the Student
    nothing toward the Reveal threshold — both asserted on the same submit."""
    monkeypatch.setattr(config, "DECONSTRUCTION_REVEAL_THRESHOLD", 3)
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-soft-error-row")
    assert state.deconstruction is not None
    deconstruction_id = state.deconstruction.deconstruction_id
    assert deconstruction_id is not None

    response = _submit_step(state, "not a number")

    assert response.is_correct is False
    assert state.deconstruction.step_attempts == 0
    assert state.deconstruction.step_revealed is False

    rows = _fetch_deconstruction_attempt_rows(deconstruction_id)
    assert len(rows) == 1
    assert rows[0]["outcome"] == "soft_error"


def test_step_accepts_equivalent_unsimplified_answer_as_correct():
    """Issue #258: `2/4` against a target of `1/2` grades as Correct inside a
    Deconstruction step — the deliberate asymmetry with a Problem's `soft_error`."""
    state = make_state(_trap_problem("p-unsimplified"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="1/2")]
    )

    response = _submit_step(state, "2/4")

    assert response.is_correct is True


def test_deconstruction_next_raises_when_none_running():
    state = make_state(_trap_problem("p-no-deconstruction"), input_mode="radio")

    with pytest.raises(HTTPException):
        run(main.deconstruction_next(state.session_id))


# --- Deconstruction endings: completion, handback, discounted retry, Abandonment (#196) ---


def test_final_step_completion_returns_handback_question():
    """Issue #196: the final step's submit response carries the original Problem's
    question text, and only that submission — Handback has no separate endpoint."""
    problem = _trap_problem("p-handback")
    state = make_state(problem, input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )

    response = _submit_step(state, "5")

    assert response.is_correct is True
    assert response.handback_question == problem["question"]
    assert state.deconstruction is None


def test_non_final_step_completion_leaves_handback_question_none():
    state = make_state(_trap_problem("p-not-yet"), input_mode="radio")
    _arm_deconstruction(
        state,
        [
            DeconstructionStep(question="q1", working_line=None, answer="5"),
            DeconstructionStep(question="q2", working_line=None, answer="7"),
        ],
    )

    response = _submit_step(state, "5")

    assert response.is_correct is True
    assert response.handback_question is None
    assert state.deconstruction is not None


def test_completion_reopens_same_problem_with_answer_withheld():
    """Issue #196: after completion the triggering Problem is answerable again on
    the same problem_id, with `correct_answer` still withheld."""
    problem = _trap_problem("p-reopen")
    state = make_state(problem, input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )

    _submit_step(state, "5")

    assert state.discounted_problem_id == "p-reopen"
    assert state.current_problem is not None
    assert state.current_problem.get("problem_id") == "p-reopen"
    revealed = session.public_problem(state.current_problem, state, StudentPlayMode())
    assert "correct_answer" not in revealed


def test_discounted_retry_scores_xp_multiplier_streak_and_flawless_untouched(
    monkeypatch,
):
    """Issue #196: a correct second attempt scores XP at the config multiplier
    and leaves Streak and Flawless untouched — a Streak discount would let a
    Deconstruction gate Level completion, contradicting ADR-0004."""
    monkeypatch.setattr(config, "DECONSTRUCTION_DISCOUNTED_XP_MULTIPLIER", 0.5)
    problem = _trap_problem("p-discounted")
    state = make_state(problem, input_mode="radio")
    state.streak = 0
    state.flawless_eligible = False
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )
    _submit_step(state, "5")
    assert state.discounted_problem_id == "p-discounted"

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-discounted",
                user_input="2",
            )
        )
    )

    assert response.is_correct is True
    expected_xp = round(config.XP_REWARDS[1] * 0.5)
    assert state.xp == expected_xp
    assert state.streak == 0
    assert state.flawless_eligible is False
    assert state.discounted_problem_id is None


def test_next_problem_rejected_while_deconstruction_active():
    """Issue #196: Next problem is not a door — it is rejected backend-side while
    a Deconstruction is running, rather than serving a fresh Problem."""
    state = make_state(_trap_problem("p-next-rejected"), input_mode="radio")
    _arm_deconstruction(
        state, [DeconstructionStep(question="q", working_line=None, answer="5")]
    )

    with pytest.raises(HTTPException) as exc_info:
        run(main.problem_next(state.session_id))
    assert exc_info.value.status_code == 403


def test_next_problem_gate_shut_while_deconstruction_active(monkeypatch):
    """The 403 is a backstop, not the Student's experience: `can_next_problem`
    closes while a Deconstruction runs, so the client never offers a door the
    backend would only refuse."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")

    first_response = _submit_trap(state, "p-first-hit")
    assert first_response.state.can_next_problem is True

    second_response = _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None
    assert second_response.state.can_next_problem is False

    abandoned = run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=state.session_id)
        )
    )
    assert abandoned.can_next_problem is True


def test_exit_control_abandons_from_any_step_and_writes_outcome(monkeypatch):
    """Issue #196: the exit control ends the Deconstruction, writing
    `abandoned_via_control`."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-abandon-control")
    assert state.deconstruction is not None

    run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=state.session_id)
        )
    )

    assert state.deconstruction is None
    row = _fetch_last_deconstruction_row(state.session_id)
    assert row is not None
    assert row[-1] == "abandoned_via_control"


def test_abandon_via_control_leaves_problem_locked_revealed_nothing_earned(
    monkeypatch,
):
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-abandon-locked")
    assert state.deconstruction is not None
    xp_before = state.xp

    response = run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=state.session_id)
        )
    )

    assert state.xp == xp_before
    assert response.can_submit is False
    assert response.current_problem is not None
    assert response.current_problem.get("correct_answer") == "2"


def test_navigation_abandons_running_deconstruction_and_writes_outcome(monkeypatch):
    """Issue #196: toolbar Navigation ends a running Deconstruction cleanly,
    writing `abandoned_via_navigation` — the second of the two doors."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-abandon-nav")
    assert state.deconstruction is not None
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id

    run(
        main.session_navigate(
            main.SessionNavigateRequest(
                session_id=state.session_id,
                selected_chapter_id=chapter_id,
                selected_topic_id=topic_id,
                selected_level=1,
            )
        )
    )

    assert state.deconstruction is None
    row = _fetch_last_deconstruction_row(state.session_id)
    assert row is not None
    assert row[-1] == "abandoned_via_navigation"


def _fetch_last_deconstruction_ended_at(session_id):
    """`ended_at` on the Session's most recently created Deconstruction header row."""
    with sqlite3.connect(main.db.DB_PATH) as conn:
        return conn.execute(
            """
            SELECT ended_at FROM deconstructions
            WHERE session_id = ?
            ORDER BY deconstruction_id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()[0]


def test_ended_at_is_written_on_completion(monkeypatch):
    """Issue #258: `ended_at` is stamped on the same call that writes `completed`."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-ended-at-complete")
    assert state.deconstruction is not None
    deconstruction_id = state.deconstruction.deconstruction_id
    assert deconstruction_id is not None

    assert _fetch_last_deconstruction_ended_at(state.session_id) is None

    while state.deconstruction is not None:
        answer = state.deconstruction.steps[state.deconstruction.step_index].answer
        _submit_step(state, answer)

    assert _fetch_last_deconstruction_ended_at(state.session_id) is not None


def test_ended_at_is_written_on_abandon_via_control(monkeypatch):
    """Issue #258: `ended_at` is stamped whichever way a Deconstruction ends."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-ended-at-control")
    assert state.deconstruction is not None

    run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=state.session_id)
        )
    )

    assert _fetch_last_deconstruction_ended_at(state.session_id) is not None


def test_ended_at_is_written_on_abandon_via_navigation(monkeypatch):
    """Issue #258: the Navigation door stamps `ended_at` too, not just the control."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-ended-at-nav")
    assert state.deconstruction is not None
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id

    run(
        main.session_navigate(
            main.SessionNavigateRequest(
                session_id=state.session_id,
                selected_chapter_id=chapter_id,
                selected_topic_id=topic_id,
                selected_level=1,
            )
        )
    )

    assert _fetch_last_deconstruction_ended_at(state.session_id) is not None


def test_misconception_does_not_retrigger_after_abandonment_via_control(monkeypatch):
    """Issue #196: either ending disarms the (Misconception, Level) pair for the
    rest of the Session."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None
    run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=state.session_id)
        )
    )
    assert state.deconstruction is None

    _submit_trap(state, "p-third-hit")

    assert state.deconstruction is None


def test_misconception_does_not_retrigger_after_completion(monkeypatch):
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None
    steps = list(state.deconstruction.steps)
    for step in steps:
        _submit_step(state, step.answer)
    assert state.deconstruction is None

    _submit_trap(state, "p-third-hit")

    assert state.deconstruction is None


def test_deconstructed_misconception_does_not_refire_at_a_second_level(monkeypatch):
    """Issue #340: the guard widens with the count. A Misconception already
    deconstructed this Session must not re-fire at a different Level, even
    though the Session-wide count there already exceeds the threshold — a
    Session-wide count with a per-Level guard would otherwise punish the
    Student again after a single hit at every subsequent Level (ADR-0014)."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    chapter_id = resolve_curriculum().chapter_ids()[0]
    topic_id = _topic_with_a_published_level(chapter_id, 2)
    if topic_id is None:
        pytest.skip("Need a Topic publishing Level 2")
    state = make_state(
        _trap_problem("p-first-hit"), input_mode="radio", selected_topic_id=topic_id
    )
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None
    run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=state.session_id)
        )
    )
    assert state.deconstruction is None

    state.selected_level = 2
    _submit_trap(state, "p-third-hit")

    assert state.deconstruction is None


def test_new_session_rearms_a_misconception_deconstructed_in_an_earlier_session(
    monkeypatch,
):
    """Issue #340: a new Session gets a fresh id, so its hit count and
    deconstructed set both start empty — the reset falls out of Session
    identity rather than needing reset code (ADR-0014)."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    first_session = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(first_session, "p-first-hit")
    _submit_trap(first_session, "p-second-hit")
    assert first_session.deconstruction is not None
    run(
        main.deconstruction_abandon(
            main.DeconstructionAbandonRequest(session_id=first_session.session_id)
        )
    )
    assert first_session.deconstruction is None

    second_session = make_state(_trap_problem("p-new-first-hit"), input_mode="radio")
    _submit_trap(second_session, "p-new-first-hit")
    assert second_session.deconstruction is None

    _submit_trap(second_session, "p-new-second-hit")

    assert second_session.deconstruction is not None
    assert (
        second_session.deconstruction.misconception_slug
        == _UNLIKE_FRACTIONS_MISCONCEPTION
    )


_DECIMAL_ORDER_MISCONCEPTION = "compares_decimals_by_wrong_digit_order"
_DECIMAL_ORDER_PARAMETERS = {"s1": "1,2", "s2": "1,3"}


def test_discounted_retry_hit_counts_toward_a_different_misconception_but_arms_nothing(
    monkeypatch,
):
    """Issue #340: the hit is recorded before the discounted-retry branch — a
    retry's wrong answer still counts toward another Misconception's trigger,
    but the retry itself can never arm a Deconstruction on the spot, since the
    trigger check never runs for it (ADR-0014)."""
    _map_traps_to_misconceptions(
        monkeypatch,
        {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION, "t2": _DECIMAL_ORDER_MISCONCEPTION},
    )
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-second-hit")
    assert state.deconstruction is not None
    for step in list(state.deconstruction.steps):
        _submit_step(state, step.answer)
    assert state.deconstruction is None
    retry_problem_id = state.discounted_problem_id
    assert retry_problem_id is not None

    _submit_trap(
        state, retry_problem_id, trap_slug="t2", parameters=_DECIMAL_ORDER_PARAMETERS
    )

    assert state.deconstruction is None

    _submit_trap(
        state, "p-b-second-hit", trap_slug="t2", parameters=_DECIMAL_ORDER_PARAMETERS
    )

    assert state.deconstruction is not None
    assert state.deconstruction.misconception_slug == _DECIMAL_ORDER_MISCONCEPTION


def test_completed_deconstruction_correct_retry_discoverable_by_joining_on_problem_id(
    monkeypatch,
):
    """Issue #196: joining `deconstructions` to `telemetry_logs` on `problem_id`
    answers whether the Student then solved the triggering Problem — never
    denormalised onto the `deconstructions` row itself."""
    _map_traps_to_misconceptions(monkeypatch, {"t1": _UNLIKE_FRACTIONS_MISCONCEPTION})
    state = make_state(_trap_problem("p-first-hit"), input_mode="radio")
    _submit_trap(state, "p-first-hit")
    _submit_trap(state, "p-join")
    assert state.deconstruction is not None
    deconstruction_id = state.deconstruction.deconstruction_id
    assert deconstruction_id is not None

    steps = list(state.deconstruction.steps)
    for step in steps:
        _submit_step(state, step.answer)
    assert state.deconstruction is None
    assert state.discounted_problem_id == "p-join"

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id, problem_id="p-join", user_input="2"
            )
        )
    )

    with sqlite3.connect(main.db.DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT tl.answer_outcome FROM deconstructions d
            JOIN telemetry_logs tl ON tl.problem_id = d.problem_id
            WHERE d.deconstruction_id = ? AND tl.answer_outcome = 'correct'
            """,
            (deconstruction_id,),
        ).fetchone()
    assert row is not None
    assert row[0] == "correct"


def test_deconstruction_abandon_raises_when_none_running():
    state = make_state(_trap_problem("p-no-deconstruction-abandon"), input_mode="radio")

    with pytest.raises(HTTPException):
        run(
            main.deconstruction_abandon(
                main.DeconstructionAbandonRequest(session_id=state.session_id)
            )
        )
