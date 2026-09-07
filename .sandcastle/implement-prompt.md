# TASK

Fix issue {{TASK_ID}}: {{ISSUE_TITLE}}

Pull in the issue using `gh issue view <ID>`. If it has a parent PRD, pull that in too.

Only work on the issue specified.

Work on branch {{BRANCH}}. Make commits and run tests.

# RESUMPTION

**This branch may already carry your own unfinished work.** A previous run can
be cut off at any moment — most often because the developer's Claude usage ran
out mid-task — and it leaves everything it had done on this branch. Before you
plan anything, find out what is already there:

1. `git log {{BRANCH}} --not main --format="%H%n%B---"` — every commit already made for this issue. Read the `Blockers or notes for next iteration` line of the most recent one; your past self wrote it for you.
2. `git status` — uncommitted changes left mid-edit. If there are any, read them with `git diff` before touching those files. They are your own work in progress, not someone else's mistake.
3. `gh issue view {{TASK_ID}} --comments` — a previous iteration may have left a note on the issue saying what it finished and what it did not.

Continue from what you find. Do not restart work that is already committed, and
do not revert a half-finished edit just because it is incomplete — finish it.

If everything the issue asks for is already committed on this branch, verify it
with the feedback loops below and output the completion signal immediately
rather than inventing more work.

# CONTEXT

Here are the last 10 commits:

<recent-commits>

!`git log -n 10 --format="%H%n%ad%n%B---" --date=short`

</recent-commits>

# EXPLORATION

Explore the repo and fill your context window with relevant information that will allow you to complete the task.

Pay extra attention to test files that touch the relevant parts of the code.

# EXECUTION

If applicable, use RGR to complete the task.

1. RED: write one test
2. GREEN: write the implementation to pass that test
3. REPEAT until done
4. REFACTOR the code

# FEEDBACK LOOPS

Before committing, run `make test` and `make lint` to ensure the tests and the
linters pass. These are the repo's real entry points — there is no `npm run
test` or `npm run typecheck` at the repo root.

# COMMIT

Make a git commit. The commit message must:

1. Start with `RALPH:` prefix
2. Include task completed + PRD reference
3. Key decisions made
4. Files changed
5. Blockers or notes for next iteration

Keep it concise.

**Commit before you run out of room.** Your work only survives an interruption
if it is committed, so commit each coherent step as you finish it rather than
saving one commit for the end.

# THE ISSUE

If the task is not complete, leave a comment on the issue with what was done.

Do not close the issue - this will be done later.

Once complete, output <promise>COMPLETE</promise>.

# FINAL RULES

ONLY WORK ON A SINGLE TASK.
