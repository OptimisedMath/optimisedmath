# Session client

Arena/login session state lives in `lib/session/` — types, the session client, localStorage, constants, and `useSession()`. Import from `@/lib/session`; do not call session operations or touch session localStorage elsewhere.

`useSession()` returns `{ view, actions }`; arena children read the slices of `view` they render and call handlers on `actions`.

## The session client seam

`SessionClient` (`lib/session/client.ts`) is the interface for the operations the app performs on a Session — start, submit, next problem, navigate, reset — expressed in domain terms with the existing payload types. There are exactly two adapters:

- `httpSessionClient` (`lib/session/httpSessionClient.ts`) — talks to the FastAPI backend. Wired in production via `SessionClientProvider` in `app/layout.tsx`.
- The in-memory adapter in `frontend/test/fakeBackend.ts` — used by every frontend test.

Consumers (`useSessionBootstrap`, `useProblemLifecycle`, `useDeconstruction`, `LoginForm`) read the client via `useSessionClient()` rather than importing an adapter directly.

This is the frontend's one test seam. Tests supply the in-memory adapter through `SessionClientProvider` and assert in Sessions/Submissions/Navigation terms — never on a URL or HTTP call. Do not add a second fake beneath this one (e.g. mocking `@/lib/api` in an app-level test); the only legitimate place that mocks `@/lib/api` is `test/httpSessionClient.test.ts`, which exists to test the HTTP adapter itself.

## The Deconstruction takeover

`useDeconstruction()` (composed by `useSession()`) owns the takeover's local phase machine — `pause -> intro -> step (looping) -> handback` — plus Abandonment via the exit control. Per ADR-0002, it computes none of the takeover's outcomes itself: the pause-to-takeover trigger is derived purely from a triggering Submission's wire shape (a locked, wrong answer whose Problem is missing `correct_answer`, withheld server-side only while a Deconstruction is running — see `backend/session.py`'s `public_problem`), and step correctness comes only from `DeconstructionSubmissionResponse.is_correct`. `components/arena/Deconstruction*.tsx` render `SessionView.deconstruction`; `GameArena` renders the takeover in place of the whole arena (not overlaid on it) so the original Problem is genuinely hidden, not just visually covered.
