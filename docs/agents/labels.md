# Labels

Every label in this repo's issue tracker, and what applying it commits you to. Four families, and an issue may carry one from each: **triage** says what state it is in, **descriptive** says what it is, **wayfinder** marks a map's children, **sandcastle** decides which PR its work lands in. Operations — creating, fetching, applying labels, closing — are [issue-tracker.md](issue-tracker.md).

## Triage labels

The skills speak in terms of canonical triage roles; this table maps those roles to the label strings used here.

| Label in mattpocock/skills | Label in our tracker | Meaning                                 |
| -------------------------- | -------------------- | --------------------------------------- |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent |
| `wontfix`                  | `wontfix`            | Will not be actioned                    |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

`ready-for-agent` is a claim that an agent can finish the ticket alone. Withhold it whenever the ticket still contains a decision — an unpicked option, a threshold nobody has chosen, a trade-off with no stated winner — and apply `grilling` instead, so the ticket is routed to the conversation that settles it rather than to an agent who would settle it by guessing. A ticket carries one or the other, never both. `grilling` comes off and `ready-for-agent` goes on once the decisions are written into the body.

## Descriptive labels

Orthogonal to triage — they say what an issue *is*, not what state it is in. Apply as many as fit, or none.

| Label         | Meaning                                                             |
| ------------- | ------------------------------------------------------------------- |
| `bug`         | Something shipped behaves wrongly                                   |
| `enhancement` | A change to behaviour that already works                            |
| `documentation` | Docs-only work                                                    |
| `spec`        | A specification issue, typically the parent of a `to-tickets` batch |
| `research`    | Answered by reading sources, not by changing code                   |
| `grilling`    | Answered by a conversation that settles a decision (use the `grill-with-docs` skill) |
| `future idea` | Worth doing, nobody is doing it, no commitment to when              |

## Wayfinder labels

`wayfinder:map` marks a map; `wayfinder:research` / `wayfinder:prototype` / `wayfinder:grilling` / `wayfinder:task` mark its child tickets by type. See [wayfinding operations](issue-tracker.md#wayfinding-operations).

These are meaningful **only inside a map**. An issue detached from its map — ruled out of scope, or orphaned when a map closes — swaps its `wayfinder:<type>` label for the plain descriptive one of the same name (`wayfinder:research` → `research`), because outside a map the type no longer names a ticket a session can claim.

## Sandcastle labels

Sandcastle works one **group** at a time and opens one PR per group, so the label decides which PR an issue's work lands in.

| Label                | Meaning                                                                       |
| -------------------- | ----------------------------------------------------------------------------- |
| `sandcastle:<id>`    | Admits the issue to Sandcastle, in the group `<id>`. One group, one PR.        |
| `sandcastle`         | Admits the issue with no group: it gets a PR of its own.                       |

`<id>` is free-form, but a **numeric id names the parent spec issue** — `sandcastle:218` means "part of #218", and merging that group's PR closes #218 once the group has nothing outstanding. Use the spec's number whenever the work has one; two issues from different specs must never share a group, or they share a review.

Groups run in one sequence per Sandcastle run: numeric ids ascending, then named ids alphabetically, then solo issues. An interrupted run resumes at the same end of the queue, so put the work you most want finished behind the lowest number.
