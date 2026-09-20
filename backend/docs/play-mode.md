# Play mode

Rules for Admin mode (`AdminPlayMode`) — QA/debug access for designated Usernames, invisible to normal Students.

1. **Admin mode has no Frontier of its own.** Frontier is a Student-only concept, so Admin mode substitutes effective full unlock (`chapter_max_frontier`) wherever a Frontier would be read or written, without touching the stored Frontier on the profile.
2. **Normal navigation access rules still apply** against that effective full unlock. There is no separate admin navigation bypass anywhere else in the codebase — do not add one.
3. **Implicit navigation defaults land at the start of the target** (first Topic, level 1) rather than at a Frontier position. Explicit Topic/Level picks are unchanged.
4. **`persists_profile = False` is the only thing that stops the profile write.** Every Submission still runs the normal grade → progression → respond pipeline and telemetry still logs, labelled `play_mode = 'admin'` rather than discarded; the write-back restores XP and the Chapter Frontiers from the stored profile, so neither the in-cycle XP nor the moved Frontier ever reaches it. Streak and Flawless have no profile column at all ([ADR-0006](../../docs/adr/0006-profile-owns-selected-not-streak-or-flawless.md)) and are written from the Session into the stored Session in both play modes, exactly like a Student's — the in-cycle Streak runs for a realistic feel and there is nothing to restore it from.
5. **`session.auto_solve_problem` and `/problem/auto-solve` are dev-tools-only.** The frontend does not call them; its admin auto-solve fills the answer and posts to `/problem/submit` like any Student.
