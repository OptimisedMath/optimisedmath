---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round — all of it, however long that runs. Then wait for the user's answers before the next round.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. Where a fact stays out of reach, ask anyway and mark the claim ⚠️ — the user can see exactly which line to distrust. The _decisions_ are the user's: put each to them and wait.

## Writing a question

Each question is a **briefing**: the user answers it from the message alone, without opening a file, searching the repo, or scrolling back. Spell out every identifier, ID, filename and prior fact the question leans on — restate the one line you depend on rather than citing an earlier round by number.

Six glyphs carry the roles, so the user can skim the left margin for the one they want:

| | |
|---|---|
| 📍 | the round's orientation line |
| 🔎 | a fact you looked up |
| ✏️ | a rendered instance |
| ❓ | a question |
| ⚠️ | unverified — distrust this line |
| ➡️ | your recommendation |

The skeleton:

```
📍 **Round N** — Settled: <what last round closed>. Open: <what this round covers>.

❓ **Q1** — **<question title>**

<what the decision is about, every term spelled out>

🔎 <a fact you verified, stated by content>

✏️ <a real instance, rendered as the end user meets it>

**(a) <short label>** — <what it means, and what it costs>
**(b) <short label>** — <what it means, and what it costs>

➡️ **(x)** — <one line: why>
```

Write a part only when you have something to put in it. A question with nothing to look up and two clean options is a paragraph, two option lines and a recommendation — the skeleton **collapses** to fit its content, and grows only where the content is genuinely there.

- **Render the artefact.** When the decision is about something concrete — an exercise, a UI string, a filename, a schema row — show a real instance of it (✏️), not just its identifier.
- **Options stay as lines**, each one labelled and carrying its consequence. A table earns its place for background you looked up — a set of Levels, a set of files — where a grid beats prose.
- **The recommendation carries its reason.** `➡️ **(b)**` tells the user nothing; one line of why lets them disagree in one word.

A worked example:

> ❓ **Q5** — **Does `frac_div_num_2` keep its name when it moves to T110?**
>
> It generates a whole number divided by a fraction, and it is moving out of `topic_100_dzielenie_liczba.py`.
>
> ✏️ `Oblicz: 4 : ⅗` → `6⅔`, with traps `2⅖` (multiplied without inverting) and `³⁄₂₀` (inverted the wrong way round).
>
> 🔎 Its destination, T110 "Dzielenie ułamków" (`topic_110_dzielenie_ulamkow.py`), is already full:
>
> | Level | Function | Docstring | Example |
> |---|---|---|---|
> | L1 | `frac_div_frac_1` | Proste odwracanie | `⅖ : ¾` → `⁸⁄₁₅` |
> | L2 | `frac_div_frac_2` | Odwracanie i skracanie | `⅘ : ⅔` → `1⅕` |
> | L3 | `frac_div_frac_3` | Dzielenie z liczbami mieszanymi | `2½ : ⅗` → `4⅙` |
>
> The newcomer is easier than all three, so it wants L1 — which `frac_div_frac_1` holds. The numeric suffix is the only thing encoding a Level, and 🔎 nothing in the repo validates suffix against Level, so a mismatch would compile and pass.
>
> **(a) Move the body, keep the name** — one file touched; `frac_div_num_2` then sits at L1 of a frac-÷-frac topic, its name wrong about both family and Level.
> **(b) Rename to `frac_div_frac_1`, cascade the others to `_2/_3/_4`** — four renames plus every reference; bigger diff, honest names.
>
> ➡️ **(b)** — the suffix is the only Level marker there is, so letting it drift costs every future reader a trip to the registry.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
