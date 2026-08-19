# Shared helpers move down, not across — Navigation stays split

Navigation is split into two modules: `navigation_snapshot.py` builds the Navigation snapshot, `navigation_resolve.py` validates and resolves a Navigation intent against it. That split stays. The three curriculum helpers they share — `_topics_for_chapter`, `_find_topic_by_id`, `_clamp_level` — do not belong to either module and move down onto `Curriculum` as public methods.

**Why:** The module has been re-cut four times and the same defect survived every swing:

| Commit | Move | Stated reason |
|---|---|---|
| `8c96c61` | `navigation.py` created | — |
| `60ed774` (#16) | split into resolution + view | "focused unit tests" |
| `ad033b8` (#32) | snapshot read model added | — |
| `5e643ff` (#66) | merged back | "one navigation module" |
| `b32fca1` | split into `navigation_snapshot` + `navigation_resolve` | "locality-only split along the boundary the tests already used" |

`git show 5e643ff^:backend/navigation_resolution.py` carries the identical private-import block present today at `navigation_resolve.py:7-12`. Merging did not fix it; it hid it. The helpers are curriculum lookup-and-clamp — they are a property of the Curriculum, not of either navigation side — so each swing dragged them along as private details of whichever file happened to be larger. Once they sit on `Curriculum`, `navigation_resolve` imports only `NavigationSnapshot`: one public name, one direction, stable for the first time.

**Rules:**

1. **If two modules must share private names, the shared thing belongs in a third module — or a lower one. The split is in the wrong place, and the fix is placement, not access.** Renaming `_clamp_level` to `clamp_level` to satisfy the letter of this rule is the wrong fix.
2. **Curriculum owns topic lookup and level clamping.** `Curriculum.topic_by_id(chapter_id, topic_id)` and `Curriculum.clamp_level(level, chapter_id, topic_id)` are the public entry points. `_topics_for_chapter` is deleted — it is a verbatim alias for `curriculum.topics()`.
3. **`TopicDict` is the single topic shape.** `TopicMeta` collapses into it; `topic_id` is added to what `curriculum.topic()` returns. (Verified additive: none of its 7 production callers read `topic_id`.)
4. **Navigation stays split.** Reopening the merge-versus-split question requires new evidence, not a new preference — the history above is the cost of the last four attempts.

**Status of the code:** Rules 2 and 3 are decided but not yet implemented — `Curriculum.topic_by_id()` and `Curriculum.clamp_level()` do not exist yet, and `navigation_resolve.py:7-12` still imports the private helpers.

**Considered options:** Merge the two modules back into one (rejected — that is swing five, and #66 already proved a merge hides this defect rather than fixing it); keep the helpers in `navigation_snapshot` but make them public (rejected — the import direction stays wrong, and navigation would still own a curriculum concern); a mechanical rule banning cross-module `_` imports (rejected — satisfiable by a rename, which leaves the misplacement intact); add a pre-commit tripwire enforcing the rule (rejected for now — one violation repo-wide does not justify it, and a hook cannot check the part that matters, whether the placement is right; the repo already does hook-based enforcement in `fb926cb`, so the option stays live if it recurs).

**Consequences:** Adding a curriculum lookup means adding a `Curriculum` method, not a private helper in the calling module. The Navigation snapshot's lifecycle is deliberately **out of scope** here and remains an open question: it is documented as one-per-request (`navigation_snapshot.py:166`) but built at four sites, is `frozen=True` while holding live session state and a mutable context cache, and memoizes lazily — so answers can depend on cache warmth relative to mutations. That is a separate decision, tracked as an architecture candidate, not settled by this ADR.
