# Backend owns game rules

FastAPI runs grading, streaks, XP, unlock logic, input mode, and progression. Next.js renders session state from API payloads and forwards user input.

**Decision:** All game rules live in the Python backend. The frontend is a dumb visual client — it must not compute streaks, XP, level unlocks, input mode switches, or Flawless eligibility in React/TypeScript.

**Considered options:** Duplicate rule logic in both stacks (rejected — drift and split bugs); compute lightweight rules on the client for responsiveness (rejected — breaks single source of truth for the mastery loop).

**Consequences:** UI that needs a rule outcome must read it from the session payload or add a backend field. Progression changes touch backend modules only. When wire shapes change, update the backend request/response models and the frontend types that mirror them — never reimplement the rule. Current file locations live in `backend/docs/api.md`.
