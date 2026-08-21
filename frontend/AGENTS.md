# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

# Frontend conventions

Next.js App Router UI. Rule outcomes stay on the backend — [ADR-0002](../docs/adr/0002-backend-owns-game-rules.md).

- **Map** — [frontend/docs/frontend-map.md](docs/frontend-map.md) when locating pages, components, or `lib/` modules.
- **API contract/calls** — request/response shapes are `backend/models.py` (Pydantic, e.g. `SessionResponse`) mirrored by `lib/session/types.ts` (e.g. `SessionResponse`) and `lib/types.ts`; relative `/api/*` paths, Next.js rewrites to FastAPI on `:8000`.
- **Session client** — [session.md](docs/session.md) when touching arena/login state, session APIs, or session localStorage.
- **Tests** — `npm test` (Vitest + Testing Library). The session client (`lib/session/client.ts`) is the test seam: tests inject the in-memory adapter from `test/fakeBackend.ts` via `SessionClientProvider`, and speak in Sessions/Submissions/Navigation, never routes. Do not add a second fake beneath it.

