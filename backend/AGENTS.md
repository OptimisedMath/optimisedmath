# Backend conventions

Pure Python FastAPI service — no UI framework imports. Game rules live here — [ADR-0002](../docs/adr/0002-backend-owns-game-rules.md).

- **Map** — [backend-map.md](docs/backend-map.md) when locating a module.
- **Layers / imports** — [layered-modules.md](docs/layered-modules.md) and [import-rules.md](docs/import-rules.md) when adding imports or new modules.
- **Submission cycle** — [submission-cycle.md](docs/submission-cycle.md) for begin-problem, Next problem, or Navigation choreography.
- **Submission** — [submission.md](docs/submission.md) for grading one answer through persist.
- **Play mode** — [play-mode.md](docs/play-mode.md) for Admin mode, effective unlock, or profile persistence.
- **Curriculum / generators** — [curriculum.md](docs/curriculum.md) when adding chapters or problem generators.
- **API contract** — [api.md](docs/api.md) when changing request/response shapes.
- **Tests** — DB isolated via pytest fixtures; run from repo root.
- **Docstrings** — [docstrings.md](docs/docstrings.md) when writing or skipping module docs.
