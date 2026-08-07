<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Frontend conventions

- **App Router:** pages live under `app/` (`/`, `/login`, `/arena`).
- **API calls:** use relative `/api/*` paths — Next.js rewrites to the FastAPI backend on `:8000`.
- **Components:** arena UI in `components/arena/`, shared UI in `components/ui/` (shadcn).
- **Session:** arena/login session state lives in `lib/session/` — types, API calls, localStorage, constants, and `useSession()`. Import from `@/lib/session`; do not call session APIs or touch session localStorage elsewhere.
- **Curriculum types:** static catalog types in `lib/types.ts` (mirror backend curriculum models).
- **Dev server:** `npm run dev` (binds `0.0.0.0` for LAN access).
