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
