import asyncio
import uuid

import pytest
from fastapi import HTTPException

import backend.main as main
from backend.core import db
from backend.models import GameState, heal_legacy_state


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
    curriculum = main.engine.get_curriculum()
    macro = next(iter(curriculum))
    topic = curriculum[macro][0]
    session_id = str(uuid.uuid4())
    state = GameState()
    main.state_manager.StateManager.init_defaults(state, list(curriculum), curriculum)
    state.session_id = session_id
    state.username = f"test-{session_id}"
    state.selected_macro = macro
    state.selected_micro_topic_order = int(topic["micro_topic_order"])
    state.selected_level = 1
    state.streak = streak
    state.current_input_mode = input_mode
    state.problem_answered = False
    state.current_problem = problem
    state.problem_start_time = 0
    main.ACTIVE_SESSIONS[session_id] = state
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
                is_text_mode=False,
            )
        )
    )

    assert response["is_correct"] is False
    revealed = response["state"].current_problem
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
    state = make_state(problem, input_mode="text")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-text-wrong",
                user_input="99",
                is_text_mode=True,
            )
        )
    )

    assert response["is_correct"] is False
    revealed = response["state"].current_problem
    assert revealed["correct_answer"] == "2"
    assert "correct" not in revealed
    assert "options_map" not in revealed


def test_next_problem_hides_answer_contract_fields():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="contract-user", selected_macro=None)
        )
    )

    response = run(main.problem_next(state.session_id))
    problem = response["problem"]

    assert "answer_options" in problem
    assert "correct" not in problem
    assert "options_map" not in problem
    assert "messages" not in problem
    assert response["state"].can_submit is True


def test_text_submit_uses_mobile_sanitizer_and_switches_to_text_mode():
    problem = {
        "problem_id": "p-mobile",
        "question": "q",
        "correct": "1 \\frac{1}{2}",
        "options": ["1 \\frac{1}{2}", "1", "2"],
        "options_map": {"1 \\frac{1}{2}": "correct", "1": "w1", "2": "w2"},
        "messages": {},
    }
    state = make_state(problem, input_mode="text")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-mobile",
                user_input="1-1/2",
                is_text_mode=True,
            )
        )
    )

    assert response["is_correct"] is True
    assert response["state"].streak == 1
    assert response["state"].current_input_mode == "text"


def test_input_mode_defers_radio_to_text_until_next_problem():
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
                is_text_mode=False,
            )
        )
    )

    assert submit_response["is_correct"] is True
    assert submit_response["state"].streak == 1
    assert submit_response["state"].current_input_mode == "radio"

    next_response = run(main.problem_next(state.session_id))
    assert next_response["state"].current_input_mode == "text"
    assert next_response["problem"]["input_mode"] == "text"


def test_input_mode_defers_text_to_radio_until_next_problem():
    problem = {
        "problem_id": "p-text-defer",
        "question": "q",
        "correct": "2",
        "options": ["2", "3"],
        "options_map": {"2": "correct", "3": "w1"},
        "messages": {},
    }
    state = make_state(problem, streak=1, input_mode="text")

    submit_response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-text-defer",
                user_input="3",
                is_text_mode=True,
            )
        )
    )

    assert submit_response["is_correct"] is False
    assert submit_response["state"].streak == 0
    assert submit_response["state"].current_input_mode == "text"

    next_response = run(main.problem_next(state.session_id))
    assert next_response["state"].current_input_mode == "radio"
    assert next_response["problem"]["input_mode"] == "radio"


def test_soft_syntax_error_does_not_lock_problem():
    problem = {
        "problem_id": "p-soft",
        "question": "q",
        "correct": "3/4",
        "options": ["3/4", "1/2"],
        "options_map": {"3/4": "correct", "1/2": "w1"},
        "messages": {},
    }
    state = make_state(problem, input_mode="text")

    response = run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state.session_id,
                problem_id="p-soft",
                user_input="abc",
                is_text_mode=True,
            )
        )
    )

    assert response["is_correct"] is False
    assert response["state"].problem_answered is False
    assert response["state"].can_submit is True


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
            main.SessionStartRequest(username="locked-user", selected_macro=None)
        )
    )
    macro = state.selected_macro
    topics = main.engine.get_curriculum()[macro]
    if len(topics) < 2:
        pytest.skip("Need at least two topics for locked navigation test")

    locked_order = int(topics[1]["micro_topic_order"])
    with pytest.raises(HTTPException) as exc:
        run(
            main.session_navigate(
                main.SessionNavigateRequest(
                    session_id=state.session_id,
                    selected_macro=macro,
                    selected_micro_topic_order=locked_order,
                    selected_level=1,
                )
            )
        )

    assert exc.value.status_code == 403


def test_legacy_state_key_healing():
    legacy = {
        "session_id": "legacy-session",
        "selected_topic_order": 20,
        "progress": {
            "Ułamki Zwykłe": {"unlocked_order": 30, "unlocked_level": 2},
        },
    }
    healed = heal_legacy_state(legacy)
    assert healed["selected_micro_topic_order"] == 20
    assert "selected_topic_order" not in healed
    assert healed["progress"]["Ułamki Zwykłe"]["unlocked_micro_topic_order"] == 30

    state = GameState.from_storage(legacy)
    assert state.selected_micro_topic_order == 20
    assert state.progress["Ułamki Zwykłe"].unlocked_micro_topic_order == 30


def test_text_mode_disabled_keeps_radio_input():
    curriculum = main.engine.get_curriculum()
    disabled_topic = None
    disabled_macro = None
    for macro, topics in curriculum.items():
        for topic in topics:
            if topic.get("text_mode_disabled"):
                disabled_topic = topic
                disabled_macro = macro
                break
        if disabled_topic:
            break

    if not disabled_topic:
        pytest.skip("No text_mode_disabled topic in curriculum")

    problem = {
        "problem_id": "p-radio-only",
        "question": "q",
        "correct": disabled_topic["name"],
        "options": ["a", "b"],
        "options_map": {"a": "correct", "b": "w1"},
        "messages": {},
    }
    state = make_state(problem, streak=0, input_mode="radio")
    state.selected_macro = disabled_macro
    state.selected_micro_topic_order = disabled_topic["micro_topic_order"]
    topic_map = main.engine.build_topic_map(curriculum, disabled_macro)

    main.state_manager.StateManager.process_submission(
        state, problem, "a", False, topic_map
    )

    assert state.streak == 1
    assert state.current_input_mode == "radio"


def test_game_state_includes_navigation_view():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="nav-user", selected_macro=None)
        )
    )
    nav = state.navigation
    assert nav is not None
    assert len(nav.macro_topics) > 0
    assert len(nav.available_micro_topics) > 0
    assert len(nav.available_levels) > 0
    assert nav.current_topic_name is not None
    assert isinstance(nav.has_next_unlocked_topic, bool)
    assert isinstance(nav.text_mode_disabled, bool)
    assert nav.macro_progress is not None
    assert nav.micro_progress is not None


def test_navigation_available_topics_respect_locks():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="lock-nav-user", selected_macro=None)
        )
    )
    macro = state.selected_macro
    topics = main.engine.get_curriculum()[macro]
    if len(topics) < 2:
        pytest.skip("Need at least two topics for lock navigation test")

    unlocked_order = state.progress[macro].unlocked_micro_topic_order
    available_orders = {t.micro_topic_order for t in state.navigation.available_micro_topics}
    expected = {
        int(t["micro_topic_order"])
        for t in topics
        if int(t["micro_topic_order"]) <= unlocked_order
    }
    assert available_orders == expected


def test_navigation_admin_sees_all_topics():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="Antoni", selected_macro=None)
        )
    )
    macro = state.selected_macro
    topics = main.engine.get_curriculum()[macro]
    assert len(state.navigation.available_micro_topics) == len(topics)


def test_navigate_macro_change_resolves_to_unlocked_topic():
    curriculum = main.engine.get_curriculum()
    macro_topics = list(curriculum.keys())
    if len(macro_topics) < 2:
        pytest.skip("Need at least two macro topics")

    state = run(
        main.session_start(
            main.SessionStartRequest(username="macro-switch-user", selected_macro=None)
        )
    )
    target_macro = macro_topics[1] if state.selected_macro == macro_topics[0] else macro_topics[0]
    expected_order = state.progress[target_macro].unlocked_micro_topic_order
    expected_level = min(
        state.progress[target_macro].unlocked_level,
        int(curriculum[target_macro][0]["max_level"])
        if not any(
            int(t["micro_topic_order"]) == expected_order for t in curriculum[target_macro]
        )
        else next(
            int(t["max_level"])
            for t in curriculum[target_macro]
            if int(t["micro_topic_order"]) == expected_order
        ),
    )

    next_state = run(
        main.session_navigate(
            main.SessionNavigateRequest(
                session_id=state.session_id,
                selected_macro=target_macro,
            )
        )
    )

    assert next_state.selected_macro == target_macro
    assert next_state.selected_micro_topic_order == expected_order
    assert next_state.selected_level == expected_level


def test_navigate_topic_change_to_completed_resets_level_to_one():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="topic-switch-user", selected_macro=None)
        )
    )
    macro = state.selected_macro
    topics = main.engine.get_curriculum()[macro]
    if len(topics) < 2:
        pytest.skip("Need at least two topics")

    unlocked_order = state.progress[macro].unlocked_micro_topic_order
    completed_topics = [
        t for t in topics if int(t["micro_topic_order"]) < unlocked_order
    ]
    if not completed_topics:
        pytest.skip("Need a completed topic behind the unlocked frontier")

    completed_order = int(completed_topics[0]["micro_topic_order"])
    state.selected_level = 3

    next_state = run(
        main.session_navigate(
            main.SessionNavigateRequest(
                session_id=state.session_id,
                selected_micro_topic_order=completed_order,
            )
        )
    )

    assert next_state.selected_micro_topic_order == completed_order
    assert next_state.selected_level == 1


def test_navigation_has_next_unlocked_topic():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="next-topic-user", selected_macro=None)
        )
    )
    macro = state.selected_macro
    topics = main.engine.get_curriculum()[macro]
    if len(topics) < 2:
        pytest.skip("Need at least two topics")

    first_order = int(topics[0]["micro_topic_order"])
    second_order = int(topics[1]["micro_topic_order"])
    state.selected_micro_topic_order = first_order
    state.progress[macro].unlocked_micro_topic_order = second_order

    nav = main.navigation.build_navigation_view(
        state.for_response(main._public_problem),
        main.engine.get_curriculum(),
    )
    assert nav.has_next_unlocked_topic is True

    state.progress[macro].unlocked_micro_topic_order = first_order
    nav = main.navigation.build_navigation_view(
        state.for_response(main._public_problem),
        main.engine.get_curriculum(),
    )
    assert nav.has_next_unlocked_topic is False


def test_navigation_progress_counts():
    state = run(
        main.session_start(
            main.SessionStartRequest(username="progress-user", selected_macro=None)
        )
    )
    macro = state.selected_macro
    topics = main.engine.get_curriculum()[macro]
    unlocked_order = state.progress[macro].unlocked_micro_topic_order
    completed = sum(1 for t in topics if int(t["micro_topic_order"]) < unlocked_order)
    total = len(topics)

    assert state.navigation.macro_progress.completed == completed
    assert state.navigation.macro_progress.total == total
    assert state.navigation.macro_progress.percentage == pytest.approx(
        (completed / total * 100) if total else 0.0
    )

    current_topic = next(
        t
        for t in topics
        if int(t["micro_topic_order"]) == state.selected_micro_topic_order
    )
    max_level = int(current_topic["max_level"])
    assert state.navigation.micro_progress.completed == state.selected_level - 1
    assert state.navigation.micro_progress.total == max_level
    assert state.navigation.micro_progress.percentage == pytest.approx(
        ((state.selected_level - 1) / max_level * 100) if max_level else 0.0
    )
