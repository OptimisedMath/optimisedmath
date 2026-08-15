# Backend owns game rules

FastAPI owns authoritative game state and rule outcomes: grading, streak, XP, Flawless, input mode, and what is Locked vs Reachable. Next.js owns presentation, interaction, and mapping those payload fields into UI — not a second rules engine, and not a dumb visual client.

**Decision:** Re-deriving a rule outcome in React/TypeScript is a leak. Drawing or combining fields the server already computed is not.

**Considered options:** Duplicate the mastery loop in both stacks (rejected — drift); compute lightweight rules on the client for snappier UI (rejected — splits the source of truth); treat the frontend as a dumb layer that must not derive any view at all (rejected on revisit — interaction and payload→UI mapping belong in the session client; forcing display exceptions onto `respond()` bloats the wire contract).

**Consequences:** UI that needs a new *outcome* (streak, unlock, input mode, Flawless, correctness) reads it from the session payload or adds a backend field. Progression changes touch backend modules only. A formula that would have to exist in Python *and* TypeScript is the leak test; mapping `feedback_type` + `can_next_problem` into a feedback phase, or `streak_meter` into stars, is not. When wire shapes change, update the Pydantic models and the frontend types that mirror them — never reimplement the rule. Current file locations live in `backend/docs/api.md`.
