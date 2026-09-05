# Documentation rules

What earns a place in the documentation layer, repo-wide.

## The test

Delete it: would a reader plausibly make a **wrong decision** the code alone wouldn't prevent? If no, it does not belong. Rules and conventions stay; narration of what the code already says goes.

## Prose docs

1. **One home per fact.** State it in exactly one doc; everywhere else links. Two docs describing the same ownership will drift.
2. **Pointers carry a trigger.** `[import-rules.md](...) when adding imports or new modules` — the condition under which to read it, never a summary of it. No limit on how deep pointers nest.
3. **ADRs are a dated record.** Amend one when a rule elaborates the decision it already owns; never trim one for length.
4. **`CONTEXT.md` defines words, not behaviour.** One or two sentences per term plus `_Avoid_`; what it IS, not what it does. Behaviour belongs in an ADR or in code. Exception: Trap, Filler, Wrong, Misconception, and Soft Error are defined by their boundaries with each other, so those entries run longer.

## Docstrings

**Every function and class gets a one-line docstring** saying what it does, so a reader can scan a module without reading bodies. Route handlers, Pydantic models, exception classes, accessors and private `_helpers` all included — role is not a reason to skip it in either direction, and privacy least of all.

**Say more only when the extra line carries something the name and signature cannot:**

- what the function **mutates**
- an **invariant or precondition** a caller must respect
- an **ownership rule** — who may call this, who may not
- **why** it exists when an obvious alternative doesn't work

Reference: [session_state.py](../../backend/session_state.py).

**Module docstrings are mandatory** on every non-trivial module — one line naming what the module owns.

**No `Args` or `Returns`** — the signature is typed. `Raises` only where the exception is part of the caller's contract.

Style: imperative one-liner. English for infrastructure.

### Problem generators

Exempt, and required: Polish one-liners on generators, plus short comments naming each Trap's error. This is pedagogical intent, not restated code. Reference: [topic_10_zamiana.py](../../backend/chapters/ulamki_dziesietne/topic_10_zamiana.py).

## Comments

Explain **why**, never **what**. A comment narrating the line beneath it goes. Section dividers are fine.

Exempt: Trap comments in generators, and constraints imposed from outside the file that would otherwise read as a mistake.

## Tests

**Same rule: a one-line docstring on every test**, naming what it pins down. It does not excuse a vague name — the test name is still the specification, so rename a test that needs its docstring to be intelligible. Where the code can't reveal the origin of a regression (an issue number, a past bug), the docstring is where that goes.

## TypeScript

Same rules. No JSDoc restating a TS type. File-header comments are allowed on the `lib/session/` seam files, where the constraint on callers is the point.

## Enforcement

`make lint` fails on `Args:`/`Returns:` sections. A missing one-liner is review, not lint — too much of the tree predates the rule for a checker to be useful yet.
