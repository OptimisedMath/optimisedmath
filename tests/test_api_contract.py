"""FastAPI integration tests for session flow, grading, and API contract."""

import asyncio
import uuid

import pytest
from fastapi import HTTPException

import backend.main as main
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
    main.session_state.sync_to_db(state)
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
                is_input_mode=False,
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
                is_input_mode=True,
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
                is_input_mode=True,
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
                is_input_mode=True,
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
                is_input_mode=True,
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
                is_input_mode=False,
            )
        )
    )

    assert submit_response.is_correct is True
    assert submit_response.state.streak == 1
    assert submit_response.state.current_input_mode == "radio"

    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.current_input_mode == "input"
    assert next_response.problem["input_mode"] == "input"


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
                is_input_mode=True,
            )
        )
    )

    assert submit_response.is_correct is False
    assert submit_response.state.streak == 0
    assert submit_response.state.current_input_mode == "input"

    next_response = run(main.problem_next(state.session_id))
    assert next_response.state.current_input_mode == "radio"
    assert next_response.problem["input_mode"] == "radio"


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
                is_input_mode=True,
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
                is_input_mode=True,
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
                is_input_mode=True,
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
    submission.process_submission(
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
    assert problem_generation.problem_fingerprint(unique_problem) in state.recent_problem_fingerprints


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
    main.session_state.sync_to_db(state)
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


def test_generator_messages_override_yaml_traps(monkeypatch):
    from backend.core.utils import build_problem_dict
    import backend.problem_generation as problem_generation
    from backend.answer_grading import grade

    branch_message = "branch-specific trap feedback"

    def fake_compare():
        result = build_problem_dict(r"\text{q}", "<", t1=">", t2="=")
        assert result is not None
        result["messages"] = {"t1": branch_message}
        return result

    monkeypatch.setitem(problem_generation.FUNCTION_REGISTRY, "dec_compare_1", fake_compare)

    from backend.curriculum import resolve_curriculum

    problem = problem_generation.generate_level_problem(
        resolve_curriculum(), 20, 20, 1
    )
    assert problem is not None
    assert problem["messages"]["t1"] == branch_message
    assert (
        problem["messages"]["t2"]
        == "Liczby nie są równe — nie wybieraj znaku równości!"
    )

    eval_result = grade(">", problem, is_input_mode=False)
    assert eval_result.get("trap_id") == "t1"
    assert eval_result.get("feedback_msg") == branch_message

