"""Internal-seam tests for the Submission cycle module."""

import uuid

import backend.submission_cycle as submission_cycle
from backend.curriculum import Curriculum
from backend.models import SessionState
import backend.session_state as session_state
from tests.support.fixture_curriculum import TOPIC_RADIO


def _fresh_state(fixture_curriculum: Curriculum) -> SessionState:
    state = SessionState()
    session_state.init_defaults(state, fixture_curriculum)
    state.username = "submission-cycle-user"
    state.session_id = str(uuid.uuid4())
    return state


def test_reset_submission_cycle_clears_problem_and_feedback(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.streak = 2
    state.problem_answered = True
    state.feedback_type = "error"
    state.feedback_msg = "oops"
    state.current_problem = {"problem_id": "p1"}

    submission_cycle.reset_submission_cycle(state)

    assert state.streak == 0
    assert state.problem_answered is False
    assert state.feedback_type is None
    assert state.feedback_msg == ""
    assert state.current_problem is None
    assert state.current_input_mode == "radio"


def test_navigate_to_updates_selection_and_resets_submission_cycle(
    fixture_curriculum: Curriculum,
):
    state = _fresh_state(fixture_curriculum)
    state.streak = 2
    state.problem_answered = True
    state.current_problem = {"problem_id": "p1"}

    submission_cycle.navigate_to(
        state,
        topic_id=TOPIC_RADIO,
        level=1,
        curriculum=fixture_curriculum,
    )

    assert state.selected_topic_id == TOPIC_RADIO
    assert state.selected_level == 1
    assert state.streak == 0
    assert state.problem_answered is False
    assert state.current_problem is None
