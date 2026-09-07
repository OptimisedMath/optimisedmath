# TASK

Merge the following branches into the current branch (a Sandcastle integration
branch — NOT `main`; do not check out or touch `main`):

{{BRANCHES}}

For each branch:

1. Run `git merge <branch> --no-edit`
2. If there are merge conflicts, resolve them intelligently by reading both sides and choosing the correct resolution
3. After resolving conflicts, run `make test` and `make lint` to verify everything works
   (these are the repo's real entry points — there is no `npm run test` at the root)
4. If tests fail, fix the issues before proceeding to the next branch

After all branches are merged, make a single commit summarizing the merge.

Do not push, do not open a PR, and do not close any issues — that happens once,
automatically, after all iterations finish. These are the issues this batch of
branches covers, for your reference only:

{{ISSUES}}

Once you've merged everything you can, output <promise>COMPLETE</promise>.
