# Play mode

Rules for Admin mode (`AdminPlayMode`) — QA/debug access for designated Usernames, invisible to normal Students.

1. **Admin mode has no Frontier of its own.** Frontier is a Student-only concept, so Admin mode substitutes effective full unlock (`chapter_max_frontier`) wherever a Frontier would be read or written, without touching the stored Frontier on the profile.
2. **Normal navigation access rules still apply** against that effective full unlock. There is no separate admin navigation bypass anywhere else in the codebase — do not add one.
3. **Implicit navigation defaults land at the start of the target** (first Topic, level 1) rather than at a Frontier position. Explicit Topic/Level picks are unchanged.
4. **`persists_profile = False` is the only thing that stops the write.** Every Submission still runs the normal grade → progression → respond pipeline and telemetry still logs; XP, Flawless, and Frontier are simply never written back. Session streak still runs in-cycle for a realistic feel, and is never persisted.
5. **`session.auto_solve_problem` and `/problem/auto-solve` are dev-tools-only.** The frontend does not call them; its admin auto-solve fills the answer and posts to `/problem/submit` like any Student.
