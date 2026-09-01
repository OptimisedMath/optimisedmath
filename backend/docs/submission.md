# Submission module

`submission.py` owns one Submission end-to-end. Call it from `session.py` — do not add pass-through wrappers in session or session_state.

The module's entry point grades the answer, logs telemetry, applies progression (pure rules in `progression.py`), and persists via `session_state.persist`. Internal helpers are private — keep testable but do not re-export.

Deconstruction trigger detection sits between telemetry and progression: on the second hit of the same Misconception at the current Level (`config.DECONSTRUCTION_TRIGGER_COUNT`, read from the Session's own telemetry rows), it arms `state.deconstruction` from `deconstruction.build_steps()` and writes the `deconstructions` header row plus one `deconstruction_steps` row per step (`attempts`/`revealed` at zero). `state.deconstruction.deconstruction_id` carries the header row's id so later step submissions (`deconstruction_step.py`) know which rows to update. The triggering answer is still graded as a completely normal Submission — the trigger only arms the takeover, it never short-circuits grading or progression. The trigger check shares its (Misconception, Level) key format with `deconstruction_step.deconstruction_key()`, so an armed Deconstruction and its own ending (completion or Abandonment) agree on exactly the same identity in `state.deconstructed`.

A discounted retry — `problem["problem_id"] == state.discounted_problem_id`, set by `deconstruction_step._finish()` when a Deconstruction reaches its final step — is graded and logged exactly like any other Submission, but branches around both the trigger check and normal progression: `_apply_discounted_retry_outcome()` scores XP at `config.DECONSTRUCTION_DISCOUNTED_XP_MULTIPLIER` and writes Feedback directly, leaving Streak, Flawless, and the Frontier untouched (ADR-0004). `state.discounted_problem_id` clears once the retry locks (a soft error keeps it open for another try, mirroring how a soft error never locks any other Problem).

Submission failures propagate with their original exception and context; do not wrap in generic internal errors or print-and-re-raise.
