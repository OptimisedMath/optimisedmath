# Import rules

1. **Strict layers:** HTTP → session → submission_cycle → submission → state → pure rules. Pure modules never import session, state, or HTTP.
2. **Shared:** any layer may import Pydantic types from `models.py` and play-mode policy from `play_mode.py`.
3. **`navigation_snapshot` reads only.** It may read `SessionState` from `models.py`, and must not mutate state or call session use-cases. Its lifecycle — one value per `(state, mutation-epoch)`, so a mutation obliges a rebuild — is [ADR-0003](../../docs/adr/0003-shared-helpers-move-down-not-across.md).
4. **`navigation_resolve` does not mutate either.** It resolves an intent against a `NavigationSnapshot`, reading it one-directionally, and never calls session use-cases.
5. **`session.py` owns the response view.** `build_session_response()` assembles `SessionResponse`; it does not embed view-building logic beyond assembling the payload.
6. **`Curriculum` is injected below session.** Modules below the session use-case layer receive it as a parameter; only HTTP/session resolve it via `resolve_curriculum()`.
