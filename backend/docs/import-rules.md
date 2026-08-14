# Import rules

1. **Strict layers:** HTTP → session → submission_cycle → submission → state → pure rules. Pure modules never import session, state, or HTTP.
2. **Shared:** any layer may import Pydantic types from `models.py` and play-mode policy from `play_mode.py`.
3. `navigation` **reads only for snapshot/view:** may read `SessionState` from `models.py`; must not mutate state or call session use-cases when building snapshots or views. View payload is derived from data captured on the snapshot at construction time.
4. `session.py` **owns the response view:** `respond()` builds `SessionResponse` from persisted `SessionState` plus play mode and navigation; calls state helpers and `navigation.build_*`; does not embed view-building logic beyond assembling the payload.
5. `Curriculum` **is injected below session:** modules below the session use-case layer receive `Curriculum` as a parameter; only HTTP/session resolve it via `resolve_curriculum()`.