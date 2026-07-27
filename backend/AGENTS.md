# Backend conventions

Pure Python FastAPI service — no UI framework imports.

## Entry points

- **API app:** `backend/main.py` (FastAPI routes, session handling)
- **Game engine:** `backend/engine.py`
- **Navigation UI state:** `backend/navigation.py` (unlock rules, dropdown options, progress counts — attached to every `GameState` response via `_respond`)
- **State:** `backend/state_manager.py`, `backend/models.py` (Pydantic)
- **Config:** `backend/config.py` — note `PROJECT_ROOT` resolves to `backend/`, not the monorepo root

## Curriculum & problems

- Curriculum YAML: `backend/data/` (one file per macro topic, e.g. `Ułamki_Zwykłe.yaml`)
- YAML schema (root keys): `macro_topic`, `order`, `keyboard_type`, `micro_topics`
- Filename convention: `{macro_topic with spaces → underscores}.yaml` (must match `macro_topic`)
- Macro `order` controls dropdown sequence (lower first)
- Each `micro_topics[]` entry: `order`, `name`, optional `text_mode_disabled`, `levels[]`
- Each level: `level`, `name`, `function`, optional `published`, `traps`
- Problem generators: `backend/macro_topics/<slug>/micro_*.py` — functions named `frac_*` or `dec_*`
- Curriculum loading: `backend/curriculum_loader.py` (parse, validate, cache); `backend/engine.py` (problem generation)

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

When changing request/response shapes, update `backend/models.py` and mirror in `frontend/lib/types.ts`.

## Docstrings

Document symbols where behavior is not obvious from the signature alone. Reference: `backend/state_manager.py`.

**Add docstrings to:**

- FastAPI route handlers (surfaces in OpenAPI `/docs`)
- Multi-branch business logic (e.g. `evaluate_answer`)
- Public helpers with non-obvious contracts or side effects
- Pydantic models that shape the API contract
- Module docstrings on core entry-point files

**Skip:**

- Private `_helpers` under ~5 lines
- Trivial one-liners (`get_level_options`, `fmt_dec`)
- Macro generators (`frac_*` / `dec_*`) — use Polish pedagogical one-liners there
- Individual `test_*` functions — descriptive names + parametrize tables are enough

**Style:**

- Default: imperative one-liner — `"""Verb + what it does."""`
- Complex functions: add `Args` / `Returns` / `Raises` when helpful (see `generate_problem`)
- Language: English for infrastructure; Polish for problem generators
