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
An authored wrong answer for one Level — anticipated by a person, and carrying its own targeted feedback explaining the specific error. Most Traps reference a Misconception, and several Traps across different Topics may reference the same one; a Trap whose error is a slip rather than a believed rule references none, and still carries its own prose. Where a Submission is wrong in both its number and its Unit, the number decides which Trap it is: a Trap diagnosing the Unit fires only on the expected number, so an answer whose number matches another Trap is that Trap, and its Unit is corroborating evidence rather than a second fault. An answer matching no Trap is Wrong too, but unanticipated.
_Avoid_: distractor, diagnostic answer, "wrong" as a Trap's identity (a Trap may grade as Wrong; and w1/w2 were Fillers, never Traps)

**Trap slug**:
The name a Trap is known by within one generator — one slug per wrong rule the generator can compute, declared up front so a Level's authored prose can be checked against what its templates actually emit. Slugs are unique within a generator, not across the curriculum: the same wrong rule appearing in two generators may share a name without being the same Trap.
_Avoid_: t1, t2, t3 (positional slots, not identities)

**Filler**:
A wrong option that exists only to fill a radio button when a Level has fewer Traps than slots — an arbitrary near miss with no anticipated rule behind it, so it carries no prose and no Misconception. A Filler grades as Wrong with the generic message, exactly as an unanticipated answer does. Once we can say how the mistake was made, it is a Trap, not a Filler.
_Avoid_: w1, w2 (positional slots), padding option

**Misconception**:
A wrong rule a Student believes and applies — a named, recurring error in their mathematical thinking (e.g. operating on only one part of a fraction), independent of any single Problem or Level. The belief is what makes it a Misconception: an error with no false rule behind it, such as misreading a symbol or pairing the wrong operands, is a slip, and the Trap carrying it references no Misconception however reliably a walkthrough could correct it. Membership is a property of the answer, not of the Student who gave it: a Trap references a Misconception when a believed rule exists whose natural output is that answer, not when this Student can be shown to have held it. Some Students reach such an answer by slip, and that does not disqualify it — a single Submission never proves a belief, and nothing acts on one, since a Misconception surfaces only in telemetry aggregation and in a Deconstruction that already requires repetition. Which Misconception a Trap references is decided by the Problem's shape, not by the wrong answer's arithmetic alone: where two entries both fit the arithmetic, only the one whose rule is true of the Problem on screen may be referenced, and where no entry's shape is present in the Problem at all — no mixed number, no second operand — the Trap references none. Traps reference a Misconception rather than owning their own error identity; a Misconception is what telemetry groups a Student's errors by and what a Deconstruction is authored against.
_Avoid_: error pattern, bug, trap type, t1/t2 (positional slots, not identities)

**Misconception slug**:
The name a Misconception is known by in the catalogue — the English key under which it is authored in the global misconceptions list, referenced by every Trap that maps to it. Not a database primary key or a number: it is a stable, human-readable identity, the same way a Trap slug names a Trap. Telemetry records it alongside a Trap's own Trap slug when the Trap maps to one.
_Avoid_: misconception_id, misconception number

**Wrong**:
An incorrect answer with no misconception behind it — a slip, where the Student's rules were sound but their execution was not: the arithmetic failed, a symbol was misread, or the wrong operands were paired. Feedback is generic where the answer was unanticipated, and the Trap's own prose where it was. Also covers a mathematically equivalent answer given in the wrong form on a Topic that requires an exact form, since there the form is part of the answer. Likewise covers an answer that omits a Unit the Problem expects, since there the Unit is part of the answer. Wrong is a grading outcome, not a category of authored answer: a Wrong answer is very often an authored Trap with its own prose, because whether a person anticipated it and whether it maps to a Misconception are separate facts.
_Avoid_: w1, w2 (internal ids)

**Unit**:
The physical dimension marker an answer carries — `cm²`, `m`, `ha`. A Problem that expects one names it, and the Student types it as part of their answer in Input mode, while in Radio mode every option carries the same Unit and none of them is typed; a Unit of the same dimension is converted before comparison, so a correct conversion is Correct. A Unit of the wrong dimension, or the right number under the wrong Unit, is a Trap. Degrees are not a Unit: `°` is shown beside the answer field but never typed, never expected, and never graded.
_Avoid_: measure, dimension (for the marker itself), suffix

**Problem fingerprint**:
A hash of a Problem's question, correct answer, and options — identifies when two generated Problems are the same content-wise even though their problem_ids differ. Used to avoid serving the Student a Problem they just saw.
_Avoid_: dedup key, content hash

**Soft Error**:
The answer could not be read as a maths expression, or used a notation the Problem did not ask for. Does not penalize streak or forfeit Flawless. Only applies where the required form was not itself part of the question — otherwise the answer is Wrong. Units never land here: a Unit is either read (converted and accepted) or the answer is penalized.
_Avoid_: format error

**Answer Outcome**:
Which of the above one Submission landed in — what the grader returns alongside its feedback. Telemetry records it alongside two further independent facts about the same attempt: which Misconception it maps to, if any, by Misconception slug, and, for a Trap, its Trap slug. Correct answers have none of the three.
_Avoid_: trap_id, misconception_id, error code, result

## Session

**Submission**:
One answered Problem within a Session — grading, streak/XP updates, and level/topic progression run once per submission.
_Avoid_: turn, answer event, Advance

**Feedback**:
The graded result shown after a Submission while the Problem stays under Answer lock — message, type, and whether the answer was Correct. Cleared by Next problem.
_Avoid_: result screen, response state

**Answer lock**:
After a Submission, the active Problem cannot be re-answered until Next problem. Lifted once, exceptionally, by a completed Deconstruction, which returns the Student to the triggering Problem for a second attempt.
_Avoid_: problem_answered (code name), lock_answer

**Next problem**:
The student dismisses Feedback and continues. Loads the next Problem at the current or newly unlocked Level; after topic completion, also navigates to the next Topic at level 1. Unavailable while a Deconstruction is active — dismissing Feedback would otherwise skip the walkthrough while keeping everything the Problem was worth.
_Avoid_: Advance, continue, proceed

**Navigation**:
Changing the Selected chapter, topic, or level — via the toolbar or as part of Next problem after topic completion.
_Avoid_: Advance

**Navigation snapshot**:
The read model of what a Student can navigate to, built from a Session and the Curriculum and used to render the toolbar and to validate a Navigation intent. Answers "which Chapters, Topics, and Levels are Reachable, and which is Selected" — it does not change the Session.
_Avoid_: nav state, navigation model, snapshot (unqualified)

**Submission cycle**:
One Problem lifecycle within a Session: served → answered (Submission) → Feedback → Next problem. Navigation or Next problem starts a fresh cycle (streak resets).

**Deconstruction**:
A guided walkthrough that takes over when a Student hits the same Misconception repeatedly at a Level. It breaks the Problem in front of them into sequential steps they answer themselves, then returns them to that same Problem. A Deconstruction is not a Submission: it runs outside the Submission cycle, so it never moves Streak, XP, Flawless, or the Frontier — though the Problem it interrupts is worth less afterwards. It opens with a brief **pause**: the triggering answer's Feedback stays on screen, without the correct answer, long enough to read the Trap prose before the takeover appears. A Deconstruction ends either by reaching its final step or by Abandonment, and either way it does not fire again for that Misconception at that Level for the rest of the Session.
_Avoid_: speed bump, intervention, hint mode, tutorial

**Abandonment**:
A Deconstruction that ended without reaching its final step — whether the Student used the walkthrough's exit control or navigated away. One concept, not two: the doors differ only in what telemetry records. An abandoned Deconstruction leaves the triggering Problem under Answer lock with its correct answer revealed, so nothing more can be earned from it.
_Avoid_: skip, quit, drop out, bail

**Deconstruction step**:
One question within a Deconstruction, derived from the Problem's parameters rather than authored per Problem. Answered by the Student to advance the walkthrough.
_Avoid_: sub-problem, micro-step

**Reveal**:
Showing a Student the correct answer to a Deconstruction step after they have got it wrong repeatedly. The step is not skipped — the Student still enters the revealed answer to advance. A Reveal is the walkthrough's only escalation; there is no lesser tier below it, because a Deconstruction step is already the help a Student gets after the Trap prose did not land.
_Avoid_: hint, give up, solution, skip

**Problem parameters**:
The structured values a Problem was generated from (operands, denominators, dimensions), carried on the Problem alongside its rendered question. What lets a Deconstruction speak about the exact Problem on screen instead of an analogous one.
_Avoid_: params (unqualified), problem data

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
