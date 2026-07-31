"""SQLite persistence for users, sessions, and telemetry."""

import json
import sqlite3
from typing import TypedDict

from backend.config import DB_PATH
from backend.models import ChapterProgress, GameState

# --- Types ---


class UserData(TypedDict):
    xp: int
    streak: int
    selected_chapter_id: int | None
    selected_topic_id: int | None
    selected_level: int
    chapter_progress: dict[int, ChapterProgress]

# --- Connection ---

DB_TIMEOUT_SECONDS = 30.0


def _configure_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT_SECONDS)
    _configure_connection(conn)
    return conn


def _user_column_names(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    return {row[1] for row in cursor.fetchall()}


def _migrate_users_schema(conn: sqlite3.Connection) -> None:
    """Migrate legacy macro/micro columns to chapter/topic ids."""
    from backend.curriculum_loader import get_chapter_id_by_name

    columns = _user_column_names(conn)
    cursor = conn.cursor()

    if "selected_chapter_id" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN selected_chapter_id INTEGER")

    if "selected_topic_id" not in columns:
        if "selected_micro_topic_order" in columns:
            conn.execute(
                "ALTER TABLE users RENAME COLUMN selected_micro_topic_order TO selected_topic_id"
            )
        else:
            conn.execute("ALTER TABLE users ADD COLUMN selected_topic_id INTEGER")

    columns = _user_column_names(conn)
    if "selected_macro" in columns:
        cursor.execute(
            "SELECT username, selected_macro, selected_chapter_id FROM users"
        )
        for username, macro_name, existing_id in cursor.fetchall():
            if existing_id is not None:
                continue
            if macro_name:
                chapter_id = get_chapter_id_by_name(str(macro_name))
                if chapter_id is not None:
                    cursor.execute(
                        "UPDATE users SET selected_chapter_id = ? WHERE username = ?",
                        (chapter_id, username),
                    )
        try:
            conn.execute("ALTER TABLE users DROP COLUMN selected_macro")
        except sqlite3.OperationalError:
            pass

    cursor = conn.cursor()
    cursor.execute("SELECT username, progress_json FROM users WHERE progress_json IS NOT NULL")
    for username, progress_json in cursor.fetchall():
        if not progress_json:
            continue
        raw_progress = json.loads(progress_json)
        if not isinstance(raw_progress, dict):
            continue
        needs_migration = any(
            not str(key).isdigit()
            or (
                isinstance(value, dict)
                and "unlocked_micro_topic_order" in value
            )
            for key, value in raw_progress.items()
        )
        if not needs_migration:
            continue
        migrated_state = GameState.model_validate(
            {"username": username, "chapter_progress": raw_progress}
        )
        progress_str = json.dumps(
            {
                str(k): v.model_dump(mode="json")
                for k, v in migrated_state.chapter_progress.items()
            }
        )
        cursor.execute(
            "UPDATE users SET progress_json = ? WHERE username = ?",
            (progress_str, username),
        )

    conn.commit()

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
                progress_json TEXT
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
                macro_topic TEXT NOT NULL,
                micro_topic TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                is_text_mode BOOLEAN NOT NULL,
                trap_id TEXT,
                is_correct BOOLEAN NOT NULL,
                user_input TEXT,
                time_spent_seconds INTEGER,
                equation_state TEXT,
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
        _migrate_users_schema(conn)
        conn.commit()

# --- Sessions ---


def save_session(session_id: str, username: str, state: GameState) -> None:
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


def load_session(session_id: str) -> GameState | None:
    """Loads a session state from SQLite. Returns None if not found."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            return GameState.model_validate_json(row[0])
        return None


def delete_session(session_id: str) -> None:
    """Removes a session from the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

# --- Users ---


def load_user(username: str) -> UserData | None:
    """Loads a user's state. Returns None if the user doesn't exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        columns = _user_column_names(conn)
        if "selected_chapter_id" in columns:
            cursor.execute(
                """
                SELECT xp, streak, selected_chapter_id, selected_topic_id,
                       selected_level, progress_json
                FROM users WHERE username = ?
                """,
                (username,),
            )
        else:
            cursor.execute(
                """
                SELECT xp, streak, selected_macro, selected_micro_topic_order,
                       selected_level, progress_json
                FROM users WHERE username = ?
                """,
                (username,),
            )
        row = cursor.fetchone()

        if row:
            raw_progress = json.loads(row[5]) if row[5] else {}
            migrated = GameState.model_validate(
                {
                    "selected_chapter_id": row[2],
                    "selected_topic_id": row[3],
                    "chapter_progress": raw_progress,
                }
            )
            return {
                "xp": row[0],
                "streak": row[1],
                "selected_chapter_id": migrated.selected_chapter_id,
                "selected_topic_id": migrated.selected_topic_id,
                "selected_level": row[4],
                "chapter_progress": migrated.chapter_progress,
            }
        return None


def save_user(username: str, state: GameState) -> None:
    """Saves or updates the user's state in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        progress_str = json.dumps(
            {
                str(k): v.model_dump(mode="json")
                for k, v in state.chapter_progress.items()
            }
        )

        cursor.execute(
            """
            INSERT INTO users (
                username, xp, streak, selected_chapter_id,
                selected_topic_id, selected_level, progress_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                xp=excluded.xp,
                streak=excluded.streak,
                selected_chapter_id=excluded.selected_chapter_id,
                selected_topic_id=excluded.selected_topic_id,
                selected_level=excluded.selected_level,
                progress_json=excluded.progress_json
        """,
            (
                username,
                state.xp,
                state.streak,
                state.selected_chapter_id,
                state.selected_topic_id,
                state.selected_level,
                progress_str,
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
    is_text_mode: bool,
    is_correct: bool,
    user_input: str | None = None,
    trap_id: str | None = None,
    time_spent_seconds: int | None = None,
    equation_state: str | None = None,
) -> None:
    """Record one answer attempt for analytics and debugging."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO telemetry_logs (
                session_id, username, macro_topic, micro_topic, level_number, is_text_mode,
                trap_id, is_correct, user_input, time_spent_seconds, equation_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                username,
                chapter_name,
                topic_name,
                level_number,
                is_text_mode,
                trap_id,
                is_correct,
                str(user_input) if user_input is not None else None,
                time_spent_seconds,
                equation_state,
            ),
        )
        conn.commit()
