"""SQLite persistence for users, sessions, and telemetry."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, TypedDict

from backend.config import DB_PATH
from backend.models import ChapterFrontier, SessionState

# --- Types ---


class UserData(TypedDict):
    xp: int
    streak: int
    selected_chapter_id: int | None
    selected_topic_id: int | None
    selected_level: int
    chapter_frontiers: dict[int, ChapterFrontier]


# --- Connection ---

DB_TIMEOUT_SECONDS = 30.0


def _configure_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection and always close it when the block exits."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH.resolve()), timeout=DB_TIMEOUT_SECONDS)
    _configure_connection(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Schema ---


def init_db() -> None:
    """Initializes the database schema if it doesn't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                selected_chapter_id INTEGER,
                selected_topic_id INTEGER,
                selected_level INTEGER,
                chapter_frontiers_json TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                state_json TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        _drop_stale_telemetry_table(cursor)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                username TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                chapter TEXT NOT NULL,
                topic TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                is_input_mode BOOLEAN NOT NULL,
                answer_outcome TEXT,
                misconception_slug TEXT,
                trap_slug TEXT,
                is_correct BOOLEAN NOT NULL,
                user_input TEXT,
                time_spent_seconds INTEGER,
                equation_state TEXT,
                problem_id TEXT,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_telemetry_username ON telemetry_logs(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_telemetry_session_id ON telemetry_logs(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_logs(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_telemetry_problem_id ON telemetry_logs(problem_id)"
        )
        conn.commit()


def _drop_stale_telemetry_table(cursor: sqlite3.Cursor) -> None:
    """Drop telemetry_logs if it predates the misconception_slug/trap_slug/problem_id columns.

    Pre-existing telemetry rows are dropped, not migrated, when the schema changes shape.
    """
    table_exists = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry_logs'"
    ).fetchone()
    if not table_exists:
        return
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(telemetry_logs)")}
    required = {"misconception_slug", "trap_slug", "problem_id"}
    if not required.issubset(columns):
        cursor.execute("DROP TABLE telemetry_logs")


# --- Sessions ---


def save_session(session_id: str, username: str, state: SessionState) -> None:
    """Persists a full session state to SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        state_json = state.to_storage()
        cursor.execute(
            """
            INSERT INTO sessions (session_id, username, state_json, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                state_json=excluded.state_json,
                updated_at=CURRENT_TIMESTAMP
        """,
            (session_id, username, state_json),
        )
        conn.commit()


def load_session(session_id: str) -> SessionState | None:
    """Loads a session state from SQLite. Returns None if not found."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            return SessionState.model_validate_json(row[0])
        return None


def delete_session(session_id: str) -> None:
    """Removes a session from the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()


# --- Users ---


def _parse_chapter_frontiers(
    raw_frontiers: dict[str, Any],
) -> dict[int, ChapterFrontier]:
    return {
        int(chapter_id): ChapterFrontier.model_validate(frontier)
        for chapter_id, frontier in raw_frontiers.items()
    }


def load_user(username: str) -> UserData | None:
    """Loads a user's state. Returns None if the user doesn't exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT xp, streak, selected_chapter_id, selected_topic_id,
                   selected_level, chapter_frontiers_json
            FROM users WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()

        if row:
            raw_frontiers = json.loads(row[5]) if row[5] else {}
            return {
                "xp": row[0],
                "streak": row[1],
                "selected_chapter_id": row[2],
                "selected_topic_id": row[3],
                "selected_level": row[4],
                "chapter_frontiers": _parse_chapter_frontiers(raw_frontiers),
            }
        return None


def save_user(username: str, state: SessionState) -> None:
    """Saves or updates the user's state in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        frontiers_str = json.dumps(
            {
                str(k): v.model_dump(mode="json")
                for k, v in state.chapter_frontiers.items()
            }
        )

        cursor.execute(
            """
            INSERT INTO users (
                username, xp, streak, selected_chapter_id,
                selected_topic_id, selected_level, chapter_frontiers_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                xp=excluded.xp,
                streak=excluded.streak,
                selected_chapter_id=excluded.selected_chapter_id,
                selected_topic_id=excluded.selected_topic_id,
                selected_level=excluded.selected_level,
                chapter_frontiers_json=excluded.chapter_frontiers_json
        """,
            (
                username,
                state.xp,
                state.streak,
                state.selected_chapter_id,
                state.selected_topic_id,
                state.selected_level,
                frontiers_str,
            ),
        )
        conn.commit()


# --- Telemetry ---


def log_telemetry(
    session_id: str,
    username: str,
    chapter_name: str,
    topic_name: str,
    level_number: int,
    is_input_mode: bool,
    is_correct: bool,
    user_input: str | None = None,
    answer_outcome: str | None = None,
    misconception_slug: str | None = None,
    trap_slug: str | None = None,
    time_spent_seconds: int | None = None,
    equation_state: str | None = None,
    problem_id: str | None = None,
) -> None:
    """Record one answer attempt for analytics and debugging."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO telemetry_logs (
                session_id, username, chapter, topic, level_number, is_input_mode,
                answer_outcome, misconception_slug, trap_slug, is_correct, user_input,
                time_spent_seconds, equation_state, problem_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                username,
                chapter_name,
                topic_name,
                level_number,
                is_input_mode,
                answer_outcome,
                misconception_slug,
                trap_slug,
                is_correct,
                str(user_input) if user_input is not None else None,
                time_spent_seconds,
                equation_state,
                problem_id,
            ),
        )
        conn.commit()
