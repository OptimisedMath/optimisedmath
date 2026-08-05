"""Unit tests for Session Orchestrator domain errors and session lookup."""

import uuid

import pytest

import backend.session_orchestrator as orchestrator
from backend.core import db
from backend.models import GameState


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    orchestrator.ACTIVE_SESSIONS.clear()
    yield
    orchestrator.ACTIVE_SESSIONS.clear()


def test_get_session_raises_when_missing():
    with pytest.raises(orchestrator.SessionNotFoundError) as exc_info:
        orchestrator.get_session(str(uuid.uuid4()))
    assert exc_info.value.status_code == 404


def test_get_session_loads_from_memory():
    session_id = str(uuid.uuid4())
    state = GameState(session_id=session_id)
    orchestrator.ACTIVE_SESSIONS[session_id] = state
    assert orchestrator.get_session(session_id) is state
