# Backend conventions

Pure Python FastAPI service — no UI framework imports.

Domain vocabulary lives in repo-root `CONTEXT.md`. This file records **module boundaries** and agent conventions for the backend.

## Target module architecture

Layers stack top-to-bottom. Each layer may import from layers below and from `models.py`. Pure rule modules never import session, state, or HTTP layers.

| Layer | Target module | Owns |
|-------|---------------|------|
| **HTTP** | `main.py` | Routes, CORS, request/response wiring, exception → HTTP status mapping |
| **Session use-cases** | `session.py` | Start, navigate, reset, submit, next problem; in-memory session cache; unlock guards; `respond()` (attach navigation view to API-safe state); `begin_problem()` |
| **Session state** | `session_state.py` | Load/save/mutate `SessionState`; wire grading → progression → persistence |
| **Progression rules** | `mastery_loop.py` | Streak, XP, level/topic progression for one Submission (pure) |
| **Access rules** | `unlock.py` | Reachable chapter/topic/level (pure) |
| **Grading** | `answer_grading.py` | Correct / Trap / Wrong / soft error (pure) |
| **Problems** | `problem_generation.py` | Generator registry, level assembly (pure) |
| **Navigation resolution** | `navigation_resolution.py` *(split from `navigation.py`)* | Resolve nav intents: chapter/topic/level changes, clamping |
| **Navigation view** | `navigation_view.py` *(split from `navigation.py`)* | Build dropdown/progress payload for API responses; reads `SessionState`, never mutates |
| **Curriculum** | `curriculum_loader.py` | YAML load, validate, cache |
| **Persistence** | `core/db.py` | SQLite read/write |
| **API contract** | `models.py` | Pydantic request/response models — single module, no split |
| **Config** | `config.py` | Settings; `PROJECT_ROOT` resolves to `backend/`, not monorepo root |

**Remove:** `engine.py` facade — callers import `answer_grading` and `problem_generation` directly.

## Import rules

1. **Strict layers:** HTTP → session → state → pure rules. Pure modules never import session, state, or HTTP.
2. **`models.py` is shared:** any layer may import Pydantic types from `models.py`.
3. **`navigation_view` reads only:** may read `SessionState` shapes from `models.py`; must not mutate state or call session use-cases.
4. **`session.py` orchestrates responses:** owns `respond()` — calls state helpers and `navigation_view.build_*`; does not embed view-building logic.

## Vocabulary (internal renames)

JSON keys and HTTP routes stay unchanged. Rename Python/TypeScript identifiers only.

| Current (code) | Target (code) | CONTEXT term |
|----------------|---------------|--------------|
| `SessionState` (Python) / `GameState` (frontend) | `SessionState` everywhere | Session |
| `TurnContext`, `TurnOutcome`, `apply_turn` | `SubmissionContext`, `SubmissionOutcome`, `apply_submission` | Submission |
| `flawless_eligible` | align with **Flawless** concept | Flawless |
| `engine.py` | removed | — |

## Refactor execution order

Bottom-up — each step leaves all tests green:

1. Remove `engine.py` facade; update imports to `answer_grading` / `problem_generation` directly
2. Rename Turn → Submission in pure modules (`mastery_loop.py`, then callers)
3. ~~`state_manager.py` → `session_state.py`~~ — done: module-level functions, Submission renames (see below)
4. ~~`session_orchestrator.py` → `session.py` + `SessionError` hierarchy~~ — done: `begin_problem()` extracted
5. ~~Split `navigation.py` → `navigation_resolution.py` + `navigation_view.py`~~ — done
6. ~~Rename `GameState` → `SessionState` in Python~~ ✓ — mirror in frontend `lib/session/` (separate ticket)
7. Frontend: hooks + `lib/session/` per wayfinder ticket 03

First two steps are separate PRs: (1) facade removal, (2) Submission rename.

## `session_state.py` public surface

Single deep module — no file split. Drop the `StateManager` class; expose module-level functions. Persistence stays in `core/db.py`; this layer calls it via `sync_to_db`.

| Function | Responsibility |
|----------|----------------|
| `init_defaults(state, chapter_ids, curriculum)` | Heal/create fresh session fields + chapter progress |
| `load_profile(state, username, chapter_ids, curriculum)` | Hydrate from DB or hard-reset new user |
| `sync_to_db(state)` | Persist user + session rows |
| `hard_reset(state, chapter_ids, curriculum)` | Wipe progress, reset submission cycle, sync |
| `navigate_to(state, *, chapter_id, topic_id, level, topics_by_id)` | Update selection, reset submission cycle, sync |
| `reset_submission_cycle(state, topics_by_id?)` | Clear streak/feedback/problem; recalc input mode *(was `reset_turn`)* |
| `resolve_input_mode(state, topics_by_id)` | Radio vs input from streak + topic config |
| `process_submission(state, problem, user_input, is_input_mode, topics_by_id)` | Grade → telemetry → `apply_submission` → sync |

Private helpers: `_get_first_topic_id`, `_build_submission_context`, `_apply_submission_outcome`.

## `session.py` public surface

| Function | Responsibility |
|----------|----------------|
| `get_session(session_id)` | In-memory lookup with SQLite fallback |
| `respond(state, curriculum)` | Build API-safe state with navigation attached |
| `begin_problem(state, problem, topics_by_id, *, recent_fingerprints?)` | Reset submission cycle fields, set current problem, persist |
| `start_session(request)` | Create session, load profile, return state with navigation |
| `navigate_session(request)` | Change chapter/topic/level with unlock validation |
| `reset_session(request)` | Hard-reset progress |
| `next_problem(session_id)` | Generate deduped problem and begin it |
| `submit_problem(request)` | Grade answer and update progression |
| `auto_solve_problem(request)` | Admin/dev auto-submit |
| `public_problem(problem, state)` | Strip internal fields for API responses |

Error hierarchy: `SessionError` → `SessionNotFoundError`, `ForbiddenError`, `ConflictError`, `InternalError`.

## Curriculum & problems

- Curriculum YAML: `backend/data/` (one file per chapter, e.g. `Ułamki_Zwykłe.yaml`)
- YAML schema (root keys): `chapter`, `id`, `keyboard_type`, `topics`
- Filename convention: `{chapter with spaces → underscores}.yaml` (must match `chapter`)
- Chapter `id` controls dropdown sequence (lower first) and is the runtime navigation key
- Each `topics[]` entry: `id`, `name`, optional `radio_only`, `levels[]`
- Each level: `level`, `name`, `function`, optional `published`, `traps`
- Problem generators: public functions in `backend/chapters/<slug>/topic_{id}_{slug}.py` (auto-registered; helpers use `_` prefix)
- Curriculum loading: `backend/curriculum_loader.py` (parse, validate, cache)
- Navigation selection fields on state: `selected_chapter_id`, `selected_topic_id`, `selected_level`

## Database

- SQLite at `backend/storage/users.db`
- DB access via `backend/core/db.py`

## Tests

Run from **repo root**:

```bash
python3 -m pytest tests/
```

Tests isolate the DB via pytest fixtures (`tests/test_api_contract.py` uses `tmp_path`).

## API contract

When changing request/response shapes, update `backend/models.py` and mirror in `frontend/lib/types.ts`. Serialized JSON field names are stable — internal type renames must not change wire format.

## Docstrings

Document symbols where behavior is not obvious from the signature alone. Reference: `backend/session_state.py`.

**Add docstrings to:**

- FastAPI route handlers (surfaces in OpenAPI `/docs`)
- Multi-branch business logic (e.g. `evaluate_answer`)
- Public helpers with non-obvious contracts or side effects
- Pydantic models that shape the API contract
- Module docstrings on core entry-point files

**Skip:**

- Private `_helpers` under ~5 lines
- Trivial one-liners (`get_level_options`, `fmt_dec`)
- Topic generators in `topic_*.py` — use Polish pedagogical one-liners there
- Individual `test_*` functions — descriptive names + parametrize tables are enough

**Style:**

- Default: imperative one-liner — `"""Verb + what it does."""`
- Complex functions: add `Args` / `Returns` / `Raises` when helpful (see `generate_problem`)
- Language: English for infrastructure; Polish for problem generators
