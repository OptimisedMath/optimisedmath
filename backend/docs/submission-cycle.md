# Submission cycle

`submission_cycle.py` owns the Submission cycle choreography (see `CONTEXT.md`): begin-problem, post-Topic-completion Navigation, and the chapter-end fallback. It sits between `session.py` and `submission.py` / `session_state.py` — call it from session use-cases; do not import `session` from here.

**Cycle reset ownership:** `session_state.clear_submission_cycle_fields` is the real owner of clearing Submission-cycle fields (streak, feedback, problem, input mode). `submission_cycle.reset_submission_cycle` is a documented forwarding seam that session use-cases call; `session_state.load_profile` and `session_state.hard_reset` call the same public helper directly.

**Why a separate module:** `submission.py` owns one graded Submission. The cycle spans problem serving and Navigation across multiple state transitions.

**Public API:**


| Function                                                                                          | Seam                                                                          |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `reset_submission_cycle(state, curriculum=None)`                                                  | Forward to `session_state.clear_submission_cycle_fields` for a fresh cycle    |
| `navigate_to(state, chapter_id=None, topic_id=None, level=None, curriculum=None, play_mode=None)` | Toolbar Navigation: update selection, reset cycle, persist                    |
| `begin_problem(state, problem, curriculum, *, recent_fingerprints=None, play_mode=None)`          | Apply state mutations for a newly generated problem and persist               |
| `serve_next_problem(state, curriculum, chapter_id, topic_id, play_mode=None)`                     | Generate at selection, dedupe fingerprints, begin problem                     |
| `resolve_next_problem(state, curriculum, chapter_id, topic_id, play_mode=None)`                   | Post-Topic-completion Navigation, chapter-end fallback, or serve next problem |

**Chapter-end fallback:** when Topic completion leaves no next unlocked Topic, return the already-completed Problem without regenerating. 