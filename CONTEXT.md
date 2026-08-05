# Domain glossary — Optimised Math Learning

Terms used across architecture reviews, ADRs, and module interfaces.

## Curriculum hierarchy

- **Chapter** — Broad mathematical domain (e.g. Ułamki Zwykłe). Runtime key: `selected_chapter_id`.
- **Topic** — Skill set within a Chapter (e.g. Dodawanie). Runtime key: `selected_topic_id`.
- **Level** — Difficulty stage within a Topic. Runtime key: `selected_level`.

## Mastery Loop (Power of 3)

The **Dynamic Mastery Loop** governs how a student advances through Levels within a Topic.

- **Level Streak** — Consecutive correct answers at the current Level (`GameState.streak`, max 3). Resets to 0 on Level completion or certain penalties.
- **Power of 3** — Three correct answers in a row at the current Level unlock the next Level (or complete the Topic if at max Level).
- **Input mode** — ABCD (radio) at streak 0; open text at streak ≥ 1 (`STREAK_THRESHOLD_FOR_TEXT_MODE`). Resolved on each `problem/next`, not during submission.
- **Flawless eligible** — Whether the student reached the current Level without a penalized mistake since streak 0. Triggers **Flawless Bonus** XP on Level completion.

## Answer taxonomy

- **Correct** — Mathematically accurate answer.
- **Trap** — Distractor based on a predictable misconception (`t1`, `t2`, `t3`). Triggers targeted feedback.
- **Wrong** — Calculation slip (`w1`, `w2`). Generic wrong feedback.
- **Soft error** — Syntax or format issues (`feedback_type: "info"`). Does not lock the problem or forfeit flawless eligibility.

## Session & persistence

- **GameState** — Mutable session snapshot: progress, streak, current problem, feedback. Serialized to SQLite; enriched with **NavigationView** on API responses only.
- **ChapterProgress** — Per-chapter unlock frontier: `unlocked_topic_id`, `unlocked_level`.

## Mastery Loop module (`backend/mastery_loop.py`)

Deep module for one answered **Turn**. Narrow seam: grading and persistence stay outside.

- **Turn** — One answer submission against the active problem.
- **TurnContext** — Session slice passed in: streak, level, unlock frontier, topic bounds.
- **TurnOutcome** — Pure result: new streak, XP earned, unlock events, Polish feedback on success.
- **apply_turn(eval_result, ctx) → TurnOutcome** — Single interface; `StateManager` applies the outcome and handles telemetry/sync.
