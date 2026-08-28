"""FastAPI integration tests for session flow, grading, and API contract."""

import asyncio
import json
import sqlite3
import uuid

import pytest
from fastapi import HTTPException

import backend.main as main
import backend.session as session
import backend.submission as submission
from backend.curriculum import resolve_curriculum
from backend.models import ChapterFrontier, SessionState
from backend.play_mode import StudentPlayMode


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def isolated_state(isolated_db):
    main.ACTIVE_SESSIONS.clear()
    yield
    main.ACTIVE_SESSIONS.clear()


def make_state(problem, *, streak=0, input_mode="radio"):
    """Build a SessionState with an active problem and register it in ACTIVE_SESSIONS."""
    curriculum = resolve_curriculum()
    chapter_ids = list(curriculum.chapter_ids())
    chapter_id = chapter_ids[0]
    topic_entry = curriculum.topics(chapter_id)[0]
    session_id = str(uuid.uuid4())
    state = SessionState()
    main.session_state.init_defaults(state, curriculum)
    state.session_id = session_id
    state.username = f"test-{session_id}"
    state.selected_chapter_id = chapter_id
    state.selected_topic_id = int(topic_entry["topic_id"])
    state.selected_level = 1
    state.streak = streak
    state.current_input_mode = input_mode
    state.problem_answered = False
    state.current_problem = problem
    state.problem_start_time = 0
    main.ACTIVE_SESSIONS[session_id] = state
    main.session_state.persist(state, StudentPlayMode())
    return state


def test_wrong_radio_submit_reveals_correct_answer():
    problem = {
        "problem_id": "p-radio-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
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


def test_wrong_text_submit_reveals_correct_answer():
    problem = {
        "problem_id": "p-text-wrong",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="input")

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


def test_input_submit_uses_mobile_sanitizer_and_keeps_input_mode():
    problem = {
        "problem_id": "p-mobile",
        "question": "q",
        "correct": "1 \\frac{1}{2}",
        "options": ["1 \\frac{1}{2}", "1", "2"],
        "options_map": {"1 \\frac{1}{2}": "correct", "1": "w1", "2": "w2"},
        "messages": {},
    }
    state = make_state(problem, input_mode="input")

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
    assert response.state.current_input_mode == "input"


def test_level_completing_submit_serves_full_streak_meter():
    problem = {
        "problem_id": "p-level-complete",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }
    state = make_state(problem, streak=2, input_mode="input")

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
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }
    state = make_state(problem, streak=1, input_mode="input")

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


def test_input_mode_defers_radio_to_input_until_next_problem():
    problem = {
        "problem_id": "p-radio-defer",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
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
    assert next_response.state.current_input_mode == "input"
    assert "input_mode" not in next_response.problem


def test_input_mode_defers_input_to_radio_until_next_problem():
    problem = {
        "problem_id": "p-text-defer",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }
    state = make_state(problem, streak=1, input_mode="input")

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
    assert submit_response.state.current_input_mode == "input"

    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.current_input_mode == "radio"
    assert "input_mode" not in next_response.problem


def test_soft_syntax_error_does_not_lock_problem():
    problem = {
        "problem_id": "p-soft",
        "question": "q",
        "correct": "3/4",
        "options": ["3/4", "1/2"],
        "options_map": {"3/4": "correct", "1/2": "w1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="input")

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


def test_soft_syntax_error_preserves_flawless_eligible():
    problem = {
        "problem_id": "p-soft-flawless",
        "question": "q",
        "correct": "3/4",
        "options": ["3/4", "1/2"],
        "options_map": {"3/4": "correct", "1/2": "w1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="input")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-soft-flawless",
                user_input="abc",
            )
        )
    )

    assert response.is_correct is False
    assert response.state.flawless_eligible is True


def test_unsimplified_fraction_preserves_flawless_eligible():
    problem = {
        "problem_id": "p-unsimplified",
        "question": "q",
        "correct": "1/2",
        "options": ["1/2", "2/4"],
        "options_map": {"1/2": "correct", "2/4": "w1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="input")

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
        "options_map": {"2": "correct", "3": "w1"},
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
        "options_map": {"2": "correct", "3": "w1"},
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
        "options_map": {"a": "correct", "b": "w1"},
        "messages": {},
    }
    state = make_state(problem, streak=0, input_mode="radio")
    state.selected_chapter_id = disabled_chapter_id
    state.selected_topic_id = disabled_topic["topic_id"]
    submission.run_submission_cycle(
        state, problem, "a", False, resolve_curriculum(), StudentPlayMode()
    )

    assert state.streak == 1
    assert state.current_input_mode == "radio"


def test_problem_next_avoids_recent_duplicate_instances(monkeypatch):
    import backend.problem_generation as problem_generation
    import backend.submission_cycle as submission_cycle

    curriculum = resolve_curriculum()
    chapter_ids = list(curriculum.chapter_ids())
    chapter_id = chapter_ids[0]
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

    duplicate_problem = {
        "problem_id": "dup-1",
        "question": "same question",
        "correct": "1",
        "options": ["1", "2"],
        "options_map": {"1": "correct", "2": "w1"},
        "messages": {},
        "level": 1,
        "level_name": "Test",
        "level_display": "Test (Lvl 1)",
        "keyboard_type": "default",
    }
    duplicate_fingerprint = problem_generation.problem_fingerprint(duplicate_problem)
    state.recent_problem_fingerprints = [duplicate_fingerprint]

    call_count = {"value": 0}

    def fake_generate_level_problem(_curriculum, _chapter_id, _topic_id, _level):
        call_count["value"] += 1
        return {
            **duplicate_problem,
            "problem_id": f"dup-{call_count['value']}",
        }

    unique_problem = {
        **duplicate_problem,
        "question": "different question",
        "problem_id": "unique-1",
    }

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

    response = run(main.problem_next(session_id))

    assert call_count["value"] == 2
    assert response.problem["question"] == "different question"
    assert duplicate_fingerprint in state.recent_problem_fingerprints
    assert (
        problem_generation.problem_fingerprint(unique_problem)
        in state.recent_problem_fingerprints
    )


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
        "options_map": {"1": "correct", "2": "w1"},
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
        "options_map": {"1": "correct", "2": "w1"},
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

    eval_result = grade(">", problem, is_input_mode=False)
    assert eval_result.get("answer_outcome") == "trap"
    assert eval_result.get("trap_slug") == "compares_by_the_lower_place_digit"
    assert eval_result.get("feedback_msg") == branch_message


def test_start_session_persists_problem_start_time():
    """The start clock must reach SQLite from the start path, not just memory."""
    response = run(
        main.session_start(
            main.SessionStartRequest(username=f"start-user-{uuid.uuid4()}")
        )
    )

    persisted = main.db.load_session(response.session_id)

    assert persisted is not None
    assert persisted.problem_start_time is not None


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
            SELECT time_spent_seconds FROM telemetry_logs
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
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
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
    """Issue #189: `parameters` rides through equation_state, which strips nothing new."""
    problem = {
        "problem_id": "p-parameters-telemetry",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
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
            SELECT equation_state FROM telemetry_logs
            WHERE session_id = ?
            ORDER BY log_id DESC
            LIMIT 1
            """,
            (state.session_id,),
        ).fetchone()

    assert row is not None
    assert row[0] is not None
    equation_state = json.loads(row[0])
    assert equation_state["parameters"] == {"n": 1, "d": 2, "op": "+"}


def _fetch_last_telemetry_row(session_id):
    with sqlite3.connect(main.db.DB_PATH) as conn:
        return conn.execute(
            """
            SELECT answer_outcome, misconception_slug, trap_slug, problem_id
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
                "w1": "test_misconception",
            },
        )

    monkeypatch.setattr(Curriculum, "level_config", fake_level_config)

    problem = {
        "problem_id": "p-mapped-trap",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
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
    assert row == ("trap", "test_misconception", "w1", "p-mapped-trap")


def test_unmapped_trap_submission_writes_trap_slug_with_null_misconception():
    """Issue #188: a Trap whose slug is un-mapped writes trap + trap_slug + NULL misconception_slug."""
    problem = {
        "problem_id": "p-unmapped-trap",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {"w1": "Try again"},
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
    assert row == ("trap", None, "w1", "p-unmapped-trap")


def test_filler_submission_writes_null_misconception_and_slug():
    """Issue #188: a Filler writes filler + NULL misconception_slug + NULL trap_slug."""
    problem = {
        "problem_id": "p-filler",
        "question": "q",
        "correct": "2",
        "options": ["2", "3", "4"],
        "options_map": {"2": "correct", "3": "w1", "4": "filler"},
        "messages": {"w1": "Try again", "filler": "Nope"},
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
    assert row == ("filler", None, None, "p-filler")


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
