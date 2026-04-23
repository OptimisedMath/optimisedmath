# core/db.py
import sqlite3
import json
from pathlib import Path

# Save the database in your existing data folder
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"

def get_connection():
    # Create the data directory if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the database schema if it doesn't exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                selected_macro TEXT,
                selected_topic_order INTEGER,
                selected_level INTEGER,
                progress_json TEXT
            )
        ''')
        conn.commit()

def load_user(username):
    """Loads a user's state. Returns None if the user doesn't exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT xp, streak, selected_macro, selected_topic_order, selected_level, progress_json FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row:
            return {
                "xp": row[0],
                "streak": row[1],
                "selected_macro": row[2],
                "selected_topic_order": row[3],
                "selected_level": row[4],
                "progress": json.loads(row[5]) if row[5] else {}
            }
        return None

def save_user(username, state_dict):
    """Saves or updates the user's state in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        progress_str = json.dumps(state_dict.get("progress", {}))
        
        cursor.execute('''
            INSERT INTO users (username, xp, streak, selected_macro, selected_topic_order, selected_level, progress_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                xp=excluded.xp,
                streak=excluded.streak,
                selected_macro=excluded.selected_macro,
                selected_topic_order=excluded.selected_topic_order,
                selected_level=excluded.selected_level,
                progress_json=excluded.progress_json
        ''', (
            username, 
            state_dict.get("xp", 0), 
            state_dict.get("streak", 0),
            state_dict.get("selected_macro"),
            state_dict.get("selected_topic_order"),
            state_dict.get("selected_level"),
            progress_str
        ))
        conn.commit()