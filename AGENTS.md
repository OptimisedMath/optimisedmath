# Optimised Math Learning — Monorepo Guide

Single-root monorepo: Python FastAPI backend + Next.js frontend. Open the **repo root** as the workspace.

## Project map

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI API, game engine, session state, curriculum YAML, problem generators |
| `frontend/` | Next.js App Router UI; calls backend via `/api` proxy |
| `tests/` | pytest suite — run from repo root |
| `docs/` | Agent skills config (`docs/agents/`), ADRs (`docs/adr/`); other files under `docs/` stay local-only |

## Run commands

```bash
# Full stack (macOS)
./start.command

# Backend only (from repo root)
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# or: python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Frontend only
cd frontend && npm run dev

# Tests (from repo root)
python3 -m pytest tests/
```

## Python

Use `python3` or `.venv/bin/python`, not bare `python`.

Dependencies: `requirements.txt` at repo root. Virtualenv: `.venv/`.

## API contract

- Frontend requests go to `/api/*` → proxied to `http://127.0.0.1:8000/*` (`frontend/next.config.ts`).
- Backend listens on port **8000**; frontend dev server on port **3000**.
- Keep `frontend/lib/types.ts` aligned with backend curriculum models and `frontend/lib/session/types.ts` aligned with backend session models when changing API shapes.

## Subproject agent docs

- **Next.js / React:** see `frontend/AGENTS.md`
- **FastAPI / Python:** see `backend/AGENTS.md`

## Agent skills

### Issue tracker

GitHub Issues on `OptimisedMath/optimisedmath` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles with matching label strings (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.

## Cursor Cloud specific instructions

- `./start.command` is macOS-only (uses `osascript`/`open`). On the cloud VM, start the two dev servers separately in the background (see "Run commands" above): backend via `.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`, and frontend via `cd frontend && npm run dev` (binds `0.0.0.0`, serves on port 3000).
- Auth is username-only — there is no password. Log in by entering any name on `/login`. Usernames in `backend/config.ADMIN_USERNAMES` (`Antoni`/`Antonio`/`Tony`) get admin mode (all topics unlocked + auto-solve). The UI is in Polish.
- SQLite DB (`backend/storage/users.db`) is created automatically on backend startup; no migration step. It is gitignored and holds all user progress/telemetry.
- The frontend proxies `/api/*` to `http://127.0.0.1:8000` (`frontend/next.config.ts`), so the backend must be running for login/problems to work.
- `black` is unpinned in `requirements.txt`; `black --check` may report many "would reformat" diffs against the currently committed code. That is a formatter-version artifact, not a broken checkout — do not mass-reformat existing files. Python-relevant lint/format is `black`; frontend lint is `npm run lint` (ESLint) and passes clean.
