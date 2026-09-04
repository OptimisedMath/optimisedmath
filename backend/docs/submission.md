# Submission module

Rules for `submission.py`, which owns one Submission end-to-end.

1. **Call it from `session.py`.** No pass-through wrappers in `session.py` or `session_state.py`.
2. **Internal helpers stay private.** Testable, but never re-exported.
3. **The Deconstruction trigger arms, it never short-circuits.** The triggering answer is graded, logged, and progressed as a completely normal Submission.
4. **The trigger and the Deconstruction's own ending must agree on one identity.** The trigger check shares its `(Misconception, Level)` key format with `deconstruction_step.deconstruction_key()`; changing one changes both.
5. **A discounted retry branches around the trigger check and normal progression**, scoring XP at the config multiplier and leaving Streak, Flawless, and the Frontier untouched ([ADR-0004](../../docs/adr/0004-deconstruction-outside-submission-cycle.md)). `state.discounted_problem_id` clears once the retry locks — a soft error keeps it open, mirroring how a soft error never locks any other Problem.
6. **Failures propagate with their original exception and context.** Do not wrap in generic internal errors, and do not print-and-re-raise.
