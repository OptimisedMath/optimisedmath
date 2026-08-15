# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

# Frontend conventions

Next.js App Router UI. Rule outcomes stay on the backend — [ADR-0002](../docs/adr/0002-backend-owns-game-rules.md).

- **Map** — [frontend/docs/frontend-map.md](docs/frontend-map.md) when locating pages, components, or `lib/` modules.
- **API contract/calls** — [backend/docs/api.md](../backend/docs/api.md) when changing request/response shapes or working with API calls.
- **Session client** — [session.md](docs/session.md) when touching arena/login state, session APIs, or session localStorage.
- **Tests** — `npm test` (Vitest + Testing Library). Fake backend via `test/apiMock.ts` at the HTTP adapter seam.

