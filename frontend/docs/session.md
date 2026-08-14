# Session client

Arena/login session state lives in `lib/session/` — types, API calls, localStorage, constants, and `useSession()`. Import from `@/lib/session`; do not call session APIs or touch session localStorage elsewhere.

`useSession()` returns `{ view, actions }`; arena children read the slices of `view` they render and call handlers on `actions`.
