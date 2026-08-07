# Optimised Math Learning

Polish ed-tech math practice for klasy 4–8. Students work through structured skills, earn XP, and advance by demonstrating mastery at each level.

**Language:** Canonical terms here and in code are English. User-facing copy is Polish — see `docs/adr/0001-english-code-polish-ui.md`.

## Curriculum

**Chapter**:
A broad mathematical area (e.g. Ułamki Zwykłe).
_Avoid_: Track, domain

**Topic**:
One skill within a Chapter (e.g. Dodawanie ułamków).
_Avoid_: micro-skill, module

**Level**:
A difficulty step within a Topic. Each level has its own problems and trap set.

**Topic max level**:
The highest level defined in the curriculum for a Topic — the full depth of that skill. Not the same as how far a student has progressed.

## Progression

**Streak**:
Consecutive correct answers at the current Level. Resets to 0 on a penalized mistake, when the level is completed, or when the student navigates away.
_UI (PL)_: Postęp do kolejnego poziomu (gwiazdki as the visual meter)
_Avoid_: Level Streak, Power of 3, passa

**Penalized mistake**:
A wrong answer that is not a Soft Error. Resets or reduces streak and forfeits Flawless eligibility.
_Avoid_: hard error, real mistake

**Level completion**:
A Level is done when streak reaches 3. Triggers a level unlock or topic completion depending on position in the Topic.
_Avoid_: Advance

**Level unlock**:
The next Level within the same Topic becomes reachable after level completion at the current UnlockedProgress boundary.
_Avoid_: Advance, progress unlock, boundary unlock

**Topic completion**:
Finishing the last Level of a Topic. On the completing Submission, UnlockedProgress opens the next Topic. The student still chooses when to start it via Next problem.
_Avoid_: Advance

**Flawless**:
Whether the student reached the current Level without a penalized mistake since streak last reset. Earns bonus XP when the level is finished.
_UI (PL)_: Bonus — Aktywny 💎 / Stracony ❌
_Avoid_: flawless eligible, flawless bonus

**UnlockedProgress**:
The furthest Topic and Level a student has *earned access to* within a Chapter — not the topic max level, and not necessarily where they are playing right now. Topics before this point are fully open; at the boundary topic, only levels up to the unlocked level are selectable; later topics stay locked.
_Avoid_: unlock frontier, progress boundary, progress map

**Chapter progress**:
Per-chapter record of UnlockedProgress for that chapter.

## Input modes

**Radio mode**:
Four-option multiple choice (ABCD). Active when streak is 0, or for the whole Topic on radio-only topics.
_Avoid_: ABCD mode, multiple choice, text mode

**Input mode**:
The student types the answer. Active when streak ≥ 1 on topics that allow it. Mode switches apply on the next problem, not mid-problem after a submission.
_Avoid_: open answer, text mode, open-ended, free text

**Radio-only topic**:
A Topic that never switches to input mode, regardless of streak.
_Avoid_: text_mode_disabled, input disabled

## Answers

**Problem**:
One generated question instance for the current Level. A fresh instance is served on each request to prevent memorisation.
_Avoid_: exercise, item

**Correct**:
Mathematically right answer for this problem.

**Trap**:
A wrong option based on a predictable misconception. Gets targeted feedback explaining the specific error.
_Avoid_: distractor, diagnostic answer

**Wrong**:
A calculation slip — the method was roughly right but arithmetic failed. Generic feedback, not misconception-specific.
_Avoid_: w1, w2 (internal ids)

**Soft Error**:
Syntax or format issue (e.g. wrong notation). Does not penalize streak or forfeit Flawless.
_Avoid_: format error

## Session

**Submission**:
One answered Problem within a Session — grading, streak/XP updates, and level/topic progression run once per submission.
_Avoid_: turn, answer event, Advance

**Next problem**:
The student dismisses feedback and continues. Loads the next Problem at the current or newly unlocked Level; after topic completion, also navigates to the next Topic at level 1.
_Avoid_: Advance, continue, proceed

**Navigation**:
Changing the selected Chapter, Topic, or Level — via the toolbar or as part of Next problem after topic completion.
_Avoid_: Advance

**Submission cycle**:
One Problem lifecycle within a Session: served → answered (Submission) → Next problem. Navigation or Next problem starts a fresh cycle (streak resets).

**Student**:
The person practicing. May also be called **User** in login and persistence contexts.
_Avoid_: player

**Username**:
The login handle that identifies a Student across sessions.

**Session**:
One play session: current chapter/topic/level selection, streak, active problem, and feedback state.
_Avoid_: GameState (code name)

**XP**:
Experience points earned per correct answer and level completion.

**Admin mode**:
QA and debug access for designated Usernames. Not visible to normal Students. Navigation bypass: all Topics and Levels are selectable regardless of UnlockedProgress. Each Submission follows write rules based on play target vs UnlockedProgress:
- **Beyond UnlockedProgress** (previewing locked content): grading and feedback run; telemetry logs; XP, streak, Flawless, UnlockedProgress, and level/topic completion UI stay frozen.
- **At UnlockedProgress boundary**: normal Student progression — XP, streak, Flawless, and UnlockedProgress advance on mastery.
- **Behind boundary (replay)**: normal XP, streak, and Flawless; UnlockedProgress unchanged (same as Students replaying earned content).
Auto-solve is a visible shortcut through the same Submission pipeline — the UI selects or types the correct answer before submitting. Navigation still resets streak on topic/level change.
_Avoid_: cheat mode, debug mode, preview mode
