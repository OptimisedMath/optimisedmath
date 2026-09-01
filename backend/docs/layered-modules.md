# Layered modules

Layers stack top-to-bottom. Each layer may import from layers below, from `models.py`, and from `play_mode.py`. Pure rule modules never import session, state, or HTTP layers.


| Layer             | Module                                  | Owns                                                                                                                  |
| ----------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| HTTP              | `main.py`                               | Routes, CORS, exception → HTTP status                                                                                 |
| Session use-cases | `session.py`                            | Start, navigate, reset, submit, next problem; in-memory cache; `build_session_response()` owns the response view (`SessionResponse`) |
| Submission cycle  | `submission_cycle.py`                   | Begin-problem, post-Topic-completion Navigation, chapter-end fallback; forwards cycle flag writes to `session_state`  |
| Submission        | `submission.py`                         | Grade → telemetry → progression → persist for one Submission                                                          |
| Session state     | `session_state.py`                      | Load/save/mutate `SessionState`; sync to DB; sole owner of the Submission-cycle completion flags (set and clear)      |
| Progression       | `progression.py`                        | Streak, XP, level/topic progression per Submission (pure)                                                             |
| Access            | `unlock.py`                             | Reachable chapter/topic/level (pure)                                                                                  |
| Grading           | `answer_grading.py`                     | Correct / Trap / Wrong / soft error (pure)                                                                            |
| Grading           | `step_grading.py`                       | Deconstruction step grading — correct/incorrect, no Trap or `options_map` taxonomy (pure)                             |
| Deconstruction    | `deconstruction.py`                     | Walkthrough registry; `build_steps()` — fixed step sequence per Misconception, from Problem parameters (pure)         |
| Deconstruction    | `deconstruction_step.py`                | Grade one step, apply the Reveal, advance, persist — the Deconstruction step-submission cycle                        |
| Problems          | `problem_generation.py`                 | Generator registry, level assembly (pure)                                                                             |
| Navigation        | `navigation_snapshot.py`                | Snapshot and view payload                                                                                             |
| Navigation        | `navigation_resolve.py`                 | Intent clamping and validate-and-resolve                                                                              |
| Curriculum        | `curriculum.py`, `curriculum_loader.py` | Read model + provider; YAML load, validate, cache; topic lookup and level clamping (ADR-0003)                                                                     |
| Persistence       | `core/db.py`                            | SQLite read/write                                                                                                     |
| Play mode         | `play_mode.py`                          | Admin vs student policy; effective Frontier; profile persistence (shared)                                             |
| API contract      | `models.py`                             | Pydantic request/response models                                                                                      |
| Config            | `config.py`                             | Settings; `PROJECT_ROOT` is `backend/`, not repo root                                                                 |


