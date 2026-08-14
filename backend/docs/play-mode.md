# Play mode

Admin mode (`AdminPlayMode`) is QA/debug access for designated Usernames,
invisible to normal Students. It has no Frontier of its own — Frontier is a
Student-only concept — so it substitutes **effective full unlock**
(`chapter_max_frontier`) everywhere a Frontier would otherwise be read or
written, without touching the stored Frontier on the profile. Normal
navigation access rules still apply against that effective full unlock;
there is no separate admin navigation bypass elsewhere in the codebase.
Implicit navigation defaults (chapter-only or topic-only changes) land at
the start of the target (first Topic, level 1) rather than at a Frontier
position; explicit Topic/Level picks are unchanged.

Every Submission still runs the normal grade → progression → respond
pipeline (see `session.py`) and telemetry still logs, but
`persists_profile = False` means XP, Flawless, and Frontier updates are
never written back to the profile, and progress bars render fully
complete. Session streak still runs in-cycle (radio → input mode, wrong
answers decrement) for a realistic feel, but is never persisted — navigation
still resets it. Admin auto-solve in the UI is a visible shortcut through
that same Submission pipeline: the client selects or types the correct
answer, then calls `/problem/submit`. `session.auto_solve_problem` and
`/problem/auto-solve` are dev-tools-only shortcuts that skip the UI fill
step; the frontend does not call them.
