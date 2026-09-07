# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

## Sandcastle labels

Sandcastle works one **group** at a time and opens one PR per group, so the label decides which PR an issue's work lands in.

| Label                | Meaning                                                                       |
| -------------------- | ----------------------------------------------------------------------------- |
| `sandcastle:<id>`    | Admits the issue to Sandcastle, in the group `<id>`. One group, one PR.        |
| `sandcastle`         | Admits the issue with no group: it gets a PR of its own.                       |

`<id>` is free-form, but a **numeric id names the parent spec issue** — `sandcastle:218` means "part of #218", and merging that group's PR closes #218 once the group has nothing outstanding. Use the spec's number whenever the work has one; two issues from different specs must never share a group, or they share a review.

Groups run in one sequence per Sandcastle run: numeric ids ascending, then named ids alphabetically, then solo issues. An interrupted run resumes at the same end of the queue, so put the work you most want finished behind the lowest number.
