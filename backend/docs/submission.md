# Submission module

`submission.py` owns one Submission end-to-end. Call it from `session.py` — do not add pass-through wrappers in session or session_state.

**Public API:** `process_submission(state, problem, user_input, is_input_mode, curriculum, play_mode) -> EvalResult` — grades the answer, logs telemetry, applies progression, and persists via `session_state.persist`.

**Internal seams** (private helpers; keep testable but do not re-export):

| Helper | Seam |
|--------|------|
| `_log_submission_telemetry` | Telemetry write to `core/db.py` |
| `_apply_progression` | Pure rules in `progression.py` via `apply_submission` |
| `_resolve_feedback` | Merge grading feedback with progression overrides (once per Submission) |
| `_apply_submission_outcome` | Apply `SubmissionOutcome` + merged feedback onto `SessionState` |
| Grading | Pure `answer_grading.grade` |

Submission failures propagate with their original exception and context; do not wrap in generic internal errors or print-and-re-raise.
