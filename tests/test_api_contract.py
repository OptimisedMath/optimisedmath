"""FastAPI integration tests for session flow, grading, and API contract."""

import asyncio
import uuid

import pytest
from fastapi import HTTPException

import backend.main as main
from backend.core import db
from backend.curriculum_loader import get_curriculum
from backend.models import GameState


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    main.ACTIVE_SESSIONS.clear()
    yield
    main.ACTIVE_SESSIONS.clear()


def make_state(problem, *, streak=0, input_mode="radio"):
    """Build a GameState with an active problem and register it in ACTIVE_SESSIONS."""
    curriculum = get_curriculum()
    chapter_ids = list(curriculum.keys())
    chapter_id = chapter_ids[0]
    topic_entry = curriculum[chapter_id][0]
    session_id = str(uuid.uuid4())
    state = GameState()
    main.state_manager.StateManager.init_defaults(state, chapter_ids, curriculum)
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
    main.state_manager.StateManager.sync_to_db(state)
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
    chapter_topics = get_curriculum()[chapter_id]
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
    curriculum = get_curriculum()
    disabled_topic = None
    disabled_chapter_id = None
    for chapter_id_key, chapter_topics in curriculum.items():
        for topic_entry in chapter_topics:
            if topic_entry.get("radio_only"):
                disabled_topic = topic_entry
                disabled_chapter_id = chapter_id_key
                break
        if disabled_topic:
            break

    if not disabled_topic:
        pytest.skip("No radio_only topic in curriculum")

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
    from backend.curriculum_loader import get_topics_by_id

    topics_by_id = get_topics_by_id(disabled_chapter_id)

    main.state_manager.StateManager.process_submission(
        state, problem, "a", False, topics_by_id
    )

    assert state.streak == 1
    assert state.current_input_mode == "radio"


def test_game_state_includes_navigation_view():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="nav-user", selected_chapter_id=None)
        )
    )
    nav = state.navigation
    assert nav is not None
    assert len(nav.available_chapters) > 0
    assert len(nav.available_topics) > 0
    assert len(nav.available_levels) > 0
    assert nav.current_topic_name is not None
    assert isinstance(nav.has_next_unlocked_topic, bool)
    assert isinstance(nav.radio_only, bool)
    assert nav.chapter_progress is not None
    assert nav.topic_progress is not None


def test_navigation_available_topics_respect_locks():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="lock-nav-user", selected_chapter_id=None)
        )
    )
    chapter_id = state.selected_chapter_id
    chapter_topics = get_curriculum()[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics for lock navigation test")

    unlocked_topic_id = state.chapter_progress[chapter_id].unlocked_topic_id
    available_topic_ids = {t.topic_id for t in state.navigation.available_topics}
    expected = {
        int(topic_entry["topic_id"])
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) <= unlocked_topic_id
    }
    assert available_topic_ids == expected


def test_navigation_admin_sees_all_topics():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="Antoni", selected_chapter_id=None)
        )
    )
    chapter_id = state.selected_chapter_id
    chapter_topics = get_curriculum()[chapter_id]
    assert len(state.navigation.available_topics) == len(chapter_topics)


def test_navigate_chapter_change_resolves_to_unlocked_topic():
    curriculum = get_curriculum()
    chapter_ids = list(curriculum.keys())
    if len(chapter_ids) < 2:
        pytest.skip("Need at least two chapters")

    state = run(
        main.session_start(
            main.SessionStartRequest(username="chapter-switch-user", selected_chapter_id=None)
        )
    )
    target_chapter_id = (
        chapter_ids[1]
        if state.selected_chapter_id == chapter_ids[0]
        else chapter_ids[0]
    )
    expected_topic_id = state.chapter_progress[target_chapter_id].unlocked_topic_id
    expected_level = min(
        state.chapter_progress[target_chapter_id].unlocked_level,
        int(curriculum[target_chapter_id][0]["max_level"])
        if not any(
            int(topic_entry["topic_id"]) == expected_topic_id
            for topic_entry in curriculum[target_chapter_id]
        )
        else next(
            int(topic_entry["max_level"])
            for topic_entry in curriculum[target_chapter_id]
            if int(topic_entry["topic_id"]) == expected_topic_id
        ),
    )

    next_state = run(
        main.session_navigate(
            main.SessionNavigateRequest(
                session_id=state.session_id,
                selected_chapter_id=target_chapter_id,
            )
        )
    )

    assert next_state.selected_chapter_id == target_chapter_id
    assert next_state.selected_topic_id == expected_topic_id
    assert next_state.selected_level == expected_level


def test_session_start_clamps_stale_selected_level():
    username = "stale-level-user"
    state = run(
        main.session_start(
            main.SessionStartRequest(username=username, selected_chapter_id=None)
        )
    )
    chapter_id = state.selected_chapter_id
    topic_entry = get_curriculum()[chapter_id][0]
    max_level = int(topic_entry["max_level"])

    state.selected_level = max_level + 10
    main.state_manager.StateManager.sync_to_db(state)

    reloaded = run(
        main.session_start(
            main.SessionStartRequest(username=username, selected_chapter_id=None)
        )
    )

    assert reloaded.selected_level == max_level


def test_navigate_topic_change_to_completed_resets_level_to_one():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="topic-switch-user", selected_chapter_id=None)
        )
    )
    chapter_id = state.selected_chapter_id
    chapter_topics = get_curriculum()[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    unlocked_topic_id = state.chapter_progress[chapter_id].unlocked_topic_id
    completed_topics = [
        topic_entry
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) < unlocked_topic_id
    ]
    if not completed_topics:
        pytest.skip("Need a completed topic behind UnlockedProgress")

    completed_topic_id = int(completed_topics[0]["topic_id"])
    state.selected_level = 3

    next_state = run(
        main.session_navigate(
            main.SessionNavigateRequest(
                session_id=state.session_id,
                selected_topic_id=completed_topic_id,
            )
        )
    )

    assert next_state.selected_topic_id == completed_topic_id
    assert next_state.selected_level == 1


def test_navigation_has_next_unlocked_topic():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="next-topic-user", selected_chapter_id=None)
        )
    )
    chapter_id = state.selected_chapter_id
    chapter_topics = get_curriculum()[chapter_id]
    if len(chapter_topics) < 2:
        pytest.skip("Need at least two topics")

    first_topic_id = int(chapter_topics[0]["topic_id"])
    second_topic_id = int(chapter_topics[1]["topic_id"])
    state.selected_topic_id = first_topic_id
    state.chapter_progress[chapter_id].unlocked_topic_id = second_topic_id

    nav = main.navigation.build_navigation_view(
        state.for_response(main._public_problem),
        get_curriculum(),
    )
    assert nav.has_next_unlocked_topic is True

    state.chapter_progress[chapter_id].unlocked_topic_id = first_topic_id
    nav = main.navigation.build_navigation_view(
        state.for_response(main._public_problem),
        get_curriculum(),
    )
    assert nav.has_next_unlocked_topic is False


def test_navigation_progress_counts():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="progress-user", selected_chapter_id=None)
        )
    )
    chapter_id = state.selected_chapter_id
    chapter_topics = get_curriculum()[chapter_id]
    unlocked_topic_id = state.chapter_progress[chapter_id].unlocked_topic_id
    completed = sum(
        1
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) < unlocked_topic_id
    )
    total = len(chapter_topics)

    assert state.navigation.chapter_progress.completed == completed
    assert state.navigation.chapter_progress.total == total
    assert state.navigation.chapter_progress.percentage == pytest.approx(
        (completed / total * 100) if total else 0.0
    )

    current_topic = next(
        topic_entry
        for topic_entry in chapter_topics
        if int(topic_entry["topic_id"]) == state.selected_topic_id
    )
    max_level = int(current_topic["max_level"])
    assert state.navigation.topic_progress.completed == state.selected_level - 1
    assert state.navigation.topic_progress.total == max_level
    assert state.navigation.topic_progress.percentage == pytest.approx(
        ((state.selected_level - 1) / max_level * 100) if max_level else 0.0
    )


def test_problem_next_avoids_recent_duplicate_instances(monkeypatch):
    import backend.problem_generation as problem_generation
    import backend.session_orchestrator as session_orchestrator

    curriculum = get_curriculum()
    chapter_ids = list(curriculum.keys())
    chapter_id = chapter_ids[0]
    topic_entry = curriculum[chapter_id][0]
    session_id = str(uuid.uuid4())
    state = GameState()
    main.state_manager.StateManager.init_defaults(state, chapter_ids, curriculum)
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

    def fake_generate_level_problem(_chapter_id, _topic_id, _level):
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

    def fake_generate_with_unique_second(_chapter_id, _topic_id, _level):
        call_count["value"] += 1
        if call_count["value"] == 1:
            return {
                **duplicate_problem,
                "problem_id": "dup-attempt",
            }
        return unique_problem

    monkeypatch.setattr(
        session_orchestrator, "generate_level_problem", fake_generate_with_unique_second
    )

    response = run(main.problem_next(session_id))

    assert call_count["value"] == 2
    assert response.problem["question"] == "different question"
    assert duplicate_fingerprint in state.recent_problem_fingerprints
    assert problem_generation.problem_fingerprint(unique_problem) in state.recent_problem_fingerprints


def test_generator_messages_override_yaml_traps(monkeypatch):
    from backend.core.utils import build_problem_dict
    import backend.problem_generation as problem_generation
    from backend.answer_grading import evaluate_answer

    branch_message = "branch-specific trap feedback"

    def fake_compare():
        result = build_problem_dict(r"\text{q}", "<", t1=">", t2="=")
        result["messages"] = {"t1": branch_message}
        return result

    monkeypatch.setitem(problem_generation.FUNCTION_REGISTRY, "dec_compare_1", fake_compare)

    problem = problem_generation.generate_level_problem(20, 20, 1)
    assert problem is not None
    assert problem["messages"]["t1"] == branch_message
    assert (
        problem["messages"]["t2"]
        == "Liczby nie są równe — nie wybieraj znaku równości!"
    )

    eval_result = evaluate_answer(">", problem, is_input_mode=False)
    assert eval_result["trap_id"] == "t1"
    assert eval_result["feedback_msg"] == branch_message

