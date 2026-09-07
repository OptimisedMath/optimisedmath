// Grouping, ordering and failure classification for the Sandcastle run.
//
// Everything here is a pure function over strings and lists, deliberately
// separated from main.mts so the paths that only fire when nobody is watching
// — the circuit breaker, the quota match, the completion test — can be tested
// without a sandbox or a quota. main.mts owns all git, gh and agent calls.

/** The admission label for an issue with no group: one issue, one PR. */
export const SOLO_LABEL = "sandcastle";

/** Prefix that admits an issue to a Sandcastle group. */
export const GROUP_LABEL_PREFIX = "sandcastle:";

/** Consecutive dead implementer iterations before a run is presumed dead. */
export const DEAD_ITERATION_THRESHOLD = 3;

export interface Issue {
  readonly number: number;
  readonly title: string;
  readonly body?: string;
  readonly labels: string[];
}

export interface Group {
  /** Group id: the label suffix, or `solo-<issue>` for an ungrouped issue. */
  readonly id: string;
  /** A numeric group id names the parent spec issue that it closes. */
  readonly parentIssue: number | undefined;
  readonly issues: Issue[];
}

/** Read the group id an issue is admitted under, or undefined if it is not admitted. */
export function groupIdOf(issue: Issue): string | undefined {
  const groupLabel = issue.labels.find((label) =>
    label.startsWith(GROUP_LABEL_PREFIX),
  );
  if (groupLabel) {
    const id = groupLabel.slice(GROUP_LABEL_PREFIX.length).trim();
    return id.length > 0 ? id : undefined;
  }
  return issue.labels.includes(SOLO_LABEL) ? `solo-${issue.number}` : undefined;
}

/** A group id that is purely numeric names the parent spec issue to close. */
export function parentIssueOf(groupId: string): number | undefined {
  return /^\d+$/.test(groupId) ? Number(groupId) : undefined;
}

/**
 * Partition open issues into the groups a run will work, in run order.
 *
 * Ordering is numeric ids ascending, then named ids alphabetically, then solo
 * issues by number. Stability matters more than cleverness: a run that keeps
 * being interrupted must keep draining the same end of the queue rather than
 * scattering half-finished work across every group.
 */
export function partitionIntoGroups(issues: Issue[]): Group[] {
  const byId = new Map<string, Issue[]>();

  for (const issue of issues) {
    const id = groupIdOf(issue);
    if (!id) continue;
    const existing = byId.get(id);
    if (existing) existing.push(issue);
    else byId.set(id, [issue]);
  }

  const groups = [...byId.entries()].map(([id, groupIssues]) => ({
    id,
    parentIssue: parentIssueOf(id),
    issues: [...groupIssues].sort((a, b) => a.number - b.number),
  }));

  return groups.sort(compareGroups);
}

/** Rank two groups into run order: numeric ids first ascending, then named ids. */
function compareGroups(a: Group, b: Group): number {
  const rank = (group: Group) => {
    if (group.parentIssue !== undefined) return 0;
    return group.id.startsWith("solo-") ? 2 : 1;
  };

  const rankDelta = rank(a) - rank(b);
  if (rankDelta !== 0) return rankDelta;

  if (a.parentIssue !== undefined && b.parentIssue !== undefined) {
    return a.parentIssue - b.parentIssue;
  }
  // Solo ids share the `solo-<number>` shape, so compare the numbers rather
  // than the strings — otherwise `solo-99` would sort after `solo-218`.
  const soloNumbers = [a, b].map((group) =>
    Number(group.id.replace(/^solo-/, "")),
  );
  if (soloNumbers.every((n) => Number.isFinite(n))) {
    return soloNumbers[0]! - soloNumbers[1]!;
  }
  return a.id.localeCompare(b.id);
}

/** Name the integration branch a group's work is merged into. */
export function batchBranchName(groupId: string, timestamp: number): string {
  return `sandcastle/batch-${groupId}-${timestamp}`;
}

/** Glob matching every integration branch belonging to one group. */
export function batchBranchGlob(groupId: string): string {
  return `sandcastle/batch-${groupId}-*`;
}

/** Name the working branch for a single issue. */
export function issueBranchName(issueNumber: number): string {
  return `sandcastle/issue-${issueNumber}`;
}

/** Read the issue number out of a `sandcastle/issue-<N>` branch name. */
export function issueNumberOfBranch(branch: string): number | undefined {
  const match = branch.match(/^sandcastle\/issue-(\d+)$/);
  return match ? Number(match[1]) : undefined;
}

/**
 * Decide whether a failure is specific to one group or fatal to the whole run.
 *
 * Quota exhaustion and a broken login kill every group equally, so continuing
 * only burns container starts. Anything else is the group's own problem and
 * the next group deserves its turn.
 */
export type FailureKind = "quota" | "auth" | "network" | "local";

const QUOTA_PATTERNS = [
  /usage limit reached/i,
  /usage limit will reset/i,
  /credit balance is too low/i,
  /insufficient credits/i,
];

// A machine that cannot reach the API will not be able to reach it on the next
// iteration either, and each retry costs a container start. Observed during the
// #260 smoke test, where a transient outage burned three cycles.
const NETWORK_PATTERNS = [
  /can't reach the api server/i,
  /\bENOTFOUND\b/,
  /\bECONNREFUSED\b/,
  /\bEAI_AGAIN\b/,
  /getaddrinfo/i,
  /network[_ ]error/i,
];

const AUTH_PATTERNS = [
  /invalid api key/i,
  /authentication[_ ]error/i,
  /please run \/login/i,
  /oauth token has expired/i,
];

/** Classify agent output or an error message as a run-fatal failure or a local one. */
export function classifyFailure(text: string): FailureKind {
  if (QUOTA_PATTERNS.some((pattern) => pattern.test(text))) return "quota";
  if (AUTH_PATTERNS.some((pattern) => pattern.test(text))) return "auth";
  if (NETWORK_PATTERNS.some((pattern) => pattern.test(text))) return "network";
  return "local";
}

/** Quota, auth and network failures end the whole run; a local one ends only its group. */
export function isRunFatal(kind: FailureKind): kind is Exclude<FailureKind, "local"> {
  return kind !== "local";
}

/**
 * Decide whether a run of iterations has stopped making progress.
 *
 * The backstop behind classifyFailure(): it needs nothing from the agent's
 * wording, so it catches a quota message we failed to anticipate, a crashed
 * image and a wedged sandbox alike. The implementer's prompt tells it to commit
 * at the end of every iteration, so consecutive commit-less iterations that
 * never signalled completion are already abnormal.
 */
export function isDeadRun(
  iterations: { commits: number; completed: boolean }[],
  threshold: number = DEAD_ITERATION_THRESHOLD,
): boolean {
  if (iterations.length < threshold) return false;
  return iterations
    .slice(-threshold)
    .every((iteration) => iteration.commits === 0 && !iteration.completed);
}

/**
 * Decide whether a group has nothing left outstanding.
 *
 * Both halves matter: an empty plan alone would call a group done while one of
 * its branches sat stranded with unmerged commits, and that PR would go out as
 * ready for review with work missing from it.
 */
export function isGroupComplete(state: {
  plannedIssues: number;
  strandedBranches: number;
}): boolean {
  return state.plannedIssues === 0 && state.strandedBranches === 0;
}

/** Title the PR for a group's batch. */
export function buildPrTitle(group: Group, mergedIssues: number): string {
  const scope = group.parentIssue
    ? `#${group.parentIssue}`
    : group.id.startsWith("solo-")
      ? `#${group.id.replace(/^solo-/, "")}`
      : group.id;
  return `Sandcastle: ${scope} — ${mergedIssues} issue(s)`;
}

/**
 * Build the PR body for a group's batch.
 *
 * The parent spec is only closed once the group is complete: a draft PR that
 * already said `Closes #218` would close the spec the moment you merged a
 * partial batch.
 */
export function buildPrBody(options: {
  group: Group;
  mergedIssues: { id: string; title: string }[];
  complete: boolean;
}): string {
  const { group, mergedIssues, complete } = options;
  const lines = [
    `Automated batch for \`${GROUP_LABEL_PREFIX}${group.id}\`, completed by Sandcastle.`,
    "",
  ];

  if (mergedIssues.length > 0) {
    lines.push(...mergedIssues.map((i) => `Closes #${i.id}: ${i.title}`));
  } else {
    lines.push(
      "Carried forward from an earlier interrupted run; see the commits on this branch.",
    );
  }

  if (group.parentIssue !== undefined) {
    lines.push("");
    lines.push(
      complete
        ? `Closes #${group.parentIssue}`
        : `Part of #${group.parentIssue}`,
    );
  }

  if (!complete) {
    lines.push("");
    lines.push(
      "Draft: this group still has outstanding work. Re-running Sandcastle folds it into this PR.",
    );
  }

  return lines.join("\n");
}

/**
 * Did a cycle prove there is nothing left for this group to do?
 *
 * An issue that signals completion without producing a commit is telling us its
 * work was already done. When that holds for every issue in a cycle, replanning
 * can only produce the same answer, so the group is finished and further cycles
 * are pure waste. A failure, or an issue that never signalled, means the
 * opposite — a retry may still get somewhere.
 */
export function isSettledWithNothingToDo(
  outcomes: { failed: boolean; commits: number; completed: boolean }[],
): boolean {
  return (
    outcomes.length > 0 &&
    outcomes.every((o) => !o.failed && o.commits === 0 && o.completed)
  );
}
