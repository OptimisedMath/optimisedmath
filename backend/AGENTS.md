# Backend conventions

Pure Python FastAPI service — no UI framework imports.

## Entry points

- **API app:** `backend/main.py` (FastAPI routes, session handling)
- **Game engine:** `backend/engine.py`
- **Navigation UI state:** `backend/navigation.py` (unlock rules, dropdown options, progress counts — attached to every `GameState` response via `_respond`)
- **State:** `backend/state_manager.py`, `backend/models.py` (Pydantic)
- **Config:** `backend/config.py` — note `PROJECT_ROOT` resolves to `backend/`, not the monorepo root

## Curriculum & problems

- Curriculum YAML: `backend/data/` (e.g. `Ułamki_Zwykłe.yaml`)
- Problem generators: `backend/macro_topics/<topic>/micro_*.py`

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
