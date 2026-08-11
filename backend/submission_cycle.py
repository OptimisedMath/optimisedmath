"""Own the Submission cycle choreography end-to-end.

One Submission cycle is the Problem lifecycle within a Session: served →
Submission → Feedback → Next problem (see ``CONTEXT.md``). This module will
consolidate the orchestration currently spread across ``session.begin_problem``,
``session_state.reset_submission_cycle``, ``session_state.navigate_to``, and
``session_state.navigate_after_topic_completion``.

Responsibilities (to be wired in follow-up tickets):

- **Cycle reset** — clear streak, feedback, and problem fields when Navigation
  or Next problem starts a fresh cycle.
- **Begin problem** — apply state mutations for a newly generated problem and
  persist.
- **Post-Topic-completion Navigation** — after Topic completion, land the
  Session on the next unlocked Topic at level 1 when Next problem unlocks one.
- **Chapter-end fallback** — when Topic completion leaves no next unlocked
  Topic, return the already-completed Problem without regenerating.

Call from ``session.py`` use-case functions; do not import ``session`` from
here. ``submission.py`` remains the owner of one graded Submission (grade →
telemetry → progression → persist).
"""
