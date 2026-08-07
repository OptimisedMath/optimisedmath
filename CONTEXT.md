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
Consecutive correct answers at the current Level. Resets to 0 on a penalized mistake or when the level is completed.
_UI (PL)_: Postęp do kolejnego poziomu (gwiazdki as the visual meter)
_Avoid_: Level Streak, Power of 3, passa

**Level completion**:
A Level is done when streak reaches 3. Triggers a level unlock or topic completion depending on position in the Topic.

**Level unlock**:
The next Level within the same Topic becomes reachable after level completion at the current UnlockedProgress boundary.

**Topic completion**:
Finishing the last Level of a Topic. Opens the next Topic at level 1.

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
_Avoid_: turn, answer event

**Student**:
The person practicing.
_Avoid_: user, player

**Session**:
One play session: current chapter/topic/level selection, streak, active problem, and feedback state.
_Avoid_: GameState (code name)

**XP**:
Experience points earned per correct answer and level completion.

**Admin mode**:
Bypass of topic and level lock rules for designated usernames. Not visible to normal students.
_Avoid_: cheat mode, debug mode
