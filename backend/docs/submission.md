# Submission module

`submission.py` owns one Submission end-to-end. Call it from `session.py` — do not add pass-through wrappers in session or session_state.

The module's entry point grades the answer, logs telemetry, applies progression (pure rules in `progression.py`), and persists via `session_state.persist`. Internal helpers are private — keep testable but do not re-export.

Deconstruction trigger detection sits between telemetry and progression: on the second hit of the same Misconception at the current Level (`config.DECONSTRUCTION_TRIGGER_COUNT`, read from the Session's own telemetry rows), it arms `state.deconstruction` from `deconstruction.build_steps()` and writes the `deconstructions` header row. The triggering answer is still graded as a completely normal Submission — the trigger only arms the takeover, it never short-circuits grading or progression.

Submission failures propagate with their original exception and context; do not wrap in generic internal errors or print-and-re-raise.
