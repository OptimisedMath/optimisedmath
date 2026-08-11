# Backend conventions

Pure Python FastAPI service — no UI framework imports.

- **Domain vocabulary:** repo-root `CONTEXT.md`
- **Game rules:** owned here only — see `docs/adr/0002-backend-owns-game-rules.md`

## Layered modules

Layers stack top-to-bottom. Each layer may import from layers below and from `models.py`. Pure rule modules never import session, state, or HTTP layers.

| Layer | Module | Owns |
|-------|--------|------|
| HTTP | `main.py` | Routes, CORS, exception → HTTP status |
| Session use-cases | `session.py` | Start, navigate, reset, submit, next problem; in-memory cache; `respond()` owns the response view (`SessionResponse`) |
| Submission cycle | `submission_cycle.py` | Cycle reset, begin-problem, post-Topic-completion Navigation, chapter-end fallback |
| Submission | `submission.py` | Grade → telemetry → progression → persist for one Submission |
| Session state | `session_state.py` | Load/save/mutate `SessionState`; sync to DB |
| Progression | `progression.py` | Streak, XP, level/topic progression per Submission (pure) |
| Access | `unlock.py` | Reachable chapter/topic/level (pure) |
| Grading | `answer_grading.py` | Correct / Trap / Wrong / soft error (pure) |
| Problems | `problem_generation.py` | Generator registry, level assembly (pure) |
| Navigation | `navigation.py` | Snapshot, view payload, and intent resolution |
| Curriculum | `curriculum.py`, `curriculum_loader.py` | Read model + provider; YAML load, validate, cache |
| Persistence | `core/db.py` | SQLite read/write |
| API contract | `models.py` | Pydantic request/response models |
| Config | `config.py` | Settings; `PROJECT_ROOT` is `backend/`, not repo root |

## Import rules

1. **Strict layers:** HTTP → session → submission_cycle → submission → state → pure rules. Pure modules never import session, state, or HTTP.
2. **`models.py` is shared:** any layer may import Pydantic types from `models.py`.
3. **`navigation` reads only for snapshot/view:** may read `SessionState` from `models.py`; must not mutate state or call session use-cases when building snapshots or views. View payload is derived from data captured on the snapshot at construction time.
4. **`session.py` owns the response view:** `respond()` builds `SessionResponse` from persisted `SessionState` plus play mode and navigation; calls state helpers and `navigation.build_*`; does not embed view-building logic beyond assembling the payload.
5. **`Curriculum` is injected below session:** modules below the session use-case layer receive `Curriculum` as a parameter; only HTTP/session resolve it via `resolve_curriculum()`.

## Submission cycle module

`submission_cycle.py` owns the Submission cycle choreography (see `CONTEXT.md`): cycle reset, begin-problem, post-Topic-completion Navigation, and the chapter-end fallback. It sits between `session.py` and `submission.py` / `session_state.py` — call it from session use-cases; do not import `session` from here.

**Why a separate module:** `submission.py` already owns one graded Submission (answer → feedback → progression → persist). The cycle spans problem serving and Navigation across multiple state transitions; keeping it in its own module preserves that boundary and gives the parent refactor (#80) a single home for choreography without bloating `submission.py`.

**Public API:**

| Function | Seam |
|----------|------|
| `reset_submission_cycle(state, curriculum=None)` | Clear streak, feedback, and problem fields for a fresh cycle |
| `navigate_to(state, chapter_id=None, topic_id=None, level=None, curriculum=None, play_mode=None)` | Toolbar Navigation: update selection, reset cycle, persist |
| `begin_problem(state, problem, curriculum, *, recent_fingerprints=None, play_mode=None)` | Apply state mutations for a newly generated problem and persist |
| `serve_next_problem(state, curriculum, chapter_id, topic_id, play_mode=None)` | Generate at selection, dedupe fingerprints, begin problem |
| `resolve_next_problem(state, curriculum, chapter_id, topic_id, play_mode=None)` | Post-Topic-completion Navigation, chapter-end fallback, or serve next problem |

## Submission module

`submission.py` owns one Submission end-to-end. Call it from `session.py` — do not add pass-through wrappers in session or session_state.

**Public API:** `process_submission(state, problem, user_input, is_input_mode, curriculum, play_mode) -> EvalResult` — grades the answer, logs telemetry, applies progression, and persists via `session_state.sync_to_db`.

**Internal seams** (private helpers; keep testable but do not re-export):

| Helper | Seam |
|--------|------|
| `_log_submission_telemetry` | Telemetry write to `core/db.py` |
| `_apply_progression` | Pure rules in `progression.py` via `apply_submission` |
| `_resolve_feedback` | Merge grading feedback with progression overrides (once per Submission) |
| `_apply_submission_outcome` | Apply `SubmissionOutcome` + merged feedback onto `SessionState` |
| Grading | Pure `answer_grading.grade` |

Submission failures propagate with their original exception and context; do not wrap in generic internal errors or print-and-re-raise.

## Curriculum & problems

- Curriculum YAML in `backend/data/`; loaded by `curriculum_loader.py`; read model + provider in `curriculum.py`.
- Problem generators in `backend/chapters/<slug>/topic_{id}_{slug}.py` (auto-registered; `_` prefix for helpers).
- Copy an existing chapter file when adding content.

## Database

- SQLite at `backend/storage/users.db`; access via `backend/core/db.py`.

## Tests

Run from repo root — see root `AGENTS.md`. DB isolated via pytest fixtures.

## API contract

When changing request/response shapes, update `backend/models.py` and mirror in `frontend/lib/session/types.ts` (session) or `frontend/lib/types.ts` (curriculum). JSON field names are stable wire format — see `CONTEXT.md` for domain terms.

## Docstrings

Reference: `backend/session_state.py`.

**Add** for route handlers, multi-branch logic, public helpers with side effects, API models, and module docstrings on entry points. **Skip** private `_helpers` under ~5 lines, trivial one-liners, and topic generators (Polish one-liners there are fine). Default style: imperative one-liner; add `Args` / `Returns` / `Raises` when helpful. English for infrastructure; Polish for problem generators.
