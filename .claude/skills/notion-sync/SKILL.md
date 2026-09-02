---
name: notion-sync
description: Reconcile the Optimised Math Learning Notion workspace against the codebase and GitHub issues — mirror curriculum databases to match code, rewrite stale spec docs to canonical CONTEXT.md terms, and report Notion-vs-issue drift for the user to decide on. Use when the user asks to sync Notion, check Notion for drift, or update the Notion docs/curriculum DBs.
disable-model-invocation: false
---

Code and `CONTEXT.md` are always the source of truth. Notion only ever gets corrected to match them, never the reverse — this skill has no operation that writes app or issue content *from* Notion without a human decision in between.

Three independent operations. Run only the one(s) the user asked for; if unspecified, run **spec-doc reconciliation** + **issue drift report** (Step 2/3) — they're read-mostly and cheap. Run **curriculum mirror** (Step 1) only when explicitly requested; it rewrites database rows.

## Known workspace map

Root page: `Optimised Math Learning Business` (`32bc26bb-22da-8029-836d-f5515feff577`).

| Notion item | id | Role |
|---|---|---|
| `🏗️ Structure` | `35bc26bb-22da-8051-8443-f8afe91be72f` | spec doc — reconcile |
| `Gamification` | `341c26bb-22da-804e-a012-c41f58ded67f` | spec doc — reconcile |
| `Learning Optimisation` | `3bac26bb-22da-80fe-a880-e4c843ff6494` | spec doc — reconcile |
| `Ułamki Zwykłe` (database) | `353c26bb-22da-80ee-b6bb-da585b80e0bf` | curriculum mirror |
| `Ułamki Dziesiętne` (database) | `353c26bb-22da-800f-ac57-fb0dae1448f4` | curriculum mirror |
| `Businessplan`, `Gem consultant` | — | **out of scope**, never read or edit |

If a page named here 404s, or `backend/chapters/` has a chapter with no row in this table, `notion-search` for it by its Polish chapter name before assuming it doesn't exist in Notion.

## Step 1 — Curriculum mirror

The app generates Traps procedurally (`@declares_traps(...)` in `backend/chapters/<chapter>/topic_*.py`); it does not author static per-level trap text. So the target shape in Notion is a **structural mirror** — Topic/Level rows carrying Trap **slugs** (and Misconception, where a slug maps to one) — never trap prose, since none is authoritative.

For each chapter directory under `backend/chapters/`:
1. Walk its `topic_*.py` files; for every `@declares_traps(...)`-decorated function, record its chapter, topic file, and slug list.
2. Find the matching Notion database from the map above (or by search). If none exists for a chapter that has code, flag it to the user — don't create a new database unasked.
3. Update rows so `T1`/`T2`/`T3`-equivalent fields hold the current slugs for that Topic/Level, dropping slugs no longer in code and adding new ones. Never invent or edit trap *message* text — that field is either left as-is or cleared, never authored by this skill.
4. A Notion row with no code counterpart (chapter/topic removed or renamed) is flagged, not deleted, unless the user confirms.

Done when every chapter directory's declared Trap slugs are reflected in its Notion database and every discrepancy that isn't a clean 1:1 match has been flagged to the user.

## Step 2 — Spec-doc reconciliation

For each spec doc in the map:
1. Fetch the page and the current `CONTEXT.md`.
2. Check every domain term the page uses against `CONTEXT.md`'s entries and their `_Avoid_` lines (e.g. "Macro Topic"/"Micro Topic"/"Level Streak"/"Power of 3"/"Mastered" are known-stale synonyms for Chapter/Topic/Streak/Mastery threshold/Level completion).
3. Check factual claims (mechanics, thresholds, architecture) against the current code, not just wording.
4. Edit the page in Notion (`notion-update-page`) to use canonical terms and current facts. Don't ask permission per-edit — the source-of-truth direction was already settled; just do it and list what changed in your final report.

Done when every spec doc in the map has been checked and any drift found has been corrected in Notion.

## Step 3 — GitHub issue drift report

1. List open issues: `gh issue list --state open --json number,title,body,labels` (see `docs/agents/issue-tracker.md` for conventions).
2. For each distinct idea in the spec docs, classify it against the issue list:
   - **New** — no issue covers it.
   - **Duplicate** — an open issue already covers it.
   - **Contradicted** — an issue documents a decision against it (e.g. #177 parked "gamification beyond current mechanics" — don't resurrect without noting the parked condition).
3. **Report only.** Present the classified list; create or edit nothing yet.
4. Wait for the user's decision on each **New** and **Contradicted** item.
5. Implement exactly what's approved, following `docs/agents/issue-tracker.md` conventions (`gh issue create`/`comment`).

Done when every idea has a classification, the user has ruled on each New/Contradicted item, and every approved action has been taken.

## Final report

State, per operation run: what Notion content changed, what was flagged for the user instead of auto-corrected, and which issue actions were taken vs. still awaiting a decision.
