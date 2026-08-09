"""Unit tests for submission telemetry adapter."""

import json
import sqlite3
import uuid

import backend.session_state as session_state
import backend.submission_telemetry as submission_telemetry
from backend.core import db
from backend.models import SessionState
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    TOPIC_MULTI,
)


def _fresh_state(fixture_curriculum) -> SessionState:
    chapter_ids = list(fixture_curriculum.chapter_ids())
    state = SessionState()
    session_state.init_defaults(
        state, chapter_ids, fixture_curriculum.as_nav_curriculum()
    )
    state.username = "telemetry-user"
    state.session_id = str(uuid.uuid4())
    state.selected_chapter_id = CHAPTER_ALPHA
    state.selected_topic_id = TOPIC_MULTI
    state.selected_level = 1
    return state


def test_sanitize_problem_strips_internal_fields():
    problem = {
        "problem_id": "p1",
        "question": "What is 2+2?",
        "correct": "4",
        "image_html": "<svg></svg>",
        "messages": {"w1": "nope"},
        "options": ["3", "4"],
        "options_map": {"4": "correct"},
        "level": 1,
        "level_name": "Easy",
        "level_display": "Level 1",
    }

    sanitized = json.loads(submission_telemetry.sanitize_problem_for_telemetry(problem))

    assert sanitized == {"question": "What is 2+2?", "correct": "4"}


def test_log_submission_telemetry_persists_fixture_names(fixture_curriculum):
    """Persisted Chapter and Topic names come from the fixture Curriculum."""
    state = _fresh_state(fixture_curriculum)
    problem = {
        "problem_id": "p1",
        "question": "q",
        "correct": "2",
        "image_html": "<svg></svg>",
        "options": ["2", "3"],
    }
    state.current_problem = problem
    state.problem_start_time = 0
    session_state.sync_to_db(state)

    submission_telemetry.log_submission_telemetry(
        state,
        problem,
        user_input="2",
        is_input_mode=False,
        eval_result={"is_correct": True},
        curriculum=fixture_curriculum,
    )

    with sqlite3.connect(db.DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT equation_state, is_correct, user_input, chapter, topic
            FROM telemetry_logs WHERE session_id = ?
            """,
            (state.session_id,),
        ).fetchone()

    assert row is not None
    stored = json.loads(row[0])
    assert "image_html" not in stored
    assert "options" not in stored
    assert row[1] == 1
    assert row[2] == "2"
    assert row[3] == "Chapter Alpha"
    assert row[4] == "Multi Level Topic"
