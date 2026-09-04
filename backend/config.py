"""Settings and tunable constants. `PROJECT_ROOT` is `backend/`, not the repo root."""

from pathlib import Path

# --- PROJECT PATHS ---
PROJECT_ROOT = Path(__file__).resolve().parent

# --- DATABASE CONFIGURATION ---
DB_PATH = PROJECT_ROOT / "storage" / "users.db"

# --- GAME MECHANICS: PROGRESSION ---
# Consecutive correct answers required to master a level (unlock the next one).
# Doubles as the streak counter ceiling and the star display limit - the counter
# resets on mastery, so it can never exceed this value.
MAX_STREAK = 3

# Streak count required to enable input mode (instead of radio mode)
STREAK_THRESHOLD_FOR_INPUT_MODE = 1

# --- GAME MECHANICS: DECONSTRUCTION ---
# Hits on the same Misconception at the current Level before a Deconstruction
# triggers. Generic repeated failure is deliberately not a trigger.
DECONSTRUCTION_TRIGGER_COUNT = 2

# Wrong (non-soft) answers on the same Deconstruction step before the Reveal.
# Global — per-step and per-Misconception thresholds are rejected, since no
# author has evidence to set them.
DECONSTRUCTION_REVEAL_THRESHOLD = 3

# XP multiplier for the discounted second attempt a completed Deconstruction
# unlocks on its triggering Problem. Streak, Flawless, and the Frontier are
# untouched by that attempt — only XP scores, and at a discount.
DECONSTRUCTION_DISCOUNTED_XP_MULTIPLIER = 0.5

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

# Bonus XP awarded for completing a level flawlessly (0 mistakes from streak 0 to 3)
FLAWLESS_LEVEL_BONUS = 50

# --- PROBLEM GENERATION ---
# Maximum attempts to generate a mathematically valid, unique problem
MAX_RETRIES_GENERATE = 50

# Maximum attempts to fetch a problem that hasn't been shown in current session
MAX_RETRIES_DUPLICATE_CHECK = 10

# Number of recent problem fingerprints retained per session for duplicate checks
RECENT_FINGERPRINT_HISTORY_SIZE = 10

# --- ERROR MESSAGES & FEEDBACK ---
DEFAULT_WRONG_MESSAGE = "Niepoprawna odpowiedź, spróbuj ponownie."

# --- DEVELOPMENT TOOLS ---
# Keep answer-revealing helper endpoints disabled unless explicitly enabled.
ENABLE_DEV_TOOLS = False

# Usernames that receive admin mode (all topics unlocked + auto-solve).
ADMIN_USERNAMES = frozenset({"Antoni", "Antonio", "Tony"})


def is_admin_user(username: str | None) -> bool:
    if not username:
        return False
    return username.strip() in ADMIN_USERNAMES
