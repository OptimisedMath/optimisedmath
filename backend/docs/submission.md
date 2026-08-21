# Submission module

`submission.py` owns one Submission end-to-end. Call it from `session.py` — do not add pass-through wrappers in session or session_state.

The module's entry point grades the answer, logs telemetry, applies progression (pure rules in `progression.py`), and persists via `session_state.persist`. Internal helpers are private — keep testable but do not re-export.

Submission failures propagate with their original exception and context; do not wrap in generic internal errors or print-and-re-raise.
