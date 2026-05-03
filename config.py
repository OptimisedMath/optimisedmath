# config.py
# Central configuration file for the Math Learning App
# Pure Python - no UI framework imports

from pathlib import Path

# --- PROJECT PATHS ---
# Absolute project root - works regardless of where imports are called from
PROJECT_ROOT = Path(__file__).resolve().parent

# --- DATABASE CONFIGURATION ---
DB_PATH = PROJECT_ROOT / "data" / "users.db"

# --- CSV PARSING SETTINGS ---
CSV_SEPARATOR = ";"
CSV_ENCODING = "utf-8"

# --- GAME MECHANICS: PROGRESSION ---
# Threshold of consecutive correct answers needed to unlock the next level
STARS_FOR_UNLOCK = 3

# Maximum streak counter (display limit)
MAX_STREAK = 3

# Streak count required to enable free-text input mode (instead of multiple choice)
STREAK_THRESHOLD_FOR_TEXT_MODE = 1

# --- GAME MECHANICS: REWARDS ---
# XP (Experience Points) awarded for correct answers by level
XP_REWARDS = {
    1: 5,
    2: 10,
    3: 20,
    4: 35,
    5: 60,
}

# Default XP for correct answers at levels not explicitly defined in XP_REWARDS
DEFAULT_XP_REWARD = 15

# --- PROBLEM GENERATION ---
# Maximum attempts to generate a mathematically valid, unique problem
MAX_RETRIES_GENERATE = 50

# Maximum attempts to fetch a problem that hasn't been shown in current session
MAX_RETRIES_DUPLICATE_CHECK = 10

# --- ERROR MESSAGES & FEEDBACK ---
DEFAULT_WRONG_MESSAGE = "Niepoprawna odpowiedź, spróbuj ponownie."
