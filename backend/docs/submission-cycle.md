# Submission cycle

`submission_cycle.py` owns the Submission cycle choreography (see `CONTEXT.md`): begin-problem, post-Topic-completion Navigation, and the chapter-end fallback. It sits between `session.py` and `submission.py` / `session_state.py` — call it from session use-cases; do not import `session` from here.

**Cycle reset ownership:** `session_state.clear_submission_cycle_fields` is the real owner of clearing Submission-cycle fields (streak, feedback, problem, input mode). It is called directly by `navigate_to`, `session_state.load_profile`, and `session_state.hard_reset` — no forwarding function in between.

**Why a separate module:** `submission.py` owns one graded Submission. The cycle spans problem serving and Navigation across multiple state transitions.

**Public API:**


| Function                                                                                      | Seam                                                                          |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `navigate_to(state, play_mode, chapter_id=None, topic_id=None, level=None, curriculum=None)` | Toolbar Navigation: update selection, reset cycle, persist                    |
| `begin_problem(state, problem, curriculum, play_mode, *, recent_fingerprints=None)`          | Apply state mutations for a newly generated problem and persist               |
| `serve_next_problem(state, curriculum, chapter_id, topic_id, play_mode)`                     | Generate at selection, dedupe fingerprints, begin problem                     |
| `resolve_next_problem(state, curriculum, chapter_id, topic_id, play_mode)`                   | Post-Topic-completion Navigation, chapter-end fallback, or serve next problem |

`play_mode` is required everywhere above — resolved once per request at the session use-case edge (`session.py`) and passed down; no callee re-derives it from `state.username` as a fallback.

**Chapter-end fallback:** when Topic completion leaves no next unlocked Topic, return the already-completed Problem without regenerating. 
