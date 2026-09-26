"""SQLite persistence for users, sessions, and telemetry."""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, TypedDict

from backend.config import DB_PATH
from backend.models import AnswerOutcome, ChapterFrontier, SessionState

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
        _drop_stale_tables(cursor)
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
                ended_at DATETIME,
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
                revealed BOOLEAN NOT NULL DEFAULT 0,
                PRIMARY KEY (deconstruction_id, step_index),
                FOREIGN KEY (deconstruction_id) REFERENCES deconstructions(deconstruction_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deconstruction_attempts (
                deconstruction_id INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                attempt_index INTEGER NOT NULL,
                user_input TEXT NOT NULL,
                answer_form TEXT NOT NULL,
                answer_value_num INTEGER,
                answer_value_den INTEGER,
                outcome TEXT NOT NULL,
                time_spent_ms INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (deconstruction_id, step_index, attempt_index),
                FOREIGN KEY (deconstruction_id) REFERENCES deconstructions(deconstruction_id)
            )
        """)
        conn.commit()


# Every telemetry_logs column `log_telemetry` writes, in INSERT order. The INSERT
# statement below is built from this list, and `_TABLE_COLUMNS` folds it into the
# shape a pre-existing table has to match — so a new telemetry column is added here
# and to the `CREATE TABLE` above, and nowhere else.
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

_INSERT_TELEMETRY_SQL = (
    f"INSERT INTO telemetry_logs ({', '.join(_TELEMETRY_COLUMNS)}) "
    f"VALUES ({', '.join('?' * len(_TELEMETRY_COLUMNS))})"
)

# The full column set each `CREATE TABLE` above declares — `_is_stale`'s reference for
# what a pre-existing table has to match. Spelled out rather than derived from the DDL,
# so it also names the columns SQLite fills in by itself: an autoincrement key and a
# default timestamp are never part of an INSERT, but they are part of the shape a table
# is matched against. A table changing shape means editing its `CREATE TABLE` and its
# column set here, and nowhere else.
_TABLE_COLUMNS = {
    "telemetry_logs": frozenset(_TELEMETRY_COLUMNS) | {"log_id", "timestamp"},
    "deconstructions": frozenset(
        {
            "deconstruction_id",
            "session_id",
            "username",
            "problem_id",
            "misconception_slug",
            "chapter",
            "topic",
            "level_number",
            "outcome",
            "created_at",
            "ended_at",
        }
    ),
    "deconstruction_steps": frozenset({"deconstruction_id", "step_index", "revealed"}),
    "deconstruction_attempts": frozenset(
        {
            "deconstruction_id",
            "step_index",
            "attempt_index",
            "user_input",
            "answer_form",
            "answer_value_num",
            "answer_value_den",
            "outcome",
            "time_spent_ms",
            "timestamp",
        }
    ),
}


# Tables that are dropped and recreated together, each group listed children before
# parents. One stale table takes its whole group with it: `PRAGMA foreign_keys=ON`
# refuses to drop a parent while a child row still references it, and a child row that
# outlived its parent would point at a `deconstruction_id` the recreated header table
# is free to hand out again.
_TABLE_GROUPS = (
    ("telemetry_logs",),
    ("deconstruction_attempts", "deconstruction_steps", "deconstructions"),
)


def _is_stale(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """Whether `table_name` exists with columns other than `_TABLE_COLUMNS` declares.

    An exact match rather than a subset check, so a column that stops being written
    (like `is_correct` in #253, or `deconstruction_steps.attempts` in #258) also
    counts as stale instead of being left behind as dead state a future INSERT
    can't satisfy.

    Raises `KeyError` for a table `_TABLE_COLUMNS` does not declare — looked up
    before the name reaches SQL, since `PRAGMA` cannot take it as a bound parameter.
    """
    expected_columns = _TABLE_COLUMNS[table_name]
    table_exists = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    if not table_exists:
        return False
    columns = {row[1] for row in cursor.execute(f"PRAGMA table_info({table_name})")}
    return columns != expected_columns


def _drop_stale_tables(cursor: sqlite3.Cursor) -> None:
    """Drop every `_TABLE_GROUPS` group holding a table whose shape has changed.

    Pre-existing rows are dropped, not migrated, when a table's schema changes
    shape — adding, renaming or removing a column is what makes that happen.
    Acceptable pre-launch, while these tables have no production readers; past
    launch, a schema change needs a real migration instead of a silent drop.
    Runs before every `CREATE TABLE IF NOT EXISTS` in `init_db`, which is what
    puts the new shape back.
    """
    for group in _TABLE_GROUPS:
        if not any(_is_stale(cursor, table_name) for table_name in group):
            continue
        for table_name in group:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")


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


def _value_columns(
    answer_value: tuple[int, int] | None,
) -> tuple[int | None, int | None]:
    """Split an Answer value into its two integer columns, NULL when there is none.

    Storing a rational as a numerator and a denominator is this layer's detail, so
    callers hand over the Answer value whole — an absent one included (ADR-0016).
    """
    return answer_value if answer_value is not None else (None, None)


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
    answer_outcome: AnswerOutcome,
    answer_form: str,
    correct_form: str,
    user_input: str | None = None,
    answer_value: tuple[int, int] | None = None,
    correct_value: tuple[int, int] | None = None,
    misconception_slug: str | None = None,
    trap_slug: str | None = None,
    trap_source: str | None = None,
    time_spent_ms: int | None = None,
    problem_snapshot: str | None = None,
    problem_id: str | None = None,
) -> None:
    """Record one answer attempt for analytics and debugging.

    Keyword-only: the row is too wide, and too many of its columns share a type,
    for a positional call to be readable or safe at the call site. Both Answer
    values arrive as the rationals they are — see `_value_columns`.
    """
    answer_value_num, answer_value_den = _value_columns(answer_value)
    correct_value_num, correct_value_den = _value_columns(correct_value)
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

    `revealed` starts at zero — a Step-submit sets it once the Reveal threshold
    is hit. The attempt count that used to live here is gone (#258): it is now
    derivable from `deconstruction_attempts`, excluding `soft_error` rows.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO deconstruction_steps (deconstruction_id, step_index, revealed)
            VALUES (?, ?, 0)
            """,
            [(deconstruction_id, step_index) for step_index in range(step_count)],
        )
        conn.commit()


def set_deconstruction_outcome(deconstruction_id: int, outcome: str) -> None:
    """Write the terminal `outcome` and `ended_at` on a `deconstructions` header row.

    Called once, whichever way the Deconstruction ends: `completed`,
    `abandoned_via_control`, or `abandoned_via_navigation` — the same call
    stamps `ended_at` on all three (#258), so a long walkthrough can be checked
    against whether it was the abandoned one.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE deconstructions SET outcome = ?, ended_at = CURRENT_TIMESTAMP
            WHERE deconstruction_id = ?
            """,
            (outcome, deconstruction_id),
        )
        conn.commit()


def update_deconstruction_step(
    deconstruction_id: int, step_index: int, *, revealed: bool
) -> None:
    """Sync one step's Reveal state after a Deconstruction submit."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE deconstruction_steps SET revealed = ?
            WHERE deconstruction_id = ? AND step_index = ?
            """,
            (revealed, deconstruction_id, step_index),
        )
        conn.commit()


def create_deconstruction_attempt(
    deconstruction_id: int,
    step_index: int,
    *,
    user_input: str,
    answer_form: str,
    answer_value: tuple[int, int] | None,
    outcome: AnswerOutcome,
    time_spent_ms: int | None,
) -> None:
    """Write one `deconstruction_attempts` row for a single step submit.

    `attempt_index` is assigned here, one past the step's highest one so far,
    rather than tracked in Session state — the ordinal is a property of what
    is actually persisted, not a second counter that could drift from it.
    Every submit gets a row, soft errors included, so the Reveal-threshold
    count stays recoverable as this table's rows excluding `soft_error`.
    """
    value_num, value_den = _value_columns(answer_value)
    with get_connection() as conn:
        cursor = conn.cursor()
        next_index = cursor.execute(
            """
            SELECT COALESCE(MAX(attempt_index), 0) + 1 FROM deconstruction_attempts
            WHERE deconstruction_id = ? AND step_index = ?
            """,
            (deconstruction_id, step_index),
        ).fetchone()[0]
        cursor.execute(
            """
            INSERT INTO deconstruction_attempts (
                deconstruction_id, step_index, attempt_index, user_input,
                answer_form, answer_value_num, answer_value_den, outcome,
                time_spent_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deconstruction_id,
                step_index,
                next_index,
                user_input,
                answer_form,
                value_num,
                value_den,
                outcome,
                time_spent_ms,
            ),
        )
        conn.commit()
