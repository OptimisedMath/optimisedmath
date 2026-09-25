"""Unit tests for the persistence layer public API (backend/core/db.py)."""

import json
import sqlite3
import uuid

import pytest

from backend.core import db
from backend.models import ChapterFrontier, SessionState

RESPONSE_ONLY_FIELDS = frozenset(
    {"can_submit", "can_next_problem", "admin_mode", "navigation"}
)


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


def _raw_session_json(session_id: str) -> dict:
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    assert row is not None
    return json.loads(row[0])


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
    assert loaded["selected_chapter_id"] == 10
    assert loaded["selected_topic_id"] == 20
    assert loaded["selected_level"] == 3
    assert loaded["chapter_frontiers"][10] == ChapterFrontier(
        frontier_topic_id=30, frontier_level=2
    )


def test_load_user_returns_none_when_missing():
    assert db.load_user("nobody") is None


def test_save_user_updates_existing():
    state = _sample_state(xp=50)
    db.save_user("alice", state)

    updated = _sample_state(xp=200, selected_level=1)
    db.save_user("alice", updated)

    loaded = db.load_user("alice")
    assert loaded is not None
    assert loaded["xp"] == 200
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
    assert RESPONSE_ONLY_FIELDS.isdisjoint(type(loaded).model_fields)


def test_saved_session_json_omits_response_only_fields():
    state = _sample_state(
        current_problem={"problem_id": "p1", "question": "q", "correct": "1"},
        problem_answered=False,
    )
    db.save_session(state.session_id, "alice", state)

    stored = _raw_session_json(state.session_id)

    assert RESPONSE_ONLY_FIELDS.isdisjoint(stored)


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
        play_mode="student",
        chapter_id=10,
        chapter_name="Ułamki",
        topic_id=20,
        topic_name="Dodawanie",
        level_number=2,
        input_mode="typing",
        streak_before_answer=1,
        flawless_eligible=True,
        frontier_relation="at_frontier",
        user_input="1/2",
        answer_outcome="trap",
        trap_slug="t1",
        time_spent_ms=1500,
        problem_snapshot="1/4 + 1/4",
    )

    with db.get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_logs WHERE session_id = ?",
            ("sess-1",),
        ).fetchone()[0]

    assert count == 1


def test_log_telemetry_trap_source_defaults_to_null():
    """Issue #257: `trap_source` is absent (NULL) when the caller passes none."""
    db.save_user("alice", _sample_state())

    db.log_telemetry(
        session_id="sess-no-trap",
        username="alice",
        play_mode="student",
        chapter_id=10,
        chapter_name="Ułamki",
        topic_id=20,
        topic_name="Dodawanie",
        level_number=2,
        input_mode="typing",
        streak_before_answer=1,
        flawless_eligible=True,
        frontier_relation="at_frontier",
        answer_outcome="correct",
    )

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT trap_source FROM telemetry_logs WHERE session_id = ?",
            ("sess-no-trap",),
        ).fetchone()

    assert row[0] is None


def test_log_telemetry_persists_trap_source():
    db.save_user("alice", _sample_state())

    db.log_telemetry(
        session_id="sess-trap-source",
        username="alice",
        play_mode="student",
        chapter_id=10,
        chapter_name="Ułamki",
        topic_id=20,
        topic_name="Dodawanie",
        level_number=2,
        input_mode="typing",
        streak_before_answer=1,
        flawless_eligible=True,
        frontier_relation="at_frontier",
        answer_outcome="trap",
        trap_slug="answers_in_the_wrong_dimension",
        trap_source="synthesized",
    )

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT trap_source FROM telemetry_logs WHERE session_id = ?",
            ("sess-trap-source",),
        ).fetchone()

    assert row[0] == "synthesized"


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
            play_mode="student",
            chapter_id=10,
            chapter_name="Ułamki",
            topic_id=20,
            topic_name="Dodawanie",
            level_number=1,
            input_mode="radio",
            streak_before_answer=0,
            flawless_eligible=True,
            frontier_relation="at_frontier",
            answer_outcome="correct",
        )


def test_telemetry_schema_has_no_is_correct_column():
    """#253: `is_correct` duplicated `answer_outcome IS NULL` and is gone."""
    with db.get_connection() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(telemetry_logs)")}

    assert "is_correct" not in columns
    assert "answer_outcome" in columns


def test_telemetry_answer_outcome_column_is_not_null():
    db.save_user("alice", _sample_state())

    with pytest.raises(sqlite3.IntegrityError):
        with db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO telemetry_logs (
                    session_id, username, play_mode, chapter_id, chapter,
                    topic_id, topic, level_number, input_mode,
                    streak_before_answer, flawless_eligible, frontier_relation,
                    answer_outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                ("sess-null-outcome", "alice", "student", 10, "Ułamki", 20,
                 "Dodawanie", 2, "typing", 0, True, "at_frontier"),
            )


def test_init_db_is_idempotent_on_a_matching_telemetry_table():
    """Calling `init_db` again on a table already shaped like `_TELEMETRY_COLUMNS`
    is a no-op — existing rows survive."""
    db.save_user("alice", _sample_state())
    db.log_telemetry(
        session_id="sess-keep",
        username="alice",
        play_mode="student",
        chapter_id=10,
        chapter_name="Ułamki",
        topic_id=20,
        topic_name="Dodawanie",
        level_number=2,
        input_mode="typing",
        streak_before_answer=1,
        flawless_eligible=True,
        frontier_relation="at_frontier",
        answer_outcome="correct",
    )

    db.init_db()

    with db.get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_logs WHERE session_id = ?",
            ("sess-keep",),
        ).fetchone()[0]
    assert count == 1


def test_init_db_drops_telemetry_table_missing_a_required_column():
    with db.get_connection() as conn:
        conn.execute("DROP TABLE telemetry_logs")
        conn.execute("""
            CREATE TABLE telemetry_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("INSERT INTO telemetry_logs (session_id) VALUES ('stale-row')")
        conn.commit()

    db.init_db()

    with db.get_connection() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(telemetry_logs)")}
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_logs WHERE session_id = 'stale-row'"
        ).fetchone()[0]
    assert "answer_outcome" in columns
    assert count == 0


def test_init_db_drops_telemetry_table_with_a_stale_extra_column():
    """A pre-#253 shape — extra `is_correct`, nullable `answer_outcome` — no
    longer matches even though it holds every column `log_telemetry` writes today,
    since its shape now differs from `_TELEMETRY_COLUMNS`."""
    with db.get_connection() as conn:
        conn.execute("DROP TABLE telemetry_logs")
        conn.execute("""
            CREATE TABLE telemetry_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                username TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                play_mode TEXT NOT NULL,
                chapter_id INTEGER NOT NULL,
                chapter TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                input_mode TEXT NOT NULL,
                streak_before_answer INTEGER NOT NULL,
                flawless_eligible BOOLEAN NOT NULL,
                frontier_relation TEXT NOT NULL,
                answer_outcome TEXT,
                misconception_slug TEXT,
                trap_slug TEXT,
                trap_source TEXT,
                is_correct BOOLEAN NOT NULL,
                user_input TEXT,
                time_spent_ms INTEGER,
                problem_snapshot TEXT,
                problem_id TEXT
            )
        """)
        conn.commit()

    db.init_db()

    with db.get_connection() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(telemetry_logs)")}
    assert "is_correct" not in columns
