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
                answer_outcome TEXT NOT NULL,
                misconception_slug TEXT,
                trap_slug TEXT,
                trap_source TEXT,
                user_input TEXT,
                answer_form TEXT NOT NULL,
                answer_value_num INTEGER,
                answer_value_den INTEGER,
                correct_form TEXT NOT NULL,
                correct_value_num INTEGER,
                correct_value_den INTEGER,
                time_spent_ms INTEGER,
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


# Every telemetry_logs column `log_telemetry` writes, in INSERT order. The INSERT
# statement below is built from this list, and `_drop_stale_telemetry_table` reads
# it as the shape a pre-existing table has to match — so a new telemetry column is
# added here and to the `CREATE TABLE` above, and nowhere else.
_TELEMETRY_COLUMNS = (
    "session_id",
    "username",
    "play_mode",
    "chapter_id",
    "chapter",
    "topic_id",
    "topic",
    "level_number",
    "input_mode",
    "streak_before_answer",
    "flawless_eligible",
    "frontier_relation",
    "answer_outcome",
    "misconception_slug",
    "trap_slug",
    "trap_source",
    "user_input",
    "answer_form",
    "answer_value_num",
    "answer_value_den",
    "correct_form",
    "correct_value_num",
    "correct_value_den",
    "time_spent_ms",
    "problem_snapshot",
    "problem_id",
)

# The full column set `CREATE TABLE` declares: everything `log_telemetry` writes,
# plus the two SQLite fills in by itself — the autoincrement key and the default
# timestamp, never part of the INSERT but still part of the shape
# `_drop_stale_telemetry_table` matches a pre-existing table against.
_TELEMETRY_TABLE_COLUMNS = frozenset(_TELEMETRY_COLUMNS) | {"log_id", "timestamp"}

_INSERT_TELEMETRY_SQL = (
    f"INSERT INTO telemetry_logs ({', '.join(_TELEMETRY_COLUMNS)}) "
    f"VALUES ({', '.join('?' * len(_TELEMETRY_COLUMNS))})"
)


def _drop_stale_telemetry_table(cursor: sqlite3.Cursor) -> None:
    """Drop telemetry_logs unless its columns are exactly `_TELEMETRY_TABLE_COLUMNS`.

    Pre-existing telemetry rows are dropped, not migrated, when the schema changes
    shape — adding, renaming or removing a column is what makes that happen. An
    exact match rather than a subset check, so a column that stops being written
    (like `is_correct` in #253) also forces the drop instead of being left behind
    as dead NOT NULL state a future INSERT can't satisfy. Acceptable pre-launch,
    while telemetry has no production readers; past launch, a schema change needs
    a real migration instead of a silent drop.
    """
    table_exists = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry_logs'"
    ).fetchone()
    if not table_exists:
        return
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(telemetry_logs)")}
    if columns != _TELEMETRY_TABLE_COLUMNS:
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
            SELECT xp, selected_chapter_id, selected_topic_id,
                   selected_level, chapter_frontiers_json
            FROM users WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        xp, chapter_id, topic_id, level, frontiers_json = row
        raw_frontiers = json.loads(frontiers_json) if frontiers_json else {}
        return {
            "xp": xp,
            "selected_chapter_id": chapter_id,
            "selected_topic_id": topic_id,
            "selected_level": level,
            "chapter_frontiers": _parse_chapter_frontiers(raw_frontiers),
        }


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
                username, xp, selected_chapter_id,
                selected_topic_id, selected_level, chapter_frontiers_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                xp=excluded.xp,
                selected_chapter_id=excluded.selected_chapter_id,
                selected_topic_id=excluded.selected_topic_id,
                selected_level=excluded.selected_level,
                chapter_frontiers_json=excluded.chapter_frontiers_json
        """,
            (
                username,
                state.xp,
                state.selected_chapter_id,
                state.selected_topic_id,
                state.selected_level,
                frontiers_str,
            ),
        )
        conn.commit()


# --- Telemetry ---


def log_telemetry(
    *,
    session_id: str,
    username: str,
    play_mode: str,
    chapter_id: int,
    chapter_name: str,
    topic_id: int,
    topic_name: str,
    level_number: int,
    input_mode: str,
    streak_before_answer: int,
    flawless_eligible: bool,
    frontier_relation: str,
    answer_outcome: str,
    answer_form: str,
    correct_form: str,
    user_input: str | None = None,
    answer_value_num: int | None = None,
    answer_value_den: int | None = None,
    correct_value_num: int | None = None,
    correct_value_den: int | None = None,
    misconception_slug: str | None = None,
    trap_slug: str | None = None,
    trap_source: str | None = None,
    time_spent_ms: int | None = None,
    problem_snapshot: str | None = None,
    problem_id: str | None = None,
) -> None:
    """Record one answer attempt for analytics and debugging.

    Keyword-only: the row is too wide, and too many of its columns share a type,
    for a positional call to be readable or safe at the call site.
    """
    row: dict[str, object] = {
        "session_id": session_id,
        "username": username,
        "play_mode": play_mode,
        "chapter_id": chapter_id,
        "chapter": chapter_name,
        "topic_id": topic_id,
        "topic": topic_name,
        "level_number": level_number,
        "input_mode": input_mode,
        "streak_before_answer": streak_before_answer,
        "flawless_eligible": flawless_eligible,
        "frontier_relation": frontier_relation,
        "answer_outcome": answer_outcome,
        "misconception_slug": misconception_slug,
        "trap_slug": trap_slug,
        "trap_source": trap_source,
        "user_input": str(user_input) if user_input is not None else None,
        "answer_form": answer_form,
        "answer_value_num": answer_value_num,
        "answer_value_den": answer_value_den,
        "correct_form": correct_form,
        "correct_value_num": correct_value_num,
        "correct_value_den": correct_value_den,
        "time_spent_ms": time_spent_ms,
        "problem_snapshot": problem_snapshot,
        "problem_id": problem_id,
    }
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            _INSERT_TELEMETRY_SQL,
            tuple(row[column] for column in _TELEMETRY_COLUMNS),
        )
        conn.commit()


# --- Deconstructions ---


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
    """Sync one step's attempt count and Reveal state after a Deconstruction submit."""
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
