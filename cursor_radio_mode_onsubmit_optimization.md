# Radio mode onSubmit optimization
_Exported on 22/07/2026 at 12:50:46 CEST from Cursor (3.12.10)_

---

**User**

@frontend/components/arena/AnswerInput.tsx the rendering of radio mode we use setTimeout() for onSubmit(). Is that an optimal way to do it, or passing the option to onSubmit would be better? Or maybe doing it in a different way?

---

**Cursor**

Reviewing `AnswerInput.tsx` and how `onSubmit` is wired in radio mode.


Checking whether click auto-submits and how similar patterns are handled elsewhere.


Identified the issue: `setTimeout` works around React's async state — `onChange(option)` then immediate `onSubmit()` reads stale `userAnswer` in `handleSubmit`. Creating a concise recommendation plan.


---

**User**

Update the plan to include the optional follow-ups you mentioned

---

**Cursor**

Updating the plan to expand the optional follow-ups into actionable implementation items and todos.


Updated the plan to fold in all three follow-ups as concrete work items:

1. **Shared callback type** — add `SubmitAnswerHandler` in `frontend/lib/types.ts` and use it in both `AnswerInput` and `GameArena`.

2. **Simplified Enter handler** — radio Enter calls only `onSubmit(option)`; no separate `onChange` or `setTimeout`, since `handleSubmit` sets `userAnswer` itself.

3. **Click auto-submit parity** — radio `onClick` calls `onSubmit(option)` instead of only `onChange`. The plan also recommends updating the global 1–N keyboard shortcuts the same way so all selection paths behave consistently.

The plan now has four todos (including the core `handleSubmit` change), an expanded files list, and a test plan covering click, Enter, number keys, manual button, text mode, and feedback UI.

Say the word if you want to execute it.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Implementing the plan: starting with the shared type and reading the files to modify.


Checking for a bug: `onClick={onSubmit}` would pass the mouse event as `answerOverride`.


Implemented the plan. Summary of changes:

**[`frontend/lib/types.ts`](frontend/lib/types.ts)** — Added `SubmitAnswerHandler` type for the optional answer override.

**[`frontend/components/arena/GameArena.tsx`](frontend/components/arena/GameArena.tsx)** — `handleSubmit` now accepts an optional `answerOverride`, validates/sends the resolved `answer`, and syncs `userAnswer` when an override is provided.

**[`frontend/components/arena/AnswerInput.tsx`](frontend/components/arena/AnswerInput.tsx)**:
- Radio **click** → `onSubmit(option)` (auto-submit)
- Radio **Enter** → `onSubmit(option)` (removed `setTimeout` and redundant `onChange`)
- **Number keys** (1–N) → `onSubmit(option)` for parity
- Manual **"Sprawdź odpowiedź"** button → `onClick={() => onSubmit()}` so the mouse event is not passed as the answer

All selection paths now submit the known value directly, with no stale-state race or 100ms delay. Text mode and container Enter are unchanged.

---

**User**

Create a file where you will step by step explain this change, explain what was the problem in the code before and how we've fixed it. Assume I don't have in depth knowledge about the code

---

**Cursor**

Reviewing the implemented changes so the explanation matches the current code.


I'm in **Ask mode**, so I can't create files on disk. Switch to **Agent mode** if you want this saved as a file in the repo. Below is the full document you can paste into e.g. `frontend/docs/radio-submit-fix.md`, or I can create it for you in Agent mode.

---

# Radio Mode Submit Fix — Step-by-Step Explanation

## What this app does (relevant parts)

The math learning app shows a question and lets the user answer in two ways:

1. **Text mode** — type an answer in a text box.
2. **Radio mode** — pick one option from a list of buttons.

When the user submits, the frontend sends the answer to the backend and shows feedback (correct/incorrect).

Two React components are involved:

- **`AnswerInput`** — renders the input UI (text box or radio buttons).
- **`GameArena`** — owns the answer state (`userAnswer`) and handles submission to the API.

`AnswerInput` receives:

- `value` — current answer (from parent state)
- `onChange` — update the answer
- `onSubmit` — send the answer to the server

---

## The problem (before the fix)

### Radio mode: pressing Enter on an option

In radio mode, pressing **Enter** on an option should select it and submit immediately.

The old code did this:

```typescript
onChange(option);                    // Step 1: "remember this choice"
setTimeout(() => onSubmit(), 100);   // Step 2: submit after 100ms
```

### Why that was broken

React state updates are **not instant**.

1. `onChange(option)` calls `setUserAnswer(option)` in `GameArena`.
2. React schedules a re-render; `userAnswer` is still the **old** value for a moment.
3. If `onSubmit()` runs right away, `handleSubmit` reads `userAnswer` and often sees:
   - an empty string `''`, or
   - the previous selection.

So submit could fail the “empty answer” check or send the wrong answer.

### The old workaround: `setTimeout(..., 100)`

The code waited 100ms, hoping React would update `userAnswer` before submit.

Problems with that:

- **Arbitrary** — 100ms isn’t guaranteed on slow devices.
- **Slower UX** — noticeable delay on every Enter.
- **Hard to understand** — looks like a random delay, not a real fix.
- **Inconsistent** — click only selected; Enter auto-submitted with a hack.

---

## The fix (what we changed)

**Idea:** When selecting and submitting at the same time, pass the chosen option directly to `onSubmit`, instead of relying on state that hasn’t updated yet.

This is a common React pattern: pass the new value through the callback instead of reading stale state.

---

## Step 1: Shared type for the submit callback

**File:** `frontend/lib/types.ts`

```typescript
export type SubmitAnswerHandler = (answerOverride?: string) => void;
```

- `onSubmit()` — submit whatever is already in state (text mode, manual button).
- `onSubmit("some option")` — submit this specific answer immediately.

---

## Step 2: Update `handleSubmit` in GameArena

**File:** `frontend/components/arena/GameArena.tsx`

**Before:** always used `userAnswer`.

**After:**

```typescript
const handleSubmit: SubmitAnswerHandler = async (answerOverride) => {
  const answer = (answerOverride ?? userAnswer).trim();

  if (answerOverride !== undefined) {
    setUserAnswer(answerOverride);  // keep UI in sync for feedback
  }

  // send `answer` to the API, not `userAnswer`
  user_input: answer,
};
```

- If an override is passed → use it for the API and update state for highlighting.
- If not → use existing `userAnswer` (text mode, “Sprawdź odpowiedź” button, etc.).

---

## Step 3: Update radio interactions in AnswerInput

**File:** `frontend/components/arena/AnswerInput.tsx`

### Click an option

**Before:** `onChange(option)` — select only.  
**After:** `onSubmit(option)` — select and submit in one step.

### Enter on an option

**Before:**

```typescript
onChange(option);
setTimeout(() => onSubmit(), 100);
```

**After:**

```typescript
onSubmit(option);
```

No timer, no stale state.

### Number keys (1, 2, 3…)

**Before:** `onChange(option)` — select only.  
**After:** `onSubmit(option)` — same behavior as click and Enter.

### “Sprawdź odpowiedź” button

Uses `onClick={() => onSubmit()}` (not `onClick={onSubmit}`), so React doesn’t pass the mouse event as the “answer”.

---

## How data flows now

```
User clicks option "1/2"
        ↓
AnswerInput calls onSubmit("1/2")
        ↓
GameArena.handleSubmit("1/2")
  - answer = "1/2"  (no waiting for state)
  - setUserAnswer("1/2")  (for UI highlighting)
  - API receives user_input: "1/2"
        ↓
Feedback shows with correct option highlighted
```

---

## What stayed the same

- **Text mode** — type in the box, submit via form or button; still uses `onSubmit()` with no override.
- **Manual submit button** — still submits current `userAnswer` when the user picks an option first, then clicks submit.
- **Container Enter** — if an option is already selected, Enter on the container still calls `onSubmit()` with existing state.
- **Backend** — no API changes.

---

## Summary

| Topic | Before | After |
|-------|--------|-------|
| Root cause | Submit read state before it updated | Answer passed directly to submit |
| Enter on option | `setTimeout` 100ms hack | `onSubmit(option)` |
| Click on option | Select only | Select + submit |
| Number keys | Select only | Select + submit |
| Reliability | Timing-dependent | Deterministic |
| UX | 100ms delay on Enter | Immediate |

---

## Quick mental model

Think of `userAnswer` as a notebook the parent writes in. When you pick an option and submit in one action, you don’t wait for the notebook to be updated — you hand the answer straight to the submit function: “Submit this: 1/2.”

---

If you want this as a file in the repo (e.g. `frontend/docs/radio-submit-fix.md`), switch to Agent mode and ask me to create it.

