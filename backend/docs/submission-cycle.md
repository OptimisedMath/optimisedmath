# Submission cycle

`submission_cycle.py` owns the Submission cycle choreography (see `CONTEXT.md`): begin-problem, post-Topic-completion Navigation, and the chapter-end fallback. It sits between `session.py` and `submission.py` / `session_state.py` — call it from session use-cases; do not import `session` from here.

**Cycle flag ownership:** `session_state.py` owns the Submission-cycle completion flags (`problem_answered`, `topic_completed`, `level_completed`) for their whole lifetime — `reset_submission_cycle` clears them (with `reset_streak=False` as the begin-problem variant that keeps the running streak) and `mark_level_and_topic_completion` sets `level_completed`/`topic_completed` from a graded Submission's outcome. `begin_problem` calls the former instead of clearing a subset directly, so a Topic-completion flag can no longer survive into the next Problem. No other module writes these fields directly.

**Why a separate module:** `submission.py` owns one graded Submission. The cycle spans problem serving and Navigation across multiple state transitions.

`play_mode` is required everywhere in this module's public API — resolved once per request at the session use-case edge (`session.py`) and passed down; no callee re-derives it from `state.username` as a fallback. `resolve_next_problem`'s `nav_snapshot` follows the same rule: built once at the edge and threaded down into `_navigate_after_topic_completion`, which reads it and never builds its own.

**Chapter-end fallback:** when Topic completion leaves no next unlocked Topic, return the already-completed Problem without regenerating. 
