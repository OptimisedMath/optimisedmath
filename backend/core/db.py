"""SQLite persistence for users, sessions, and telemetry."""

import json
import sqlite3

from fastapi.encoders import jsonable_encoder

from backend.config import DB_PATH
from backend.models import GameState, TopicProgress

# --- Connection ---


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

# --- Schema ---


def init_db():
    """Initializes the database schema if it doesn't exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                selected_macro TEXT,
                selected_micro_topic_order INTEGER,
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
        conn.commit()

# --- Sessions ---


def save_session(session_id, username, state: GameState):
    """Persists a full session state to SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        state_json = json.dumps(jsonable_encoder(state.model_dump(mode="json")))
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


def load_session(session_id) -> GameState | None:
    """Loads a session state from SQLite. Returns None if not found."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            data = json.loads(row[0])
            return GameState.from_storage(data)
        return None


def delete_session(session_id):
    """Removes a session from the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

# --- Users ---


def load_user(username):
    """Loads a user's state. Returns None if the user doesn't exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
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
            progress = {}
            for macro, prog_data in raw_progress.items():
                if isinstance(prog_data, dict):
                    progress[macro] = TopicProgress(**prog_data)
                else:
                    progress[macro] = prog_data

            return {
                "xp": row[0],
                "streak": row[1],
                "selected_macro": row[2],
                "selected_micro_topic_order": row[3],
                "selected_level": row[4],
                "progress": progress,
            }
        return None


def save_user(username, state: GameState):
    """Saves or updates the user's state in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        progress_str = json.dumps(
            jsonable_encoder({k: v.model_dump() for k, v in state.progress.items()})
        )

        cursor.execute(
            """
            INSERT INTO users (
                username, xp, streak, selected_macro,
                selected_micro_topic_order, selected_level, progress_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                xp=excluded.xp,
                streak=excluded.streak,
                selected_macro=excluded.selected_macro,
                selected_micro_topic_order=excluded.selected_micro_topic_order,
                selected_level=excluded.selected_level,
                progress_json=excluded.progress_json
        """,
            (
                username,
                state.xp,
                state.streak,
                state.selected_macro,
                state.selected_micro_topic_order,
                state.selected_level,
                progress_str,
            ),
        )
        conn.commit()

# --- Telemetry ---


def log_telemetry(
    session_id,
    username,
    macro_topic,
    micro_topic,
    level_number,
    is_text_mode,
    is_correct,
    user_input=None,
    trap_id=None,
    time_spent_seconds=None,
    equation_state=None,
):
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
                macro_topic,
                micro_topic,
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
