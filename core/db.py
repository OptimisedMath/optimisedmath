import sqlite3
import json
from config import DB_PATH

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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,            -- NEW: Groups events by session
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

def log_telemetry(session_id, username, macro_topic, micro_topic, level_number, is_text_mode, is_correct, user_input=None, trap_id=None, time_spent_seconds=None, equation_state=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO telemetry_logs (
                session_id, username, macro_topic, micro_topic, level_number, is_text_mode,
                trap_id, is_correct, user_input, time_spent_seconds, equation_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, username, macro_topic, micro_topic, level_number, is_text_mode,
            trap_id, is_correct, str(user_input) if user_input is not None else None, 
            time_spent_seconds, equation_state
        ))
        conn.commit()