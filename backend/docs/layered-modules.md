# Layered modules

The stack, top to bottom. Each layer may import from layers below it, from `models.py`, and from `play_mode.py`. Pure rule modules never import session, state, or HTTP layers. What each module owns is in its own docstring.

| Layer | Module |
| ----- | ------ |
| HTTP | `main.py` |
| Session use-cases | `session.py` |
| Submission cycle | `submission_cycle.py` |
| Submission | `submission.py` |
| Session state | `session_state.py` |
| Progression | `progression.py` (pure) |
| Access | `unlock.py` (pure) |
| Grading | `answer_grading.py`, `step_grading.py` (pure) |
| Deconstruction | `deconstruction.py` (pure), `deconstruction_step.py` |
| Problems | `problem_generation.py` (pure) |
| Navigation | `navigation_snapshot.py`, `navigation_resolve.py` |
| Curriculum | `curriculum.py`, `curriculum_loader.py` |
| Persistence | `core/db.py` |
| Play mode | `play_mode.py` (shared) |
| API contract | `models.py` |
| Config | `config.py` |

`config.PROJECT_ROOT` is `backend/`, not the repo root.
