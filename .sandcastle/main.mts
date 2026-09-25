// Parallel Planner with Review — grouped, resumable orchestration loop
//
// A run works one **group** at a time, in sequence. A group is the set of open
// issues sharing a `sandcastle:<id>` label; an issue carrying the bare
// `sandcastle` label is a group of one. Each group gets its own integration
// branch and its own PR, so two unrelated specs never share a review.
//
// Per group:
//   Phase 0 (Pick up):          Merge `sandcastle/issue-<N>` branches belonging
//                               to THIS group that a prior run left finished.
//   Phase 1 (Plan):             Each remaining issue is checked against
//                               GitHub's own record of what blocks it — native
//                               issue dependencies, or a `Blocked by:` line in
//                               the body as a fallback. A blocker whose work is
//                               already on the integration branch counts as
//                               resolved, so a group that blocks itself drains
//                               over successive cycles rather than waiting for
//                               its own PR to merge. Anything still blocked is
//                               skipped, not attempted; there is no inferred
//                               dependency graph and no fallback candidate
//                               forced through when everything is blocked.
//   Phase 2 (Execute + Review): Per issue, a sandbox is created. The implementer
//                               is driven one iteration at a time so a dead run
//                               can be cut short; the reviewer follows if it
//                               committed. Issues run concurrently.
//   Phase 3 (Merge):            One agent merges the completed branches.
//   Phase 4 (PR):               Push and open (or refresh) a DRAFT PR. It is
//                               marked ready for review only once the group has
//                               nothing planned, nothing blocked, and nothing
//                               stranded.
//
// A run is built to be killed. Quota exhaustion mid-run is the expected case,
// not an exception: whatever merged is pushed as a draft PR, and the next run
// resumes the same integration branch and grows the same PR.
//
// Usage:
//   npm run sandcastle              # every group, in order
//   npm run sandcastle -- 244       # one group only
//   npm run sandcastle -- solo-365  # one solo issue only
//   SANDCASTLE_DRY_RUN=1 npm run sandcastle
//   node --test .sandcastle/lib/    # unit tests for the logic below
//
// The argument is always a group id, so what you can run by hand is decided by
// the admission label. An issue carrying the bare `sandcastle` label is the
// group `solo-<its number>`, which is how you name it above. An issue inside a
// `sandcastle:<id>` group has no handle of its own: the whole group is the
// smallest thing a run will take, and the siblings you did not want cost a
// sandbox each to report they have nothing to do.

import * as sandcastle from "@ai-hero/sandcastle";
import { defaultImageName, docker } from "@ai-hero/sandcastle/sandboxes/docker";
import { execFileSync, execSync } from "node:child_process";
import { existsSync } from "node:fs";

import {
  doneIssues,
  isBatchBranchShipped,
  isStale,
  markDone,
  readyToMerge,
  saveWorktree,
  unfinishedBranches,
  type IssueBranch,
} from "./lib/gitFacts.mts";
import { reportOutcome } from "./notify.mts";
import {
  batchBranchGlob,
  batchBranchName,
  buildPrBody,
  buildPrTitle,
  classifyFailure,
  DEAD_ITERATION_THRESHOLD,
  describeGroup,
  isDeadRun,
  isGroupComplete,
  isRunFatal,
  type FailureKind,
  isSettledWithNothingToDo,
  issueBranchName,
  issueNumberOfBranch,
  liveBlockers,
  parseBlockedByLine,
  partitionIntoGroups,
  type Group,
  type Issue,
} from "./lib/groups.mts";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Plan→execute→merge cycles per group. The loop exists to pick up issues that
// a merge unblocks, so it needs to cover the depth of a dependency chain, not
// the size of the backlog — plus slack, because a cycle that produces no
// commits still spends one. The deepest chain on the board when this was last
// checked was four (#272,#273 → #277 → #278 → #279 under `sandcastle:262`), so
// four exactly would drain that group only if nothing went wrong on the way.
// Still deliberately small: with a finite quota, the constant that matters is
// the one that stops a wedged group eating the night. Cycles are not spent
// speculatively — the loop breaks as soon as nothing is plannable.
const MAX_ITERATIONS = 6;

// Upper bound on implementer iterations per issue. Driven one at a time from
// here rather than handed to maxIterations, so the circuit breaker below can
// stop a dead run instead of burning the remainder on container starts.
const MAX_IMPLEMENTER_ITERATIONS = 100;

// Hooks run inside the sandbox before the agent starts. The agent's feedback
// loop is `make test` / `make lint`, so all three toolchains it reaches for —
// root node, frontend node, and the Python env uv manages — must be present, or
// the loop fails in a way the agent will read as a broken repo.
// Every sandbox installs from cold, and the 60s default is a budget for a
// top-up rather than an install. A hook that times out throws the whole group
// away *after* the agents have done their expensive work. Slow is recoverable;
// dead is not — and this one budget now covers the whole chain below, which
// runs in sequence rather than three installs racing each other.
const HOOK_TIMEOUT_MS = 20 * 60 * 1000;

const hooks = {
  sandbox: {
    onSandboxReady: [
      // One command, not four. Sandcastle runs the entries of this list
      // concurrently, so a reset listed after the installs does not follow them:
      // it finished first, npm rewrote frontend/package-lock.json behind it, and
      // every sandbox handed its agent a worktree that was already dirty.
      //
      // That dirt is indistinguishable from an interrupted agent, so Phase 0
      // refuses to pick the branch up — permanently, since every run redoes the
      // same install. Finished commits then never reach a PR, and `gh pr merge`
      // cannot clean up the worktree afterwards. Setup must leave no trace;
      // this all runs before the agent starts, so a lockfile change the agent
      // genuinely intends is unaffected.
      {
        command: [
          "npm install",
          "npm install --prefix frontend",
          "uv sync",
          "git checkout -- package-lock.json frontend/package-lock.json",
        ].join(" && "),
        timeoutMs: HOOK_TIMEOUT_MS,
      },
    ],
  },
};

// Nothing is copied from the host. node_modules was, to make the hooks above a
// top-up rather than a cold install, but the host is Darwin arm64 and the
// sandbox is Linux aarch64: the tree carries platform-specific binaries like
// @rollup/rollup-darwin-arm64 that are wrong inside the container. npm has to
// reconcile them, and that reconciliation rewrote the lockfiles on a good day
// and died with ENOTEMPTY on a bad one. A cold install is slower and correct.
// If the minutes ever matter, the fix is a cache the container owns — a volume
// or an image layer — not a copy of a tree built for another platform.

const BASE_BRANCH = "main";

// Every git comparison against the base uses the remote's copy, fetched per
// group. The run never checks anything out on the host, so it cannot `git pull`
// the local branch, and a stale local main would make shipped work look new.
const BASE_REF = `origin/${BASE_BRANCH}`;

const DRY_RUN = process.env.SANDCASTLE_DRY_RUN === "1";

const REQUESTED_GROUP = process.argv[2];

// ---------------------------------------------------------------------------
// Shell helpers
// ---------------------------------------------------------------------------

/** Run a command and return its trimmed stdout. */
function sh(command: string): string {
  return execSync(command, { encoding: "utf-8" }).trim();
}

/** Run a command, returning its stdout or undefined if it failed. */
function shQuiet(command: string): string | undefined {
  try {
    return execSync(command, {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "ignore"],
    }).trim();
  } catch {
    return undefined;
  }
}

/** Split git's newline-delimited branch output into names. */
function lines(output: string): string[] {
  return output
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

/**
 * Reject a group id that could not safely reach a shell or a branch name.
 *
 * Group ids come from label names, which a human writes; they are interpolated
 * into `gh` queries and git refs, so anything outside this set is refused
 * rather than escaped.
 */
function assertSafeGroupId(id: string): void {
  if (!/^[A-Za-z0-9._-]+$/.test(id)) {
    throw new Error(
      `Unsafe Sandcastle group id ${JSON.stringify(id)}. Group ids may contain letters, digits, dot, dash and underscore only.`,
    );
  }
}

// ---------------------------------------------------------------------------
// Reading the board
// ---------------------------------------------------------------------------

/** Fetch every open issue with its labels and body, in one call. */
function fetchOpenIssues(): Issue[] {
  const json = sh(
    `gh issue list --state open --limit 200 --json number,title,body,labels`,
  );
  const raw = JSON.parse(json) as {
    number: number;
    title: string;
    body: string;
    labels: { name: string }[];
  }[];
  return raw.map((issue) => ({
    number: issue.number,
    title: issue.title,
    body: issue.body,
    labels: issue.labels.map((label) => label.name),
  }));
}

// ---------------------------------------------------------------------------
// Blocking
// ---------------------------------------------------------------------------

/**
 * Open issue numbers currently blocking this issue — the deterministic
 * replacement for a planner inferring dependencies from issue text.
 *
 * Native GitHub issue dependencies (docs/agents/issue-tracker.md:42) are the
 * primary signal, checked against every open issue in the repo, not just
 * Sandcastle-labelled ones: a dependency is real regardless of whether its
 * blocker happens to carry a Sandcastle label. A `Blocked by: #<n>` line at
 * the top of the body is the documented fallback, used only when the native
 * check finds nothing — and only for blockers that are themselves still open,
 * since a stale `Blocked by:` line naming a closed issue is not a live block.
 *
 * GET on `dependencies/blocked_by` (the docs only show POST, for adding an
 * edge) returns a JSON array of the blocking issues, each with a `state` and
 * `number` — confirmed against a real edge: `gh api
 * repos/{owner}/{repo}/issues/<n>/dependencies/blocked_by --paginate --jq
 * '[.[] | select(.state=="open") | .number]'` returned `[345]` for an issue
 * with a single open native blocker, #345.
 */
function fetchBlockers(issue: Issue): number[] {
  const native = shQuiet(
    `gh api repos/{owner}/{repo}/issues/${issue.number}/dependencies/blocked_by --paginate --jq '[.[] | select(.state=="open") | .number]'`,
  );
  if (native !== undefined) {
    const numbers = JSON.parse(native.length > 0 ? native : "[]") as number[];
    if (numbers.length > 0) return numbers;
  }

  return parseBlockedByLine(issue.body).filter(isIssueOpen);
}

/** Whether an issue is still open, for validating a `Blocked by:` fallback line. */
function isIssueOpen(issueNumber: number): boolean {
  return shQuiet(`gh issue view ${issueNumber} --json state --jq .state`) === "OPEN";
}

// ---------------------------------------------------------------------------
// Branch bookkeeping, scoped to one group
// ---------------------------------------------------------------------------

/** List local branches matching a glob. */
function branchesMatching(glob: string): string[] {
  return lines(
    sh(`git branch --list "${glob}" --sort=-committerdate --format="%(refname:short)"`),
  );
}

/** Count commits on `branch` that `ref` does not already contain. */
function commitsAhead(ref: string, branch: string): number {
  return Number(sh(`git rev-list --count ${ref}..${branch}`));
}

/** The group's issues, described as {issueNumber, branch} pairs for gitFacts. */
function groupIssueBranchDescriptors(group: Group): IssueBranch[] {
  return group.issues.map((issue) => ({
    issueNumber: issue.number,
    branch: issueBranchName(issue.number),
  }));
}

/**
 * Merged PR head branches matching `glob`, for deciding whether a batch
 * branch shipped by squash merge rather than by ancestry. `gh` has no glob
 * search over head branch names, so every merged PR is fetched once and
 * filtered here.
 */
function fetchMergedPrHeadBranches(glob: string): string[] {
  const json = shQuiet(
    `gh pr list --state merged --limit 200 --json headRefName --jq '[.[].headRefName]'`,
  );
  if (json === undefined) return [];
  const pattern = new RegExp(
    `^${glob.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*")}$`,
  );
  return (JSON.parse(json) as string[]).filter((branch) => pattern.test(branch));
}

/**
 * Resolve the integration branch for a group, resuming one if it exists.
 *
 * A run is resumable: a `sandcastle/batch-<id>-*` branch left by an earlier run
 * is continued so its work — and its PR — carry forward. A fresh branch is cut
 * from BASE_BRANCH only when this group has none outstanding. A branch counts
 * as shipped — and is never resumed — once BASE_REF has it as an ancestor, or
 * once a PR with that head branch has merged. The second case is what a squash
 * merge needs: it never makes the branch an ancestor of BASE_REF.
 */
function resolveIntegrationBranch(group: Group): string {
  execSync(`git fetch origin ${BASE_BRANCH}`, { stdio: "inherit" });
  const glob = batchBranchGlob(group.id);
  const mergedPrHeads = fetchMergedPrHeadBranches(glob);
  const outstanding = branchesMatching(glob).find(
    (branch) => !isBatchBranchShipped(process.cwd(), branch, BASE_REF, mergedPrHeads),
  );

  // Neither branch is checked out on the host. Agents work on it in their own
  // worktree — see onIntegrationBranch — and git refuses a worktree for a
  // branch that is already checked out somewhere else.
  if (outstanding) {
    console.log(`\nResuming integration branch: ${outstanding}`);
    return outstanding;
  }

  const fresh = batchBranchName(group.id, Date.now());
  sh(`git branch ${fresh} ${BASE_REF}`);
  console.log(`\nCut integration branch: ${fresh}`);
  return fresh;
}

/**
 * Which of the group's issues does the integration branch already cover?
 *
 * Driven by Done markers reachable from the integration branch, not by
 * ancestry or commit counts: an issue is merged once the orchestrator marked
 * it done, whether or not its branch produced a diff.
 */
function resolveMergedIssues(
  group: Group,
  integrationBranch: string,
): { id: string; title: string; branch: string }[] {
  const titles = new Map(group.issues.map((i) => [i.number, i.title]));

  return doneIssues(process.cwd(), integrationBranch)
    .filter((number) => titles.has(number))
    .map((number) => ({
      id: String(number),
      title: titles.get(number) ?? `Issue #${number}`,
      branch: issueBranchName(number),
    }))
    .sort((a, b) => Number(a.id) - Number(b.id));
}

/** Host path of the worktree Sandcastle keeps for a branch. */
function worktreePathOf(branch: string): string {
  return `.sandcastle/worktrees/${branch.replace(/\//g, "-")}`;
}

/** Whether a branch's worktree has uncommitted changes mid-edit. */
function worktreeIsDirty(branch: string): boolean {
  const status = shQuiet(`git -C ${worktreePathOf(branch)} status --porcelain`);
  // No worktree checked out for this branch means nothing is mid-edit.
  return status !== undefined && status.length > 0;
}

/**
 * Commit whatever a killed process left mid-edit in the group's issue
 * worktrees, before Phase 0 even looks at them. Nothing else runs between a
 * Ctrl-C and the next invocation of Sandcastle, so this is the only point
 * that ever sees that dirt.
 */
function saveDirtyWorktreesAtGroupStart(group: Group): void {
  for (const issue of group.issues) {
    const branch = issueBranchName(issue.number);
    const worktree = worktreePathOf(branch);
    if (!existsSync(worktree)) continue;
    if (!worktreeIsDirty(branch)) continue;

    if (saveWorktree(worktree, issue.number, "found-dirty-at-start")) {
      console.log(
        `Saved #${issue.number}: ${branch} was left dirty by an interrupted run.`,
      );
    }
  }
}

/**
 * Recreate an issue branch left pointing at content already on BASE_REF —
 * e.g. commits later squash-merged (#253, #258, #355, #356). Safe because a
 * stale branch holds nothing BASE_REF lacks. A dirty worktree is left alone:
 * `saveDirtyWorktreesAtGroupStart` already gave it content of its own by the
 * time this runs, so it is no longer stale.
 */
function recreateStaleBranches(
  planned: { id: string; branch: string }[],
  integrationBranch: string,
): void {
  for (const { id, branch } of planned) {
    if (branchesMatching(branch).length === 0) continue;
    if (worktreeIsDirty(branch)) continue;
    if (!isStale(process.cwd(), branch, BASE_REF)) continue;

    sh(`git branch -f ${branch} ${integrationBranch}`);
    console.log(
      `#${id}: ${branch} was stale (its commits already reached ${BASE_BRANCH}, likely via a squash merge) — recreated from ${integrationBranch}.`,
    );
  }
}

/**
 * Report the group's work that is saved but not yet marked done.
 *
 * A branch lands here either because an implementer is still mid-issue, or
 * because it was interrupted before signalling completion — the save points
 * in gitFacts mean neither case loses work, so there is nothing to do by
 * hand. This just makes the omission loud at PR time.
 */
function warnAboutUnfinishedBranches(
  group: Group,
  integrationBranch: string,
): void {
  const unfinished = unfinishedBranches(
    process.cwd(),
    integrationBranch,
    groupIssueBranchDescriptors(group),
  );
  if (unfinished.length === 0) return;

  console.warn(
    `\n⚠️  ${describeGroup(group.id)}: ${unfinished.length} branch(es) hold saved work with no Done marker yet:\n`,
  );

  for (const branch of unfinished) {
    const ahead = commitsAhead(integrationBranch, branch);
    const dirty = worktreeIsDirty(branch);
    console.warn(
      `  ${branch} — ${ahead} commit(s), ${dirty ? "currently mid-edit" : "idle, waiting for its implementer or reviewer to finish"}`,
    );
  }
  console.warn(`\n  Nothing to do by hand — re-run Sandcastle and it will be continued.\n`);
}

// ---------------------------------------------------------------------------
// Failures
// ---------------------------------------------------------------------------

/** A failure that should end the whole run rather than just its group. */
const FATAL_REASONS: Record<Exclude<FailureKind, "local">, string> = {
  quota: "Claude usage exhausted",
  auth: "Agent authentication failed",
  network: "Cannot reach the API from inside the sandbox",
};

class RunFatalError extends Error {
  constructor(
    readonly kind: Exclude<FailureKind, "local">,
    detail: string,
  ) {
    super(`${FATAL_REASONS[kind]} — stopping the run. (${detail})`);
  }
}

/** Turn an unknown thrown value into text the failure classifier can read. */
function errorText(error: unknown): string {
  return error instanceof Error ? `${error.message}\n${error.stack ?? ""}` : String(error);
}

/** Rethrow as fatal when the text names a failure that would kill every group. */
function throwIfRunFatal(text: string): void {
  const kind = classifyFailure(text);
  if (isRunFatal(kind)) {
    throw new RunFatalError(kind, text.slice(0, 200));
  }
}

/**
 * Where an agent that works on the integration branch gets its checkout.
 *
 * Without this, a bind-mount sandbox defaults to the "head" strategy: it mounts
 * the developer's own checkout. Every setup hook then ran against it, which
 * replaced the Mac's frontend/node_modules with Linux binaries, rewrote the
 * lockfile, and let the merger `git stash` the developer's working tree. A
 * named branch gets a worktree under .sandcastle/worktrees/ instead, exactly as
 * an issue sandbox always has.
 */
function onIntegrationBranch(branch: string) {
  return { type: "branch", branch } as const;
}

// ---------------------------------------------------------------------------
// Phase 0: pick up finished work from a prior run
// ---------------------------------------------------------------------------

/**
 * Merge this group's branches that a prior run finished but never merged —
 * "finished" meaning carrying a Done marker for this integration branch, not
 * merely carrying commits. A branch with agent commits but no marker is left
 * alone: it is unfinished, not ready, however far it got.
 */
async function pickUpPriorWork(
  group: Group,
  integrationBranch: string,
): Promise<void> {
  const ready = new Set(
    readyToMerge(process.cwd(), integrationBranch, groupIssueBranchDescriptors(group)),
  );
  const pickedUp = group.issues
    .map((issue) => ({ issue, branch: issueBranchName(issue.number) }))
    .filter(({ branch }) => ready.has(branch));

  if (pickedUp.length === 0) return;

  console.log(`\nPicking up ${pickedUp.length} branch(es) from a prior run:`);
  for (const { issue, branch } of pickedUp) {
    console.log(`  ${issue.number}: ${issue.title} → ${branch}`);
  }

  await sandcastle.run({
    hooks,
    sandbox: docker(),
    branchStrategy: onIntegrationBranch(integrationBranch),
    name: "merger",
    maxIterations: 1,
    agent: sandcastle.claudeCode("claude-sonnet-5"),
    promptFile: "./.sandcastle/merge-prompt.md",
    promptArgs: {
      BRANCHES: pickedUp.map(({ branch }) => `- ${branch}`).join("\n"),
      ISSUES: pickedUp
        .map(({ issue }) => `- ${issue.number}: ${issue.title}`)
        .join("\n"),
    },
  });

  console.log("\nPrior-run branches merged into integration branch.");
}

// ---------------------------------------------------------------------------
// Phase 1: plan
// ---------------------------------------------------------------------------

/**
 * Split the group's remaining issues into what can run now and what is
 * blocked, by checking each one deterministically rather than inferring a
 * dependency graph. Applies the same way to a solo group's single issue as to
 * a multi-issue group — a blocked solo issue simply comes back with nothing
 * planned and itself in `blocked`.
 *
 * `alreadyMerged` does double duty: it drops the issues this batch has already
 * done, and it satisfies blockers pointing at them, so a group whose own
 * members block each other drains over successive cycles instead of stalling on
 * issues GitHub will only close when the batch PR merges.
 */
function planGroup(
  group: Group,
  alreadyMerged: number[],
): {
  planned: { id: string; title: string; branch: string }[];
  blocked: { id: string; title: string; blockedBy: number[] }[];
} {
  const remaining = group.issues.filter(
    (issue) => !alreadyMerged.includes(issue.number),
  );

  const planned: { id: string; title: string; branch: string }[] = [];
  const blocked: { id: string; title: string; blockedBy: number[] }[] = [];

  for (const issue of remaining) {
    const blockedBy = liveBlockers(fetchBlockers(issue), alreadyMerged);
    if (blockedBy.length > 0) {
      blocked.push({ id: String(issue.number), title: issue.title, blockedBy });
    } else {
      planned.push({
        id: String(issue.number),
        title: issue.title,
        branch: issueBranchName(issue.number),
      });
    }
  }

  return { planned, blocked };
}

// ---------------------------------------------------------------------------
// Phase 2: execute + review
// ---------------------------------------------------------------------------

/**
 * What iterations 2+ send when the implementer's session survived the last one.
 *
 * A resumed session still holds the prompt it was given, the repo it explored
 * and the work it committed, so re-sending the prompt file would pay to rebuild
 * context the agent already has. The two rules restated here are the ones the
 * orchestrator itself depends on — commits are how it sees progress, the signal
 * is how it sees the end — and they are cheap enough to repeat every time.
 */
const IMPLEMENTER_CONTINUE_PROMPT = [
  "Continue working on this issue from where you stopped.",
  "Commit each coherent step as you finish it. Uncommitted work is invisible to the orchestrator and is lost if this turn is cut off.",
  "Once everything the issue asks for is committed and verified, output <promise>COMPLETE</promise>.",
].join("\n\n");

/**
 * Drive the implementer one iteration at a time until it finishes or dies.
 *
 * Handing `maxIterations: 100` to a single run() would mean a quota death
 * burns the remaining 99 iterations inside a call this process cannot see
 * into. Driving the loop here makes each iteration's commits and completion
 * signal observable, which is what lets the breaker and the quota match work.
 *
 * The cost of that visibility used to be a cold agent every iteration: a fresh
 * session re-read the prompt, re-explored the repo and re-derived what it had
 * already decided. Iterations 2+ now resume the previous iteration's session
 * instead, which keeps every per-iteration check exactly as it was while the
 * agent keeps what it learned. `resume` is absent when the provider cannot
 * store sessions, so the cold path stays as the fallback rather than an error.
 */
async function runImplementer(
  sandbox: Awaited<ReturnType<typeof sandcastle.createSandbox>>,
  issue: { id: string; title: string; branch: string },
): Promise<{ commits: { sha: string }[]; completed: boolean }> {
  const history: { commits: number; completed: boolean }[] = [];
  const commits: { sha: string }[] = [];

  const coldStart = () =>
    sandbox.run({
      name: `implementer#${issue.id}`,
      maxIterations: 1,
      agent: sandcastle.claudeCode("claude-sonnet-5"),
      promptFile: "./.sandcastle/implement-prompt.md",
      promptArgs: {
        TASK_ID: issue.id,
        ISSUE_TITLE: issue.title,
        BRANCH: issue.branch,
      },
    });

  let previous: Awaited<ReturnType<typeof sandbox.run>> | undefined;

  for (let i = 1; i <= MAX_IMPLEMENTER_ITERATIONS; i++) {
    if (i > 1 && !previous?.resume) {
      // Worth saying out loud: a run that silently fell back to cold starts
      // still works, but it costs several times as much quota per iteration.
      console.log(
        `No session to resume for #${issue.id} — iteration ${i} starts cold.`,
      );
    }

    const result = previous?.resume
      ? await previous.resume(IMPLEMENTER_CONTINUE_PROMPT)
      : await coldStart();
    previous = result;

    // An agent that dies on quota still resolves its run, so the stdout of a
    // successful call is as important a signal as a thrown error.
    throwIfRunFatal(result.stdout);

    commits.push(...result.commits);
    const completed = result.completionSignal !== undefined;

    // Save whatever this iteration left behind before deciding whether the
    // run is dead. An iteration that edited files but never committed still
    // produces a save commit here, which counts as progress below — only an
    // iteration that changed nothing at all does not.
    const saved = saveWorktree(sandbox.worktreePath, Number(issue.id), "iteration-ended");
    history.push({ commits: result.commits.length + (saved ? 1 : 0), completed });

    if (completed) return { commits, completed: true };

    if (isDeadRun(history)) {
      throw new Error(
        `Implementer for #${issue.id} produced nothing in ${DEAD_ITERATION_THRESHOLD} consecutive iterations — presuming the run is dead.`,
      );
    }
  }

  return { commits, completed: false };
}

/**
 * Implement one issue, then review it if the implementer signalled
 * completion — even with zero commits, since that is the agent reporting the
 * work was already done, and the reviewer still confirms it. Done, from here
 * on, means the reviewer finished without a fatal failure: that is the only
 * thing that earns the Done marker, whatever the commit count was.
 *
 * Sandbox creation reuses an existing issue branch as-is and ignores
 * `baseBranch` for it — the SDK's own behaviour. That is fine now that a
 * stale branch (one holding nothing BASE_REF lacks) is recreated from the
 * integration branch before this runs; see recreateStaleBranches.
 */
async function workIssue(
  issue: { id: string; title: string; branch: string },
  integrationBranch: string,
): Promise<{ commits: { sha: string }[]; completed: boolean }> {
  const sandbox = await sandcastle.createSandbox({
    branch: issue.branch,
    // A new issue branch forks from the batch so far, so it builds on what this
    // group has already merged. The default is the host's HEAD, which is only
    // the batch when something has checked it out — and nothing does any more.
    baseBranch: integrationBranch,
    sandbox: docker(),
    hooks,
  });

  try {
    const implement = await runImplementer(sandbox, issue);
    if (!implement.completed) return implement;

    const review = await sandbox.run({
      name: `reviewer#${issue.id}`,
      maxIterations: 1,
      agent: sandcastle.claudeCode("claude-opus-5"),
      promptFile: "./.sandcastle/review-prompt.md",
      promptArgs: { BRANCH: issue.branch },
    });
    throwIfRunFatal(review.stdout);

    saveWorktree(sandbox.worktreePath, Number(issue.id), "iteration-ended");
    markDone(sandbox.worktreePath, Number(issue.id), integrationBranch);

    return {
      commits: [...implement.commits, ...review.commits],
      completed: true,
    };
  } finally {
    // Safety net for a fatal failure anywhere above: whatever is sitting
    // uncommitted in the worktree at this point is saved before the sandbox
    // — and the worktree with it — closes. A no-op when there is nothing
    // dirty, which is the common case on a clean success.
    saveWorktree(sandbox.worktreePath, Number(issue.id), "run-died");
    await sandbox.close();
  }
}

// ---------------------------------------------------------------------------
// Phase 4: the PR
// ---------------------------------------------------------------------------

/**
 * Push the group's batch and open or refresh its PR.
 *
 * Always a draft while work is outstanding: a partial batch is worth publishing
 * — the next run grows the same PR — but it is not worth anyone's review yet.
 */
function publish(
  group: Group,
  integrationBranch: string,
  complete: boolean,
  blocked: { id: string; title: string; blockedBy: number[] }[],
): boolean {
  if (commitsAhead(BASE_REF, integrationBranch) === 0) {
    console.log(`\n${describeGroup(group.id)}: no commits produced. No PR opened.`);
    return false;
  }

  execSync(`git push -u origin ${integrationBranch}`, { stdio: "inherit" });

  const mergedIssues = resolveMergedIssues(group, integrationBranch);
  const title = buildPrTitle(group, mergedIssues.length);
  const body = buildPrBody({ group, mergedIssues, blockedIssues: blocked, complete });

  const existing = sh(
    `gh pr list --head ${integrationBranch} --state open --json url --jq ".[0].url // empty"`,
  );

  // Title and body go to gh as argv, never through a shell. They are built from
  // issue titles a human wrote and from Markdown that uses backticks, and a
  // JSON-quoted string is still double-quoted to the shell: backticks and `$`
  // run as command substitution, and `\n` escapes arrive as literal text. The
  // first published PR shipped with its group label executed out of the body.
  if (existing) {
    execFileSync(
      "gh",
      ["pr", "edit", integrationBranch, "--title", title, "--body", body],
      { stdio: "inherit" },
    );
    console.log(`\nRefreshed PR for ${integrationBranch}: ${existing}`);
  } else {
    execFileSync(
      "gh",
      [
        "pr", "create", "--draft",
        "--base", BASE_BRANCH,
        "--head", integrationBranch,
        "--title", title,
        "--body", body,
      ],
      { stdio: "inherit" },
    );
    console.log(`\nOpened draft PR for ${integrationBranch} → ${BASE_BRANCH}.`);
  }

  if (complete) {
    // `gh pr ready` on an already-ready PR is a no-op, so a resumed run that
    // finishes a group needs no check of the current draft state.
    sh(`gh pr ready ${integrationBranch}`);
    console.log(`Group ${describeGroup(group.id)} is complete — PR marked ready for review.`);
  } else {
    console.log(`Group ${describeGroup(group.id)} still has outstanding work — PR left as a draft.`);
  }

  return true;
}

// ---------------------------------------------------------------------------
// One group, start to finish
// ---------------------------------------------------------------------------

async function runGroup(group: Group): Promise<boolean> {
  console.log(`\n${"=".repeat(70)}`);
  console.log(`Group ${describeGroup(group.id)} — ${group.issues.length} open issue(s)`);
  console.log(`${"=".repeat(70)}`);

  const integrationBranch = resolveIntegrationBranch(group);

  // Covers the process-killed-with-Ctrl-C path: nothing else runs between an
  // interrupted invocation and this one, so this is the only point that ever
  // sees a worktree left dirty by it.
  saveDirtyWorktreesAtGroupStart(group);

  await pickUpPriorWork(group, integrationBranch);

  let planned: { id: string; title: string; branch: string }[] = [];
  let blocked: { id: string; title: string; blockedBy: number[] }[] = [];
  let settledWithNothingToDo = false;

  for (let iteration = 1; iteration <= MAX_ITERATIONS; iteration++) {
    console.log(`\n=== ${describeGroup(group.id)} — cycle ${iteration}/${MAX_ITERATIONS} ===\n`);

    const alreadyMerged = resolveMergedIssues(group, integrationBranch).map(
      (issue) => Number(issue.id),
    );
    // Rechecked every cycle, not cached: a blocker that closes mid-run — or
    // whose work this run has just merged — should let its dependent join this
    // same run, not wait for the next invocation.
    ({ planned, blocked } = planGroup(group, alreadyMerged));

    if (blocked.length > 0) {
      console.log(`${blocked.length} issue(s) blocked, skipped this cycle:`);
      for (const issue of blocked) {
        console.log(`  #${issue.id}: ${issue.title} (blocked by ${issue.blockedBy.map((n) => `#${n}`).join(", ")})`);
      }
    }

    if (planned.length === 0) {
      // Nothing left that this batch can unblock by itself: every remaining
      // blocker sits outside the integration branch.
      console.log("No unblocked issues left in this group.");
      break;
    }

    console.log(`${planned.length} issue(s) to work in parallel:`);
    for (const issue of planned) {
      console.log(`  ${issue.id}: ${issue.title} → ${issue.branch}`);
    }

    recreateStaleBranches(planned, integrationBranch);

    const settled = await Promise.allSettled(
      planned.map((issue) => workIssue(issue, integrationBranch)),
    );

    // A fatal failure in any pipeline ends the run, but only after every other
    // pipeline has settled — killing sibling agents mid-commit would strand
    // exactly the work this design exists to preserve.
    for (const outcome of settled) {
      if (outcome.status === "rejected") throwIfRunFatal(errorText(outcome.reason));
    }
    for (const [i, outcome] of settled.entries()) {
      if (outcome.status === "rejected") {
        console.error(`  ✗ ${planned[i]!.id} (${planned[i]!.branch}) failed: ${outcome.reason}`);
      }
    }

    // "Completed" here means carrying a Done marker for this integration
    // branch — written inside workIssue once the implementer signalled and
    // the reviewer finished — not merely having produced a commit.
    const ready = new Set(
      readyToMerge(process.cwd(), integrationBranch, groupIssueBranchDescriptors(group)),
    );
    const completed = planned.filter((issue) => ready.has(issue.branch));

    if (completed.length === 0) {
      console.log("No issues marked done this cycle. Nothing to merge.");

      // Every issue reporting completion with nothing to show for it means the
      // work was already done. Replanning would ask the same question and get
      // the same answer, so stop rather than spend the remaining cycles on it.
      const outcomes = settled.map((outcome) => ({
        failed: outcome.status === "rejected",
        commits: outcome.status === "fulfilled" ? outcome.value.commits.length : 0,
        completed: outcome.status === "fulfilled" && outcome.value.completed,
      }));
      if (isSettledWithNothingToDo(outcomes)) {
        console.log("Every issue reports its work was already done. Group finished.");
        settledWithNothingToDo = true;
        break;
      }

      continue;
    }

    console.log(`\n${completed.length} branch(es) with commits:`);
    for (const issue of completed) console.log(`  ${issue.branch}`);

    await sandcastle.run({
      hooks,
      sandbox: docker(),
      branchStrategy: onIntegrationBranch(integrationBranch),
      name: "merger",
      maxIterations: 1,
      agent: sandcastle.claudeCode("claude-sonnet-5"),
      promptFile: "./.sandcastle/merge-prompt.md",
      promptArgs: {
        BRANCHES: completed.map((i) => `- ${i.branch}`).join("\n"),
        ISSUES: completed.map((i) => `- ${i.id}: ${i.title}`).join("\n"),
      },
    });

    console.log("\nBranches merged into integration branch.");
  }

  warnAboutUnfinishedBranches(group, integrationBranch);
  const stillUnfinished = unfinishedBranches(
    process.cwd(),
    integrationBranch,
    groupIssueBranchDescriptors(group),
  ).length;
  stranded += stillUnfinished;

  const complete = isGroupComplete({
    plannedIssues: planned.length,
    blockedIssues: blocked.length,
    settledWithNothingToDo,
    strandedBranches: stillUnfinished,
  });

  return publish(group, integrationBranch, complete, blocked);
}

// ---------------------------------------------------------------------------
// The run
// ---------------------------------------------------------------------------

const allGroups = partitionIntoGroups(fetchOpenIssues());
for (const group of allGroups) assertSafeGroupId(group.id);

const groups = REQUESTED_GROUP
  ? allGroups.filter((group) => group.id === REQUESTED_GROUP)
  : allGroups;

if (REQUESTED_GROUP && groups.length === 0) {
  console.error(
    // The board listing prints raw ids, not describeGroup's rendering: these
    // are the strings you type as the argument, and a solo group's argument is
    // `solo-365`, not the `#365` a message about it would say.
    `No Sandcastle group or solo issue matches ${JSON.stringify(REQUESTED_GROUP)}. Groups on the board: ${allGroups.map((g) => g.id).join(", ") || "(none)"}`,
  );
  process.exit(1);
}

if (groups.length === 0) {
  console.log("No issues are labelled for Sandcastle. Nothing to do.");
  process.exit(0);
}

console.log(`\n${groups.length} group(s), in run order:\n`);
for (const group of groups) {
  const parent = group.parentIssue ? ` (closes spec #${group.parentIssue} when complete)` : "";
  console.log(`  ${describeGroup(group.id)}${parent}`);
  for (const issue of group.issues) {
    const blockers = fetchBlockers(issue);
    const suffix =
      blockers.length > 0 ? ` [blocked by ${blockers.map((n) => `#${n}`).join(", ")}]` : "";
    console.log(`    #${issue.number} ${issue.title}${suffix}`);
  }
  console.log(`    → ${batchBranchGlob(group.id)}, one draft PR`);
}

if (DRY_RUN) {
  console.log("\nSANDCASTLE_DRY_RUN=1 — planned above, nothing executed.");
  process.exit(0);
}

/**
 * Refuse to start a run the sandboxes cannot possibly survive.
 *
 * A stopped Docker daemon or a missing image fails every sandbox in exactly the
 * same way, and it fails them by *throwing* out of createSandbox — which
 * bypasses both the dead-iteration breaker and the fatal-output check, so the
 * run burns every cycle of every group retrying a machine that cannot change
 * mid-run. The costlier half is quieter: a failed create tears down the
 * worktree it had just prepared, so uncommitted work a previous run left behind
 * to be resumed is deleted by a run that never got as far as reading it. One
 * second of checking here is cheaper than either.
 */
function preflightSandbox(): void {
  if (shQuiet(`docker info`) === undefined) {
    console.error(
      `\nDocker is not responding — every sandbox would fail to start. Open Docker Desktop, wait for it to finish starting, then re-run Sandcastle.`,
    );
    process.exit(1);
  }

  const image = defaultImageName(process.cwd());
  if (shQuiet(`docker image inspect ${image}`) === undefined) {
    console.error(
      `\nSandbox image ${image} is missing — every sandbox would fail to start. Build it with 'npx sandcastle docker build-image', then re-run Sandcastle.`,
    );
    process.exit(1);
  }
}

preflightSandbox();

const startBranch = sh(`git rev-parse --abbrev-ref HEAD`);

/**
 * Put the developer's checkout back where they left it.
 *
 * Registered as an exit handler rather than run as a line at the end, because
 * the ends that matter most never reach that line: Ctrl-C and a spent quota
 * both leave through `process.exit`, and stranding someone on an integration
 * branch is a poor way to greet them after a run died overnight. Everything
 * here is synchronous, which an exit handler requires, and nothing here may
 * throw — an exception at this point would mask whatever actually went wrong.
 */
let restored = false;
function restoreStartBranch(): void {
  if (restored) return;
  restored = true;
  try {
    if (sh(`git rev-parse --abbrev-ref HEAD`) === startBranch) return;
    if (shQuiet(`git checkout ${startBranch}`) === undefined) {
      console.error(
        `\nCould not return to ${startBranch} — your checkout is still on the integration branch.`,
      );
    }
  } catch {
    console.error(`\nCould not determine the current branch to restore ${startBranch}.`);
  }
}
process.on("exit", restoreStartBranch);

let fatal: RunFatalError | undefined;

let published = 0;

let failed = 0;

// Branches left holding commits no batch took. Counted so the ending cannot
// claim the agents produced nothing while the warning above lists their work.
let stranded = 0;

for (const group of groups) {
  try {
    if (await runGroup(group)) published++;
  } catch (error) {
    if (error instanceof RunFatalError) {
      fatal = error;
      break;
    }
    const text = errorText(error);
    try {
      throwIfRunFatal(text);
    } catch (rethrown) {
      fatal = rethrown as RunFatalError;
      break;
    }
    failed++;
    console.error(
      `\n✗ Group ${describeGroup(group.id)} failed, continuing to the next group:\n${text}\n`,
    );
  }
}

restoreStartBranch();

const RESUME_ADVICE: Record<Exclude<FailureKind, "local">, string> = {
  quota: "Re-run Sandcastle when your quota resets.",
  auth: "Log the agent in, then re-run Sandcastle.",
  network: "Check the sandbox's connectivity, then re-run Sandcastle.",
};

if (fatal) {
  console.error(`\n${fatal.message}`);
  console.error(
    `Work committed before this point is pushed and covered by its draft PR. ${RESUME_ADVICE[fatal.kind]} It will resume where it stopped.`,
  );
  reportOutcome("interrupted");
  process.exit(2);
}

// A group that threw says nothing either way about what its agents committed —
// the merge step is the last thing to run, so a failure there lands with the
// work already committed on the issue branches. Reporting that as "nothing was
// produced" sends you looking for an agent that did nothing, when what actually
// happened is that finished work never got merged. The commits are not lost:
// the next run picks those branches up.
if (failed > 0) {
  console.error(
    `\n${failed} group(s) failed${published > 0 ? `, ${published} published` : " and nothing was published"}. Any commits their agents made are still on the sandcastle/issue-* branches and the next run will pick them up. The error above says what broke.`,
  );
  reportOutcome("crash");
  process.exit(1);
}

if (published === 0 && stranded > 0) {
  console.error(
    `\nNothing was published, but ${stranded} branch(es) carry finished commits that never reached a batch — see the warning above. The agents did work; it is the merge that did not happen.`,
  );
  reportOutcome("empty");
} else if (published === 0) {
  console.log(
    `\nNo group produced any commits, so nothing was published. Check the logs in .sandcastle/logs/ — the agents ran but left nothing behind.`,
  );
  reportOutcome("empty");
} else {
  console.log(`\nAll done — ${published} group(s) published.`);
  reportOutcome("success");
}
