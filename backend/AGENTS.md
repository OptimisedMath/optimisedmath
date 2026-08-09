# Backend conventions

Pure Python FastAPI service — no UI framework imports.

- **Domain vocabulary:** repo-root `CONTEXT.md`
- **Game rules:** owned here only — see `docs/adr/0002-backend-owns-game-rules.md`

## Layered modules

Layers stack top-to-bottom. Each layer may import from layers below and from `models.py`. Pure rule modules never import session, state, or HTTP layers.

| Layer | Module | Owns |
|-------|--------|------|
| HTTP | `main.py` | Routes, CORS, exception → HTTP status |
| Session use-cases | `session.py` | Start, navigate, reset, submit, next problem; in-memory cache; `respond()` |
| Session state | `session_state.py` | Load/save/mutate `SessionState`; grade → progression → persist |
| Progression | `progression.py` | Streak, XP, level/topic progression per Submission (pure) |
| Access | `unlock.py` | Reachable chapter/topic/level (pure) |
| Grading | `answer_grading.py` | Correct / Trap / Wrong / soft error (pure) |
| Problems | `problem_generation.py` | Generator registry, level assembly (pure) |
| Navigation resolution | `navigation_resolution.py` | Nav intents, clamping (pure) |
| Navigation view | `navigation_view.py` | Dropdown/progress payload; reads state, never mutates |
| Curriculum | `curriculum.py`, `curriculum_loader.py` | Read model + provider; YAML load, validate, cache |
| Persistence | `core/db.py` | SQLite read/write |
| API contract | `models.py` | Pydantic request/response models |
| Config | `config.py` | Settings; `PROJECT_ROOT` is `backend/`, not repo root |

## Import rules

1. **Strict layers:** HTTP → session → state → pure rules. Pure modules never import session, state, or HTTP.
2. **`models.py` is shared:** any layer may import Pydantic types from `models.py`.
3. **`navigation_view` reads only:** may read `SessionState` from `models.py`; must not mutate state or call session use-cases.
4. **`session.py` orchestrates responses:** owns `respond()` — calls state helpers and `navigation_view.build_*`; does not embed view-building logic.
5. **`Curriculum` is injected below session:** modules below the session use-case layer receive `Curriculum` as a parameter; only HTTP/session resolve it via `resolve_curriculum()`.

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
