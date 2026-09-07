// Unit tests for the Sandcastle grouping and failure logic.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  batchBranchGlob,
  batchBranchName,
  buildPrBody,
  buildPrTitle,
  classifyFailure,
  groupIdOf,
  isDeadRun,
  isGroupComplete,
  isRunFatal,
  isSettledWithNothingToDo,
  issueNumberOfBranch,
  parentIssueOf,
  partitionIntoGroups,
  type Issue,
} from "./groups.mts";

const issue = (number: number, labels: string[]): Issue => ({
  number,
  title: `Issue ${number}`,
  labels,
});

test("a sandcastle:<id> label admits an issue under that group id", () => {
  assert.equal(groupIdOf(issue(245, ["ready-for-agent", "sandcastle:218"])), "218");
});

test("a bare sandcastle label admits an issue as its own solo group", () => {
  assert.equal(groupIdOf(issue(999, ["sandcastle"])), "solo-999");
});

test("an issue carrying neither label is not admitted", () => {
  assert.equal(groupIdOf(issue(300, ["ready-for-agent"])), undefined);
});

test("a group label wins over a bare sandcastle label on the same issue", () => {
  assert.equal(groupIdOf(issue(245, ["sandcastle", "sandcastle:218"])), "218");
});

test("an empty group suffix does not admit the issue", () => {
  assert.equal(groupIdOf(issue(245, ["sandcastle:"])), undefined);
});

test("a numeric group id names the parent spec issue, a named one does not", () => {
  assert.equal(parentIssueOf("218"), 218);
  assert.equal(parentIssueOf("telemetry"), undefined);
});

test("issues partition into groups, each holding only its own issues", () => {
  const groups = partitionIntoGroups([
    issue(245, ["sandcastle:218"]),
    issue(255, ["sandcastle:244"]),
    issue(246, ["sandcastle:218"]),
    issue(400, ["ready-for-agent"]),
  ]);

  assert.deepEqual(
    groups.map((g) => [g.id, g.issues.map((i) => i.number)]),
    [
      ["218", [245, 246]],
      ["244", [255]],
    ],
  );
});

test("numeric groups run ascending, before named groups, before solo issues", () => {
  const groups = partitionIntoGroups([
    issue(1, ["sandcastle"]),
    issue(2, ["sandcastle:telemetry"]),
    issue(3, ["sandcastle:244"]),
    issue(4, ["sandcastle:99"]),
  ]);

  assert.deepEqual(groups.map((g) => g.id), ["99", "244", "telemetry", "solo-1"]);
});

test("two-digit numeric groups sort before three-digit ones, not after", () => {
  // The bug a plain string sort would introduce: "218" < "99".
  const groups = partitionIntoGroups([
    issue(1, ["sandcastle:218"]),
    issue(2, ["sandcastle:99"]),
  ]);

  assert.deepEqual(groups.map((g) => g.id), ["99", "218"]);
});

test("solo groups sort by issue number rather than by string", () => {
  const groups = partitionIntoGroups([
    issue(218, ["sandcastle"]),
    issue(99, ["sandcastle"]),
  ]);

  assert.deepEqual(groups.map((g) => g.id), ["solo-99", "solo-218"]);
});

test("a group's branch glob matches its own batch branches and no other group's", () => {
  const branch = batchBranchName("218", 1_700_000_000_000);

  assert.equal(branch, "sandcastle/batch-218-1700000000000");
  assert.equal(batchBranchGlob("218"), "sandcastle/batch-218-*");
  assert.ok(!branch.startsWith("sandcastle/batch-244-"));
});

test("an issue branch name round-trips to its issue number", () => {
  assert.equal(issueNumberOfBranch("sandcastle/issue-245"), 245);
});

test("a batch branch is not mistaken for an issue branch", () => {
  assert.equal(issueNumberOfBranch("sandcastle/batch-218-1700000000000"), undefined);
});

test("a usage-limit message is classified as fatal to the whole run", () => {
  assert.equal(classifyFailure("Claude AI usage limit reached|1700000000"), "quota");
  assert.ok(isRunFatal("quota"));
});

test("an expired login is classified as fatal to the whole run", () => {
  assert.equal(classifyFailure("OAuth token has expired. Please run /login"), "auth");
  assert.ok(isRunFatal("auth"));
});

test("an ordinary test failure is local to its group and does not stop the run", () => {
  assert.equal(classifyFailure("FAILED tests/test_grader.py::test_flawless"), "local");
  assert.ok(!isRunFatal("local"));
});

test("three consecutive commit-less unfinished iterations mark a run dead", () => {
  const dead = { commits: 0, completed: false };

  assert.ok(isDeadRun([dead, dead, dead]));
});

test("two dead iterations are not yet enough to trip the breaker", () => {
  const dead = { commits: 0, completed: false };

  assert.ok(!isDeadRun([dead, dead]));
});

test("a commit inside the window keeps the run alive", () => {
  const dead = { commits: 0, completed: false };

  assert.ok(!isDeadRun([dead, { commits: 1, completed: false }, dead]));
});

test("an iteration that signalled completion keeps the run alive", () => {
  const dead = { commits: 0, completed: false };

  assert.ok(!isDeadRun([dead, dead, { commits: 0, completed: true }]));
});

test("only the last N iterations count, so early exploration is forgiven", () => {
  const dead = { commits: 0, completed: false };
  const alive = { commits: 2, completed: true };

  assert.ok(!isDeadRun([dead, dead, dead, alive]));
});

test("a group is complete only when nothing is planned and nothing is stranded", () => {
  assert.ok(isGroupComplete({ plannedIssues: 0, strandedBranches: 0 }));
  assert.ok(!isGroupComplete({ plannedIssues: 1, strandedBranches: 0 }));
  assert.ok(!isGroupComplete({ plannedIssues: 0, strandedBranches: 1 }));
});

test("an incomplete group's PR references the parent spec without closing it", () => {
  const body = buildPrBody({
    group: { id: "218", parentIssue: 218, issues: [] },
    mergedIssues: [{ id: "245", title: "Emit expression structure" }],
    complete: false,
  });

  assert.ok(body.includes("Closes #245: Emit expression structure"));
  assert.ok(body.includes("Part of #218"));
  assert.ok(!body.includes("Closes #218"));
  assert.ok(body.includes("Draft"));
});

test("a complete group's PR closes the parent spec", () => {
  const body = buildPrBody({
    group: { id: "218", parentIssue: 218, issues: [] },
    mergedIssues: [{ id: "245", title: "Emit expression structure" }],
    complete: true,
  });

  assert.ok(body.includes("Closes #218"));
  assert.ok(!body.includes("Part of #218"));
  assert.ok(!body.includes("Draft"));
});

test("a named group closes its children but has no parent spec to close", () => {
  const body = buildPrBody({
    group: { id: "telemetry", parentIssue: undefined, issues: [] },
    mergedIssues: [{ id: "300", title: "Something" }],
    complete: true,
  });

  assert.ok(body.includes("Closes #300: Something"));
  assert.ok(!body.includes("Closes #undefined"));
  assert.ok(!/Part of #/.test(body));
});

test("a resumed branch with no newly merged issues still explains itself", () => {
  const body = buildPrBody({
    group: { id: "218", parentIssue: 218, issues: [] },
    mergedIssues: [],
    complete: false,
  });

  assert.ok(body.includes("Carried forward from an earlier interrupted run"));
});

test("the PR title names the spec a group serves", () => {
  assert.equal(
    buildPrTitle({ id: "218", parentIssue: 218, issues: [] }, 3),
    "Sandcastle: #218 — 3 issue(s)",
  );
});

test("a solo group's PR title names the issue itself", () => {
  assert.equal(
    buildPrTitle({ id: "solo-999", parentIssue: undefined, issues: [] }, 1),
    "Sandcastle: #999 — 1 issue(s)",
  );
});

// --- a cycle that had nothing to do ---------------------------------------

test("a group whose every issue reports completion without commits is finished", () => {
  assert.equal(
    isSettledWithNothingToDo([
      { failed: false, commits: 0, completed: true },
      { failed: false, commits: 0, completed: true },
    ]),
    true,
  );
});

test("a cycle that produced commits is not a cycle with nothing to do", () => {
  assert.equal(
    isSettledWithNothingToDo([{ failed: false, commits: 2, completed: true }]),
    false,
  );
});

test("an issue that never signalled completion leaves the group retryable", () => {
  assert.equal(
    isSettledWithNothingToDo([{ failed: false, commits: 0, completed: false }]),
    false,
  );
});

test("a failed issue leaves the group retryable", () => {
  assert.equal(
    isSettledWithNothingToDo([{ failed: true, commits: 0, completed: false }]),
    false,
  );
});

test("one unfinished issue is enough to keep a group going", () => {
  assert.equal(
    isSettledWithNothingToDo([
      { failed: false, commits: 0, completed: true },
      { failed: false, commits: 0, completed: false },
    ]),
    false,
  );
});

test("an empty cycle proves nothing, since planning handles that case", () => {
  assert.equal(isSettledWithNothingToDo([]), false);
});

// --- network failures ------------------------------------------------------

test("the API being unreachable is a network failure, not a local one", () => {
  assert.equal(
    classifyFailure(
      "API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)",
    ),
    "network",
  );
});

test("DNS and connection errors are recognised by their codes", () => {
  assert.equal(classifyFailure("Error: getaddrinfo EAI_AGAIN api.anthropic.com"), "network");
  assert.equal(classifyFailure("connect ECONNREFUSED 127.0.0.1:443"), "network");
});

test("a network failure ends the whole run, since the next container fares no better", () => {
  assert.equal(isRunFatal("network"), true);
});

test("a spent quota still outranks a network error in the same output", () => {
  assert.equal(
    classifyFailure("usage limit reached; also ENOTFOUND while retrying"),
    "quota",
  );
});

test("an ordinary test failure is still local", () => {
  assert.equal(classifyFailure("FAILED tests/test_session.py::test_streak"), "local");
  assert.equal(isRunFatal("local"), false);
});
