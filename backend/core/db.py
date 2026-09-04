"""SQLite persistence for users, sessions, and telemetry."""

import json
import sqlite3
from collections.abc import Generator
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
def get_connection() -> Generator[sqlite3.Connection, None, None]:
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
                problem_snapshot TEXT,
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deconstructions (
                deconstruction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                username TEXT NOT NULL,
                problem_id TEXT,
                misconception_slug TEXT NOT NULL,
                chapter TEXT NOT NULL,
                topic TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                outcome TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deconstructions_session_id ON deconstructions(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deconstructions_problem_id ON deconstructions(problem_id)"
        )
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deconstruction_steps (
                deconstruction_id INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                revealed BOOLEAN NOT NULL DEFAULT 0,
                PRIMARY KEY (deconstruction_id, step_index),
                FOREIGN KEY (deconstruction_id) REFERENCES deconstructions(deconstruction_id)
            )
        """)
        conn.commit()


def _drop_stale_telemetry_table(cursor: sqlite3.Cursor) -> None:
    """Drop telemetry_logs if it predates the misconception_slug/trap_slug/problem_id/
    problem_snapshot columns.

    Pre-existing telemetry rows are dropped, not migrated, when the schema changes shape.
    """
    table_exists = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry_logs'"
    ).fetchone()
    if not table_exists:
        return
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(telemetry_logs)")}
    required = {"misconception_slug", "trap_slug", "problem_id", "problem_snapshot"}
    if not required.issubset(columns):
        cursor.execute("DROP TABLE telemetry_logs")


# --- Sessions ---


def save_session(session_id: str, username: str, state: SessionState) -> None:
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
    problem_snapshot: str | None = None,
    problem_id: str | None = None,
) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO telemetry_logs (
                session_id, username, chapter, topic, level_number, is_input_mode,
                answer_outcome, misconception_slug, trap_slug, is_correct, user_input,
                time_spent_seconds, problem_snapshot, problem_id
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
                problem_snapshot,
                problem_id,
            ),
        )
        conn.commit()


# --- Deconstructions ---


def count_misconception_hits(
    session_id: str,
    misconception_slug: str,
    chapter_name: str,
    topic_name: str,
    level_number: int,
) -> int:
    """Count this Session's telemetry hits for one Misconception at one Level.

    The per-Level hit counter the trigger reads is derived from `telemetry_logs`
    rather than stored on `SessionState` — a Level change naturally starts it
    fresh, since rows for a different Level never match this query.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM telemetry_logs
            WHERE session_id = ? AND misconception_slug = ?
              AND chapter = ? AND topic = ? AND level_number = ?
            """,
            (session_id, misconception_slug, chapter_name, topic_name, level_number),
        )
        return int(cursor.fetchone()[0])


def create_deconstruction(
    session_id: str,
    username: str,
    problem_id: str | None,
    misconception_slug: str,
    chapter_name: str,
    topic_name: str,
    level_number: int,
) -> int:
    """Write the `deconstructions` header row at trigger detection, before the pause.

    `outcome` starts NULL so a Student who leaves during the pause is still counted.
    Returns the new row's id, so the caller can key its `deconstruction_steps` rows.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO deconstructions (
                session_id, username, problem_id, misconception_slug,
                chapter, topic, level_number, outcome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
        """,
            (
                session_id,
                username,
                problem_id,
                misconception_slug,
                chapter_name,
                topic_name,
                level_number,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        assert new_id is not None
        return new_id


def create_deconstruction_steps(deconstruction_id: int, step_count: int) -> None:
    """Write one `deconstruction_steps` row per step at trigger detection.

    `attempts` and `revealed` start at zero — a Step-submit updates them as the
    Student answers, so the row tracks the whole escalation, not just its end state.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO deconstruction_steps (deconstruction_id, step_index, attempts, revealed)
            VALUES (?, ?, 0, 0)
            """,
            [(deconstruction_id, step_index) for step_index in range(step_count)],
        )
        conn.commit()


def set_deconstruction_outcome(deconstruction_id: int, outcome: str) -> None:
    """Write the terminal `outcome` on a `deconstructions` header row.

    Called once, whichever way the Deconstruction ends: `completed`,
    `abandoned_via_control`, or `abandoned_via_navigation`.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE deconstructions SET outcome = ? WHERE deconstruction_id = ?",
            (outcome, deconstruction_id),
        )
        conn.commit()


def update_deconstruction_step(
    deconstruction_id: int, step_index: int, *, attempts: int, revealed: bool
) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE deconstruction_steps SET attempts = ?, revealed = ?
            WHERE deconstruction_id = ? AND step_index = ?
            """,
            (attempts, revealed, deconstruction_id, step_index),
        )
        conn.commit()
