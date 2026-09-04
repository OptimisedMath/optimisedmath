# Backend conventions

Pure Python FastAPI service — no UI framework imports. Game rules live here — [ADR-0002](../docs/adr/0002-backend-owns-game-rules.md).

- **Map** — [backend-map.md](docs/backend-map.md) when locating a module.
- **Layers / imports** — [layered-modules.md](docs/layered-modules.md) and [import-rules.md](docs/import-rules.md) when adding imports or new modules.
- **Submission cycle** — [submission-cycle.md](docs/submission-cycle.md) for begin-problem, Next problem, or Navigation choreography.
- **Submission** — [submission.md](docs/submission.md) for grading one answer through persist.
- **Play mode** — [play-mode.md](docs/play-mode.md) for Admin mode, effective unlock, or profile persistence.
- **Curriculum / generators** — [backend-map.md](docs/backend-map.md) when adding chapters or problem generators.
- **API contract** — request/response shapes are `models.py` (Pydantic) mirrored by `frontend/lib/session/types.ts` and `frontend/lib/types.ts`; JSON field names are stable wire format — see `CONTEXT.md`.
- **Tests** — DB isolated via pytest fixtures; run from repo root.
- **Documentation** — [documentation.md](../docs/agents/documentation.md) when writing or skipping a docstring or comment.
