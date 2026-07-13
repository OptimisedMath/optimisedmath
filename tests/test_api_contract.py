import asyncio
import uuid

import pytest
from fastapi import HTTPException

import backend.main as main
from backend.core import db


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
    state = {}
    main.state_manager.StateManager.init_defaults(state, list(curriculum), curriculum)
    state.update(
        {
            "session_id": session_id,
            "username": f"test-{session_id}",
            "selected_macro": macro,
            "selected_topic_order": int(topic["Topic_Order"]),
            "selected_level": 1,
            "streak": streak,
            "current_input_mode": input_mode,
            "problem_answered": False,
            "current_problem": problem,
            "problem_start_time": 0,
        }
    )
    main.ACTIVE_SESSIONS[session_id] = state
    return state


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
                session_id=state["session_id"],
                problem_id="p-mobile",
                user_input="1-1/2",
                is_text_mode=True,
            )
        )
    )

    assert response["is_correct"] is True
    assert response["state"].streak == 1
    assert response["state"].current_input_mode == "text"


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
                session_id=state["session_id"],
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
                    session_id=state["session_id"],
                    problem_id="wrong-id",
                    user_input="2",
                )
            )
        )
    assert stale.value.status_code == 409

    run(
        main.problem_submit(
            main.ProblemSubmissionRequest(
                session_id=state["session_id"],
                problem_id="p-lock",
                user_input="2",
            )
        )
    )

    with pytest.raises(HTTPException) as duplicate:
        run(
            main.problem_submit(
                main.ProblemSubmissionRequest(
                    session_id=state["session_id"],
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

    locked_order = int(topics[1]["Topic_Order"])
    with pytest.raises(HTTPException) as exc:
        run(
            main.session_navigate(
                main.SessionNavigateRequest(
                    session_id=state.session_id,
                    selected_macro=macro,
                    selected_topic_order=locked_order,
                    selected_level=1,
                )
            )
        )

    assert exc.value.status_code == 403
