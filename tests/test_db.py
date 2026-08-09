"""Unit tests for the persistence layer public API (backend/core/db.py)."""

import sqlite3
import uuid

import pytest

from backend.core import db
from backend.models import ChapterFrontier, SessionState


def _sample_state(**overrides) -> SessionState:
    state = SessionState(
        session_id=str(uuid.uuid4()),
        username="alice",
        xp=120,
        streak=2,
        selected_chapter_id=10,
        selected_topic_id=20,
        selected_level=3,
        chapter_frontiers={
            10: ChapterFrontier(frontier_topic_id=30, frontier_level=2),
        },
    )
    for key, value in overrides.items():
        setattr(state, key, value)
    return state


def test_init_db_is_idempotent(tmp_path):
    db_path = tmp_path / "users.db"
    assert db_path.exists()
    db.init_db()
    state = _sample_state()
    db.save_user("alice", state)
    assert db.load_user("alice") is not None


def test_save_and_load_user_round_trip():
    state = _sample_state()
    db.save_user("alice", state)

    loaded = db.load_user("alice")

    assert loaded is not None
    assert loaded["xp"] == 120
    assert loaded["streak"] == 2
    assert loaded["selected_chapter_id"] == 10
    assert loaded["selected_topic_id"] == 20
    assert loaded["selected_level"] == 3
    assert loaded["chapter_frontiers"][10] == ChapterFrontier(
        frontier_topic_id=30, frontier_level=2
    )


def test_load_user_returns_none_when_missing():
    assert db.load_user("nobody") is None


def test_save_user_updates_existing():
    state = _sample_state(xp=50, streak=1)
    db.save_user("alice", state)

    updated = _sample_state(xp=200, streak=0, selected_level=1)
    db.save_user("alice", updated)

    loaded = db.load_user("alice")
    assert loaded is not None
    assert loaded["xp"] == 200
    assert loaded["streak"] == 0
    assert loaded["selected_level"] == 1


def test_save_and_load_session_round_trip():
    state = _sample_state()
    session_id = state.session_id
    db.save_session(session_id, "alice", state)

    loaded = db.load_session(session_id)

    assert loaded is not None
    assert loaded.session_id == session_id
    assert loaded.username == "alice"
    assert loaded.xp == state.xp
    assert loaded.streak == state.streak
    assert loaded.selected_chapter_id == state.selected_chapter_id
    assert loaded.chapter_frontiers == state.chapter_frontiers
    assert loaded.navigation is None


def test_load_session_returns_none_when_missing():
    assert db.load_session(str(uuid.uuid4())) is None


def test_save_session_upserts_existing():
    state = _sample_state(streak=1)
    session_id = state.session_id
    db.save_session(session_id, "alice", state)

    state.streak = 3
    state.xp = 999
    db.save_session(session_id, "alice", state)

    loaded = db.load_session(session_id)
    assert loaded is not None
    assert loaded.streak == 3
    assert loaded.xp == 999


def test_delete_session_removes_persisted_state():
    state = _sample_state()
    session_id = state.session_id
    db.save_session(session_id, "alice", state)
    assert db.load_session(session_id) is not None

    db.delete_session(session_id)

    assert db.load_session(session_id) is None


def test_log_telemetry_persists_entry():
    db.save_user("alice", _sample_state())

    db.log_telemetry(
        session_id="sess-1",
        username="alice",
        chapter_name="Ułamki",
        topic_name="Dodawanie",
        level_number=2,
        is_input_mode=True,
        is_correct=False,
        user_input="1/2",
        trap_id="t1",
        time_spent_seconds=15,
        equation_state="1/4 + 1/4",
    )

    with db.get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_logs WHERE session_id = ?",
            ("sess-1",),
        ).fetchone()[0]

    assert count == 1


def test_get_connection_closes_after_use(monkeypatch):
    connections: list[sqlite3.Connection] = []
    original_connect = sqlite3.connect

    def tracking_connect(*args, **kwargs):
        conn = original_connect(*args, **kwargs)
        connections.append(conn)
        return conn

    monkeypatch.setattr(sqlite3, "connect", tracking_connect)

    state = _sample_state()
    db.save_user("alice", state)
    db.load_user("alice")

    assert connections
    for conn in connections:
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


def test_log_telemetry_requires_existing_user():
    with pytest.raises(sqlite3.IntegrityError):
        db.log_telemetry(
            session_id="sess-orphan",
            username="ghost",
            chapter_name="Ułamki",
            topic_name="Dodawanie",
            level_number=1,
            is_input_mode=False,
            is_correct=True,
        )
