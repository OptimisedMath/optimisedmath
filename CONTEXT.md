# Optimised Math Learning

Polish ed-tech math practice for klasy 4–8. Students work through structured skills, earn XP, and progress by demonstrating Mastery at each Level.

**Language:** Canonical terms here and in code are English. User-facing copy is Polish — see `docs/adr/0001-english-code-polish-ui.md`.

## Curriculum

**Curriculum**:
The full set of Chapters, Topics, and Levels available to any Student — the content itself, not any one Student's progress through it. Resolved once per request from a single provider (`backend/curriculum.py`) and passed explicitly to lower layers. Distinct from Frontier, which is what one Student has earned.
_Avoid_: content, curriculum data

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

**Streak meter**:
The star-meter display value served on the Session payload. Equals Streak everywhere except at Level completion while Feedback is still on screen, when it stays full so the meter does not visibly empty at the moment the Student earns the Level.
_Avoid_: display streak, meter streak, completed streak pending next problem

**Mastery threshold**:
The streak count required for Level completion at the current Level (currently 3).
_Avoid_: Power of 3, stars for unlock

**Mastery**:
Demonstrating sufficient correctness at the current Level — streak reaching the Mastery threshold while playing At the Frontier.
_Avoid_: pass, complete (as verbs for progression)

**Penalized mistake**:
A wrong answer that is not a Soft Error. Resets or reduces streak and forfeits Flawless eligibility.
_Avoid_: hard error, real mistake

**Level completion**:
A Level is done when streak reaches the Mastery threshold. Triggers a level unlock or topic completion depending on position in the Topic.
_Avoid_: Advance

**Level unlock**:
The next Level within the same Topic becomes Reachable after level completion At the Frontier.
_Avoid_: Advance, progress unlock, boundary unlock

**Topic completion**:
Finishing the last Level of a Topic At the Frontier. On the completing Submission, the Frontier moves to open the next Topic. The student still chooses when to start it via Next problem.
_Avoid_: Advance

**Flawless**:
Whether the student reached the current Level without a penalized mistake since streak last reset. Earns bonus XP when the level is finished.
_UI (PL)_: Bonus — Aktywny 💎 / Stracony ❌
_Avoid_: flawless eligible, flawless bonus

**Frontier**:
The furthest Topic and Level a Student has earned within a Chapter — persisted per Chapter on the profile. Not the topic max level, and not necessarily where they are playing right now. Defines what is Locked vs Reachable for Students.
_Avoid_: UnlockedProgress, unlock frontier, progress boundary, chapter progress, progress map

**Behind the Frontier**:
A Topic or Level before the earned boundary — fully Reachable for Students.

**At the Frontier**:
The current earned boundary Topic and Level — where level unlock and topic completion happen.

**Beyond the Frontier**:
A Topic or Level past what the Student has earned — Locked until Mastery At the Frontier moves the earned boundary.

**Locked**:
Beyond the Frontier for Students — visible in the curriculum but not selectable until the Frontier moves.
_Avoid_: blocked, gated

**Reachable**:
Selectable by a Student: Behind the Frontier, At the Frontier, or any Topic and Level in Admin mode.
_Avoid_: unlocked (as an adjective for content), accessible

**Replay**:
Practising a Topic or Level Behind the Frontier. Streak and XP still run; level unlock and topic completion do not.
_Avoid_: review mode, practice mode

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
An incorrect answer with no misconception behind it — usually a calculation slip, where the method was roughly right but the arithmetic failed. Generic feedback, not misconception-specific. Also covers a mathematically equivalent answer given in the wrong form on a Topic that requires an exact form, since there the form is part of the answer.
_Avoid_: w1, w2 (internal ids)

**Soft Error**:
The answer could not be read as a maths expression, or used a notation the Problem did not ask for. Does not penalize streak or forfeit Flawless. Only applies where the required form was not itself part of the question — otherwise the answer is Wrong.
_Avoid_: format error

**Answer Outcome**:
Which of the above one Submission landed in — the single value the grader returns alongside its feedback, and the one telemetry groups attempts by. Correct answers have none.
_Avoid_: trap_id, error code, result

## Session

**Submission**:
One answered Problem within a Session — grading, streak/XP updates, and level/topic progression run once per submission.
_Avoid_: turn, answer event, Advance

**Feedback**:
The graded result shown after a Submission while the Problem stays under Answer lock — message, type, and whether the answer was Correct. Cleared by Next problem.
_Avoid_: result screen, response state

**Answer lock**:
After a Submission, the active Problem cannot be re-answered until Next problem.
_Avoid_: problem_answered (code name), lock_answer

**Next problem**:
The student dismisses Feedback and continues. Loads the next Problem at the current or newly unlocked Level; after topic completion, also navigates to the next Topic at level 1.
_Avoid_: Advance, continue, proceed

**Navigation**:
Changing the Selected chapter, topic, or level — via the toolbar or as part of Next problem after topic completion.
_Avoid_: Advance

**Navigation snapshot**:
The read model of what a Student can navigate to, built once from the Session and the Curriculum and used to render the toolbar and to validate a Navigation intent. Answers "which Chapters, Topics, and Levels are Reachable, and which is Selected" — it does not change the Session.
_Avoid_: nav state, navigation model, snapshot (unqualified)

**Submission cycle**:
One Problem lifecycle within a Session: served → answered (Submission) → Feedback → Next problem. Navigation or Next problem starts a fresh cycle (streak resets).

**Selected**:
Prefix for the Chapter, Topic, or Level the Session is currently set to — where the Student is playing now, not necessarily At the Frontier. Used as Selected chapter, Selected topic, Selected level.
_Avoid_: current, active, selection

**Student**:
The person practicing. May also be called **User** in login and persistence contexts.
_Avoid_: player

**Username**:
The login handle that identifies a Student across sessions.

**Session**:
One play session: Selected chapter/topic/level, streak, active problem, and Feedback state.
_Avoid_: GameState (code name)

**XP**:
Experience points earned per correct answer and level completion.

**Admin mode**:
A play mode for designated Usernames that makes every Topic and Level Reachable without earned progression and never writes XP, Flawless, or Frontier to the profile. Invisible to normal Students; use a normal Student account to experience the mastery loop.
_Avoid_: cheat mode, debug mode, preview mode, QA mode
