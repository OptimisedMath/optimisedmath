# Session client

Rules for `lib/session/` — session types, the client, localStorage, constants, and `useSession()`.

1. **Import from `@/lib/session`.** Do not call session operations or touch session localStorage anywhere else.
2. **`SessionClient` is the app's one test seam.** It expresses the operations performed on a Session — start, submit, next problem, navigate, reset — in domain terms. There are exactly two adapters: `httpSessionClient` (wired in `app/layout.tsx`) and the in-memory adapter in `test/fakeBackend.ts`.
3. **Consumers read the client via `useSessionClient()`**, never by importing an adapter directly.
4. **Do not add a second fake beneath this one** — e.g. mocking `@/lib/api` in an app-level test. The one legitimate place that mocks `@/lib/api` is `test/httpSessionClient.test.ts`, which exists to test the HTTP adapter itself. Tests assert in Sessions/Submissions/Navigation terms, never on a URL or an HTTP call.
5. **The Deconstruction takeover computes no outcomes** ([ADR-0002](../../docs/adr/0002-backend-owns-game-rules.md)). `useDeconstruction()` owns only the local phase machine — `pause -> intro -> step (looping) -> handback` — plus Abandonment. The trigger is `SessionResponse.deconstruction_running`; step correctness is `DeconstructionSubmissionResponse.is_correct`.
6. **Do not infer the trigger from the Submission's wire shape.** `public_problem` also withholds `correct_answer` while a Deconstruction runs, but that is a spoiler rule free to grow other reasons; reading it as the trigger would arm or disarm the takeover from a change nothing links back here.
7. **`GameArena` renders the takeover in place of the whole arena**, not overlaid on it, so the original Problem is genuinely hidden rather than visually covered.
