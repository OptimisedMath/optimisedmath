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
//   Phase 1 (Plan):             An opus agent reads the group's open issues,
//                               builds a dependency graph, and outputs a <plan>
//                               JSON listing unblocked issues with branch names.
//   Phase 2 (Execute + Review): Per issue, a sandbox is created. The implementer
//                               is driven one iteration at a time so a dead run
//                               can be cut short; the reviewer follows if it
//                               committed. Issues run concurrently.
//   Phase 3 (Merge):            One agent merges the completed branches.
//   Phase 4 (PR):               Push and open (or refresh) a DRAFT PR. It is
//                               marked ready for review only once the group has
//                               nothing planned and nothing stranded.
//
// A run is built to be killed. Quota exhaustion mid-run is the expected case,
// not an exception: whatever merged is pushed as a draft PR, and the next run
// resumes the same integration branch and grows the same PR.
//
// Usage:
//   npm run sandcastle              # every group, in order
//   npm run sandcastle -- 244       # one group only
//   SANDCASTLE_DRY_RUN=1 npm run sandcastle
//   node --test .sandcastle/lib/    # unit tests for the logic below

import * as sandcastle from "@ai-hero/sandcastle";
import { defaultImageName, docker } from "@ai-hero/sandcastle/sandboxes/docker";
import { z } from "zod";
import { execSync } from "node:child_process";

import { reportOutcome } from "./notify.mts";
import {
  batchBranchGlob,
  batchBranchName,
  buildPrBody,
  buildPrTitle,
  classifyFailure,
  DEAD_ITERATION_THRESHOLD,
  GROUP_LABEL_PREFIX,
  isDeadRun,
  isGroupComplete,
  isRunFatal,
  type FailureKind,
  isSettledWithNothingToDo,
  issueBranchName,
  issueNumberOfBranch,
  partitionIntoGroups,
  type Group,
  type Issue,
} from "./lib/groups.mts";

const planSchema = z.object({
  issues: z.array(
    z.object({ id: z.string(), title: z.string(), branch: z.string() }),
  ),
});

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Plan→execute→merge cycles per group. The loop exists to pick up issues that
// a merge unblocks, so it needs to cover the depth of a dependency chain, not
// the size of the backlog. Deliberately small: with a finite quota, the
// constant that matters is the one that stops a wedged group eating the night.
const MAX_ITERATIONS = 4;

// Upper bound on implementer iterations per issue. Driven one at a time from
// here rather than handed to maxIterations, so the circuit breaker below can
// stop a dead run instead of burning the remainder on container starts.
const MAX_IMPLEMENTER_ITERATIONS = 100;

// Hooks run inside the sandbox before the agent starts. The agent's feedback
// loop is `make test` / `make lint`, so all three toolchains it reaches for —
// root node, frontend node, and the Python env uv manages — must be present, or
// the loop fails in a way the agent will read as a broken repo.
// The 60s default is a budget for a top-up, not an install. When copyToWorktree
// misses — a fresh frontend lockfile, or a sandbox that never got the copy —
// these run cold, and a hook that times out throws the whole group away *after*
// the agents have already done their expensive work. Slow is recoverable; dead
// is not.
const HOOK_TIMEOUT_MS = 10 * 60 * 1000;

const hooks = {
  sandbox: {
    onSandboxReady: [
      { command: "npm install", timeoutMs: HOOK_TIMEOUT_MS },
      { command: "npm install --prefix frontend", timeoutMs: HOOK_TIMEOUT_MS },
      { command: "uv sync", timeoutMs: HOOK_TIMEOUT_MS },
      // Reconciling the copied node_modules against the lockfiles rewrites them,
      // which leaves the worktree dirty before the agent has touched anything.
      // That dirt is indistinguishable from an interrupted agent, so Phase 0
      // refuses to pick the branch up — permanently, since every run redoes the
      // same install. Finished commits then never reach a PR. Setup must leave
      // no trace; this runs before the agent starts, so a lockfile change the
      // agent genuinely intends is unaffected.
      {
        command: "git checkout -- package-lock.json frontend/package-lock.json",
        timeoutMs: HOOK_TIMEOUT_MS,
      },
    ],
  },
};

// Copied from the host before each sandbox starts, so the hooks above are a
// top-up rather than a cold install.
const copyToWorktree = ["node_modules", "frontend/node_modules"];

const BASE_BRANCH = "main";

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

/** Fetch every open issue with its labels, in one call. */
function fetchOpenIssues(): Issue[] {
  const json = sh(
    `gh issue list --state open --limit 200 --json number,title,labels`,
  );
  const raw = JSON.parse(json) as {
    number: number;
    title: string;
    labels: { name: string }[];
  }[];
  return raw.map((issue) => ({
    number: issue.number,
    title: issue.title,
    labels: issue.labels.map((label) => label.name),
  }));
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

/** List branches matching a glob whose commits are already contained in a ref. */
function branchesMergedInto(ref: string, glob: string): string[] {
  return lines(
    sh(`git branch --merged ${ref} --list "${glob}" --format="%(refname:short)"`),
  );
}

/** Count commits on `branch` that `ref` does not already contain. */
function commitsAhead(ref: string, branch: string): number {
  return Number(sh(`git rev-list --count ${ref}..${branch}`));
}

/** The issue branches that could belong to this group, whether or not they exist. */
function groupIssueBranches(group: Group): string[] {
  const existing = new Set(branchesMatching("sandcastle/issue-*"));
  return group.issues
    .map((issue) => issueBranchName(issue.number))
    .filter((branch) => existing.has(branch));
}

/**
 * Resolve the integration branch for a group, resuming one if it exists.
 *
 * A run is resumable: a `sandcastle/batch-<id>-*` branch left by an earlier run
 * is continued so its work — and its PR — carry forward. A fresh branch is cut
 * from BASE_BRANCH only when this group has none outstanding. Branches already
 * merged into BASE_BRANCH have shipped and must not be resumed.
 */
function resolveIntegrationBranch(group: Group): string {
  const shipped = new Set(
    branchesMergedInto(BASE_BRANCH, batchBranchGlob(group.id)),
  );
  const outstanding = branchesMatching(batchBranchGlob(group.id)).find(
    (branch) => !shipped.has(branch),
  );

  if (outstanding) {
    console.log(`\nResuming integration branch: ${outstanding}`);
    sh(`git checkout ${outstanding}`);
    return outstanding;
  }

  const fresh = batchBranchName(group.id, Date.now());
  sh(`git checkout ${BASE_BRANCH}`);
  execSync(`git pull`, { stdio: "inherit" });
  sh(`git checkout -b ${fresh}`);
  console.log(`\nCut integration branch: ${fresh}`);
  return fresh;
}

/**
 * Which of the group's issues does the integration branch already cover?
 *
 * Derived from git rather than run-local state, so it stays correct however
 * many interrupted runs contributed to the branch. Branches already in
 * BASE_BRANCH shipped in an earlier batch and must not be re-announced.
 */
function resolveMergedIssues(
  group: Group,
  integrationBranch: string,
): { id: string; title: string; branch: string }[] {
  const shipped = new Set(
    branchesMergedInto(BASE_BRANCH, "sandcastle/issue-*"),
  );
  const titles = new Map(group.issues.map((i) => [i.number, i.title]));

  return branchesMergedInto(integrationBranch, "sandcastle/issue-*")
    .filter((branch) => !shipped.has(branch))
    .map((branch) => ({ branch, number: issueNumberOfBranch(branch) }))
    .filter(
      (entry): entry is { branch: string; number: number } =>
        entry.number !== undefined && titles.has(entry.number),
    )
    .map((entry) => ({
      id: String(entry.number),
      title: titles.get(entry.number) ?? `Issue #${entry.number}`,
      branch: entry.branch,
    }))
    .sort((a, b) => Number(a.id) - Number(b.id));
}

/** The group's issue branches carrying commits the integration branch lacks. */
function strandedBranches(group: Group, integrationBranch: string): string[] {
  return groupIssueBranches(group).filter(
    (branch) => commitsAhead(integrationBranch, branch) > 0,
  );
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
 * Report the group's work that exists but did not make it into the batch.
 *
 * Phase 0 refuses to merge a branch that is mid-edit, and the planner only ever
 * sees open issues, so a branch can drop out of a batch silently. This does not
 * try to rescue it — merging a half-edit unattended is exactly what Phase 0 is
 * right to refuse — it just makes the omission loud at PR time.
 */
function warnAboutUnmergedBranches(
  group: Group,
  integrationBranch: string,
): void {
  const stranded = strandedBranches(group, integrationBranch);
  if (stranded.length === 0) return;

  console.warn(
    `\n⚠️  ${GROUP_LABEL_PREFIX}${group.id}: ${stranded.length} branch(es) carry commits that are NOT in this PR:\n`,
  );

  for (const branch of stranded) {
    const ahead = commitsAhead(integrationBranch, branch);
    const dirty = worktreeIsDirty(branch);
    const worktree = worktreePathOf(branch);

    console.warn(
      `  ${branch} — ${ahead} unmerged commit(s), ${dirty ? "worktree has uncommitted changes" : "not picked up by any iteration"}`,
    );

    if (dirty) {
      console.warn(`    An agent was interrupted mid-job. Inspect it:`);
      console.warn(`      git -C ${worktree} status`);
      console.warn(`    Then keep the loose changes:`);
      console.warn(`      git -C ${worktree} add -A && git -C ${worktree} commit -m "..."`);
      console.warn(`    ...or discard just the loose changes, keeping the commits:`);
      console.warn(`      git -C ${worktree} restore --staged --worktree .`);
      console.warn(`    ...or leave it and re-run, to let an implementer finish it.`);
    } else {
      console.warn(`    Nothing to do by hand — re-run Sandcastle and it will be picked up.`);
    }
    console.warn("");
  }
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

// ---------------------------------------------------------------------------
// Phase 0: pick up finished work from a prior run
// ---------------------------------------------------------------------------

/** Merge this group's branches that a prior run finished but never merged. */
async function pickUpPriorWork(
  group: Group,
  integrationBranch: string,
): Promise<void> {
  const pickedUp = group.issues
    .map((issue) => ({ issue, branch: issueBranchName(issue.number) }))
    .filter(({ branch }) => branchesMatching(branch).length > 0)
    .filter(({ branch }) => commitsAhead(integrationBranch, branch) > 0)
    .filter(({ branch }) => {
      if (!worktreeIsDirty(branch)) return true;
      console.log(
        `Skipping pickup of ${branch}: worktree has uncommitted changes, letting the normal loop finish it.`,
      );
      return false;
    });

  if (pickedUp.length === 0) return;

  console.log(`\nPicking up ${pickedUp.length} branch(es) from a prior run:`);
  for (const { issue, branch } of pickedUp) {
    console.log(`  ${issue.number}: ${issue.title} → ${branch}`);
  }

  await sandcastle.run({
    hooks,
    sandbox: docker(),
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
 * Choose the group's unblocked issues.
 *
 * A solo group skips the planner entirely: one issue has no dependency graph,
 * and an Opus call to say so is a call the quota can spend elsewhere.
 */
async function planGroup(
  group: Group,
  alreadyMerged: number[],
): Promise<{ id: string; title: string; branch: string }[]> {
  const remaining = group.issues.filter(
    (issue) => !alreadyMerged.includes(issue.number),
  );

  if (group.id.startsWith("solo-")) {
    return remaining.map((issue) => ({
      id: String(issue.number),
      title: issue.title,
      branch: issueBranchName(issue.number),
    }));
  }

  if (remaining.length === 0) return [];

  const plan = await sandcastle.run({
    hooks,
    sandbox: docker(),
    name: "planner",
    maxIterations: 1,
    agent: sandcastle.claudeCode("claude-opus-5"),
    promptFile: "./.sandcastle/plan-prompt.md",
    promptArgs: {
      GROUP_LABEL: `${GROUP_LABEL_PREFIX}${group.id}`,
      ALREADY_MERGED:
        alreadyMerged.length > 0
          ? alreadyMerged.map((n) => `- #${n}`).join("\n")
          : "- (none)",
    },
    output: sandcastle.Output.object({ tag: "plan", schema: planSchema }),
  });

  // The planner is told to skip merged issues, but it is an agent; the
  // integration branch is the authority on what is already done.
  return plan.output.issues.filter(
    (issue) => !alreadyMerged.includes(Number(issue.id)),
  );
}

// ---------------------------------------------------------------------------
// Phase 2: execute + review
// ---------------------------------------------------------------------------

/**
 * Drive the implementer one iteration at a time until it finishes or dies.
 *
 * Handing `maxIterations: 100` to a single run() would mean a quota death
 * burns the remaining 99 iterations inside a call this process cannot see
 * into. Driving the loop here makes each iteration's commits and completion
 * signal observable, which is what lets the breaker and the quota match work.
 */
async function runImplementer(
  sandbox: Awaited<ReturnType<typeof sandcastle.createSandbox>>,
  issue: { id: string; title: string; branch: string },
): Promise<{ commits: { sha: string }[]; completed: boolean }> {
  const history: { commits: number; completed: boolean }[] = [];
  const commits: { sha: string }[] = [];

  for (let i = 1; i <= MAX_IMPLEMENTER_ITERATIONS; i++) {
    const result = await sandbox.run({
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

    // An agent that dies on quota still resolves its run, so the stdout of a
    // successful call is as important a signal as a thrown error.
    throwIfRunFatal(result.stdout);

    commits.push(...result.commits);
    const completed = result.completionSignal !== undefined;
    history.push({ commits: result.commits.length, completed });

    if (completed) return { commits, completed: true };

    if (isDeadRun(history)) {
      throw new Error(
        `Implementer for #${issue.id} produced nothing in ${DEAD_ITERATION_THRESHOLD} consecutive iterations — presuming the run is dead.`,
      );
    }
  }

  return { commits, completed: false };
}

/** Implement one issue, then review it if the implementer committed. */
async function workIssue(issue: {
  id: string;
  title: string;
  branch: string;
}): Promise<{ commits: { sha: string }[]; completed: boolean }> {
  const sandbox = await sandcastle.createSandbox({
    branch: issue.branch,
    sandbox: docker(),
    hooks,
    copyToWorktree,
  });

  try {
    const implement = await runImplementer(sandbox, issue);
    if (implement.commits.length === 0) return implement;

    const review = await sandbox.run({
      name: `reviewer#${issue.id}`,
      maxIterations: 1,
      agent: sandcastle.claudeCode("claude-opus-5"),
      promptFile: "./.sandcastle/review-prompt.md",
      promptArgs: { BRANCH: issue.branch },
    });
    throwIfRunFatal(review.stdout);

    return {
      commits: [...implement.commits, ...review.commits],
      completed: implement.completed,
    };
  } finally {
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
function publish(group: Group, integrationBranch: string, complete: boolean): boolean {
  if (commitsAhead(BASE_BRANCH, integrationBranch) === 0) {
    console.log(`\n${GROUP_LABEL_PREFIX}${group.id}: no commits produced. No PR opened.`);
    return false;
  }

  execSync(`git push -u origin ${integrationBranch}`, { stdio: "inherit" });

  const mergedIssues = resolveMergedIssues(group, integrationBranch);
  const title = buildPrTitle(group, mergedIssues.length);
  const body = buildPrBody({ group, mergedIssues, complete });

  const existing = sh(
    `gh pr list --head ${integrationBranch} --state open --json url --jq ".[0].url // empty"`,
  );

  if (existing) {
    sh(
      `gh pr edit ${integrationBranch} --title ${JSON.stringify(title)} --body ${JSON.stringify(body)}`,
    );
    console.log(`\nRefreshed PR for ${integrationBranch}: ${existing}`);
  } else {
    execSync(
      `gh pr create --draft --base ${BASE_BRANCH} --head ${integrationBranch} ` +
        `--title ${JSON.stringify(title)} --body ${JSON.stringify(body)}`,
      { stdio: "inherit" },
    );
    console.log(`\nOpened draft PR for ${integrationBranch} → ${BASE_BRANCH}.`);
  }

  if (complete) {
    // `gh pr ready` on an already-ready PR is a no-op, so a resumed run that
    // finishes a group needs no check of the current draft state.
    sh(`gh pr ready ${integrationBranch}`);
    console.log(`Group ${GROUP_LABEL_PREFIX}${group.id} is complete — PR marked ready for review.`);
  } else {
    console.log(`Group ${GROUP_LABEL_PREFIX}${group.id} still has outstanding work — PR left as a draft.`);
  }

  return true;
}

// ---------------------------------------------------------------------------
// One group, start to finish
// ---------------------------------------------------------------------------

async function runGroup(group: Group): Promise<boolean> {
  console.log(`\n${"=".repeat(70)}`);
  console.log(`Group ${GROUP_LABEL_PREFIX}${group.id} — ${group.issues.length} open issue(s)`);
  console.log(`${"=".repeat(70)}`);

  const integrationBranch = resolveIntegrationBranch(group);

  await pickUpPriorWork(group, integrationBranch);

  let planned: { id: string; title: string; branch: string }[] = [];

  for (let iteration = 1; iteration <= MAX_ITERATIONS; iteration++) {
    console.log(`\n=== ${GROUP_LABEL_PREFIX}${group.id} — cycle ${iteration}/${MAX_ITERATIONS} ===\n`);

    const alreadyMerged = resolveMergedIssues(group, integrationBranch).map(
      (issue) => Number(issue.id),
    );
    planned = await planGroup(group, alreadyMerged);

    if (planned.length === 0) {
      console.log("No unblocked issues left in this group.");
      break;
    }

    console.log(`${planned.length} issue(s) to work in parallel:`);
    for (const issue of planned) {
      console.log(`  ${issue.id}: ${issue.title} → ${issue.branch}`);
    }

    const settled = await Promise.allSettled(planned.map(workIssue));

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

    const completed = settled
      .map((outcome, i) => ({ outcome, issue: planned[i]! }))
      .filter(
        (entry) =>
          entry.outcome.status === "fulfilled" &&
          entry.outcome.value.commits.length > 0,
      )
      .map((entry) => entry.issue);

    if (completed.length === 0) {
      console.log("No commits produced. Nothing to merge.");

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
        break;
      }

      continue;
    }

    console.log(`\n${completed.length} branch(es) with commits:`);
    for (const issue of completed) console.log(`  ${issue.branch}`);

    await sandcastle.run({
      hooks,
      // The merger resolves conflicts and then runs `make test`, so it needs the
      // same toolchain an issue sandbox gets. Without this its install runs cold.
      copyToWorktree,
      sandbox: docker(),
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

  warnAboutUnmergedBranches(group, integrationBranch);
  stranded += strandedBranches(group, integrationBranch).length;

  const complete = isGroupComplete({
    plannedIssues: planned.length,
    strandedBranches: strandedBranches(group, integrationBranch).length,
  });

  return publish(group, integrationBranch, complete);
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
    `No open issues carry ${GROUP_LABEL_PREFIX}${REQUESTED_GROUP}. Groups on the board: ${allGroups.map((g) => g.id).join(", ") || "(none)"}`,
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
  console.log(`  ${GROUP_LABEL_PREFIX}${group.id}${parent}`);
  for (const issue of group.issues) {
    console.log(`    #${issue.number} ${issue.title}`);
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
      `\n✗ Group ${GROUP_LABEL_PREFIX}${group.id} failed, continuing to the next group:\n${text}\n`,
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
