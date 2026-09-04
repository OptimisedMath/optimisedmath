# Submission cycle

Rules for `submission_cycle.py`, which owns the Submission cycle choreography (see [CONTEXT.md](../../CONTEXT.md)).

**Why it is separate from `submission.py`:** `submission.py` owns one graded Submission; the cycle spans problem serving and Navigation across several state transitions.

1. **Call it from session use-cases.** Never import `session` from here.
2. **`session_state.py` owns the cycle completion flags** — `problem_answered`, `topic_completed`, `level_completed` — for their whole lifetime, setting and clearing them. No other module writes these fields directly. Callers that need them cleared call `reset_submission_cycle`, never a subset by hand, so a Topic-completion flag cannot survive into the next Problem.
3. **`session_state.lift_answer_lock()` is the one exception**, used by `deconstruction_step._finish()` on a completed Deconstruction. It delegates to `reset_submission_cycle` and restores `current_problem` to the same instance, so the discounted retry answers the Problem the Student was on.
4. **`play_mode` and `nav_snapshot` are resolved once at the session use-case edge and threaded down.** Required everywhere in this module's public API; no callee re-derives `play_mode` from `state.username` or builds its own snapshot.
5. **Navigation ends a running Deconstruction first.** `navigate_to` calls `abandon_via_navigation()` before touching selection or resetting the cycle — toolbar Navigation is one of Abandonment's two doors, and the two differ only in the `outcome` recorded on the `deconstructions` row.
6. **Chapter-end fallback:** when Topic completion leaves no next unlocked Topic, return the already-completed Problem rather than regenerating.
