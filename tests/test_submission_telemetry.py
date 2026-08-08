"""Unit tests for submission telemetry adapter."""

import json
import sqlite3
import uuid

import pytest

import backend.session_state as session_state
import backend.submission_telemetry as submission_telemetry
from backend.core import db
from backend.curriculum_loader import get_curriculum, get_topics_by_id
from backend.models import SessionState


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    yield


def _fresh_state() -> SessionState:
    curriculum = get_curriculum()
    chapter_ids = sorted(curriculum.keys())
    state = SessionState()
    session_state.init_defaults(state, chapter_ids, curriculum)
    state.username = "telemetry-user"
    state.session_id = str(uuid.uuid4())
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


def test_log_submission_telemetry_persists_sanitized_problem():
    state = _fresh_state()
    chapter_id = state.selected_chapter_id
    topics_by_id = get_topics_by_id(chapter_id)
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
        eval_result={"is_correct": True, "trap_id": None},
        topics_by_id=topics_by_id,
    )

    with sqlite3.connect(db.DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT equation_state, is_correct, user_input
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
