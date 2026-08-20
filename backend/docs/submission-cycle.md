# Submission cycle

`submission_cycle.py` owns the Submission cycle choreography (see `CONTEXT.md`): begin-problem, post-Topic-completion Navigation, and the chapter-end fallback. It sits between `session.py` and `submission.py` / `session_state.py` — call it from session use-cases; do not import `session` from here.

**Cycle flag ownership:** `session_state.py` owns the Submission-cycle completion flags (`problem_answered`, `topic_completed`, `level_completed`) for their whole lifetime — `clear_submission_cycle_fields` clears them (with `reset_streak=False` as the begin-problem variant that keeps the running streak) and `record_completion` sets `level_completed`/`topic_completed` from a graded Submission's outcome. `begin_problem` calls the former instead of clearing a subset directly, so a Topic-completion flag can no longer survive into the next Problem. No other module writes these fields directly.

**Why a separate module:** `submission.py` owns one graded Submission. The cycle spans problem serving and Navigation across multiple state transitions.

**Public API:**


| Function                                                                                                       | Seam                                                                                                                                    |
| --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `navigate_to(state, play_mode, chapter_id=None, topic_id=None, level=None, curriculum=None, *, persist=True)` | Toolbar Navigation: update Selected chapter/topic/level, reset cycle, persist (`persist=False` for a caller doing one persist itself) |
| `begin_problem(state, problem, curriculum, play_mode, *, recent_fingerprints=None)`                           | Apply state mutations for a newly generated problem and persist                                                                         |
| `serve_next_problem(state, curriculum, chapter_id, topic_id, play_mode)`                                      | Generate at selection, dedupe fingerprints, begin problem                                                                               |
| `resolve_next_problem(state, curriculum, chapter_id, topic_id, play_mode)`                                    | Post-Topic-completion Navigation, chapter-end fallback, or serve next problem                                                           |

`play_mode` is required everywhere above — resolved once per request at the session use-case edge (`session.py`) and passed down; no callee re-derives it from `state.username` as a fallback.

**Chapter-end fallback:** when Topic completion leaves no next unlocked Topic, return the already-completed Problem without regenerating. 
