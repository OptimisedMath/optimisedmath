"""Own the Submission cycle choreography end-to-end.

One Submission cycle is the Problem lifecycle within a Session: served →
Submission → Feedback → Next problem (see ``CONTEXT.md``). This module
consolidates orchestration currently spread across ``session.begin_problem``,
``session_state.navigate_after_topic_completion``, and (formerly)
``session_state.reset_submission_cycle`` / ``session_state.navigate_to``.

Responsibilities:

- **Cycle reset** — clear streak, feedback, and problem fields when Navigation
  or Next problem starts a fresh cycle.
- **Begin problem** — apply state mutations for a newly generated problem and
  persist (follow-up ticket).
- **Post-Topic-completion Navigation** — after Topic completion, land the
  Session on the next unlocked Topic at level 1 when Next problem unlocks one
  (follow-up ticket).
- **Chapter-end fallback** — when Topic completion leaves no next unlocked
  Topic, return the already-completed Problem without regenerating (follow-up
  ticket).

Call from ``session.py`` use-case functions; do not import ``session`` from
here. ``submission.py`` remains the owner of one graded Submission (grade →
telemetry → progression → persist).
"""

from backend.curriculum import Curriculum
from backend.models import SessionState
from backend.play_mode import PlayMode
import backend.session_state as session_state


def reset_submission_cycle(
    state: SessionState, curriculum: Curriculum | None = None
) -> None:
    """Clear the current problem state when navigating or loading the next problem."""
    session_state._clear_submission_cycle_fields(state, curriculum)


def navigate_to(
    state: SessionState,
    chapter_id: int | None = None,
    topic_id: int | None = None,
    level: int | None = None,
    curriculum: Curriculum | None = None,
    play_mode: PlayMode | None = None,
) -> None:
    """Navigate to a different chapter/topic/level, resetting submission cycle and syncing."""
    if chapter_id is not None:
        state.selected_chapter_id = chapter_id
    if topic_id is not None:
        state.selected_topic_id = topic_id
    if level is not None:
        state.selected_level = level
    reset_submission_cycle(state, curriculum)
    session_state.sync_to_db(state, play_mode)
