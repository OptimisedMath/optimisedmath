# Pure rule modules take values, not the Session

`backend/docs/import-rules.md` rule 1 bans pure modules from importing "state", and rule 2 lets any layer import Pydantic types from `models.py`. `SessionState` is one of those types, so the two rules together allowed either reading, and the code followed both: `unlock` took a `ChapterFrontier`, `progression` took a `SessionState` for its Streak meter rule (#304). We decided "state" means the `SessionState` type: a pure rule module may take small value types such as `ChapterFrontier`, and never the whole Session.

**Considered options:** "state" means only the `session_state.py` module (rejected — then a pure module could take the whole Session, and "pure" would say nothing about how wide its inputs are); no Pydantic session model below the state layer at all (rejected — `unlock.get_frontier` and `PlayMode.resolve_frontier` would change signature for no gain over this reading).

**Consequences:** Rule 1 names the type. `progression` gives up its `SessionState` import, so the Streak meter rule leaves it. The layer that owns the Session builds each rule's inputs, which is why `SubmissionContext` is a "Session slice" and not the Session itself.
