# TASK

Merge the following branches into the current branch (a Sandcastle integration
branch — NOT `main`; do not check out or touch `main`):

{{BRANCHES}}

For each branch:

1. Run `git merge <branch> --no-ff --no-edit`
2. If there are merge conflicts, resolve them intelligently by reading both sides and choosing the correct resolution
3. After resolving conflicts, run `make test` and `make lint` to verify everything works
   (these are the repo's real entry points — there is no `npm run test` at the root)
4. If tests fail, fix the issues before proceeding to the next branch

Leave the merge commits exactly as `git merge` wrote them. Do NOT tidy the
history afterwards — no `git reset`, no `git rebase`, no squash, no amending a
merge commit away, and no single commit summarizing the whole merge. Sandcastle
decides what has already been merged, what is still stranded, and which issues a
PR closes by asking git whether each issue branch is an ancestor of this branch
(`git branch --merged`). Squashing keeps the code but destroys that ancestry, so
the next run re-plans work that is already here, the PR omits `Closes #...` for
every issue you squashed, and the run ends with a false "branches carry commits
that are NOT in this PR" warning.

Extra commits of your own — conflict fixes, a test repair — are fine on top of
the merges.

Do not push, do not open a PR, and do not close any issues — that happens once,
automatically, after all iterations finish. These are the issues this batch of
branches covers, for your reference only:

{{ISSUES}}

Once you've merged everything you can, output <promise>COMPLETE</promise>.
