# Optimised Math Learning

Polish ed-tech math practice for klasy 4–8. Students work through structured skills, earn XP, and progress by demonstrating Mastery at each Level.

**Language:** Canonical terms here and in code are English. User-facing copy is Polish — see [ADR-0001](docs/adr/0001-english-code-polish-ui.md).

This is a glossary: it defines words. Behaviour lives in the ADR or the module that owns it.

## Curriculum

**Curriculum**:
The full set of Chapters, Topics, and Levels available to any Student — the content itself, not any one Student's progress through it. Distinct from Frontier, which is what one Student has earned.
_Avoid_: content, curriculum data

**Chapter**:
A broad mathematical area (e.g. Ułamki Zwykłe).
_Avoid_: Track, domain

**Topic**:
One skill within a Chapter (e.g. Dodawanie ułamków).
_Avoid_: micro-skill, module

**Level**:
A difficulty step within a Topic. Each Level has its own Problems and Traps.

**Topic max level**:
The highest Level defined in the Curriculum for a Topic — the full depth of that skill, not how far a Student has progressed.

## Progression

**Streak**:
Consecutive correct answers at the current Level. Resets to 0 on a penalized mistake, on Level completion, or on Navigation.
_UI (PL)_: Postęp do kolejnego poziomu (gwiazdki as the visual meter)
_Avoid_: Level Streak, Power of 3, passa

**Streak meter**:
The star-meter value served on the Session payload. Equals Streak everywhere except at Level completion while Feedback is still on screen, when it stays full.
_Avoid_: display streak, meter streak, completed streak pending next problem

**Mastery threshold**:
The Streak count required for Level completion (currently 3).
_Avoid_: Power of 3, stars for unlock

**Mastery**:
Demonstrating sufficient correctness at the current Level — Streak reaching the Mastery threshold while playing At the Frontier.
_Avoid_: pass, complete (as verbs for progression)

**Penalized mistake**:
A wrong answer that is not a Soft Error. Resets or reduces Streak and forfeits Flawless eligibility.
_Avoid_: hard error, real mistake

**Level completion**:
A Level is done when Streak reaches the Mastery threshold.
_Avoid_: Advance

**Level unlock**:
The next Level within the same Topic becomes Reachable after Level completion At the Frontier.
_Avoid_: Advance, progress unlock, boundary unlock

**Topic completion**:
Finishing the last Level of a Topic At the Frontier, which moves the Frontier to open the next Topic.
_Avoid_: Advance

**Flawless**:
Whether the Student reached the current Level without a penalized mistake since Streak last reset. Earns bonus XP when the Level is finished.
_UI (PL)_: Bonus — Aktywny 💎 / Stracony ❌
_Avoid_: flawless eligible, flawless bonus

**Frontier**:
The furthest Topic and Level a Student has earned within a Chapter, persisted per Chapter on the profile. Not the Topic max level, and not necessarily where they are playing right now.
_Avoid_: UnlockedProgress, unlock frontier, progress boundary, chapter progress, progress map

**Behind the Frontier**:
A Topic or Level before the earned boundary — fully Reachable for Students.

**At the Frontier**:
The current earned boundary Topic and Level — where Level unlock and Topic completion happen.

**Beyond the Frontier**:
A Topic or Level past what the Student has earned — Locked until Mastery At the Frontier moves the boundary.

**Locked**:
Beyond the Frontier for Students — visible in the Curriculum but not selectable.
_Avoid_: blocked, gated

**Reachable**:
Selectable by a Student: Behind the Frontier, At the Frontier, or anywhere in Admin mode.
_Avoid_: unlocked (as an adjective for content), accessible

**Replay**:
Practising a Topic or Level Behind the Frontier. Streak and XP still run; Level unlock and Topic completion do not.
_Avoid_: review mode, practice mode

## Input modes

**Radio mode**:
Four-option multiple choice (ABCD). Active when Streak is 0, or for the whole Topic on radio-only topics.
_Avoid_: ABCD mode, multiple choice, text mode

**Input mode**:
The Student types the answer. Active when Streak ≥ 1 on Topics that allow it.
_Avoid_: open answer, text mode, open-ended, free text

**Radio-only topic**:
A Topic that never switches to Input mode, regardless of Streak.
_Avoid_: text_mode_disabled, input disabled

## Answers

**Problem**:
One generated question instance for the current Level. A fresh instance is served on each request to prevent memorisation.
_Avoid_: exercise, item

**Correct**:
Mathematically right answer for this Problem.

**Trap**:
An authored wrong answer for one Level — anticipated by a person, and carrying its own targeted feedback explaining the specific error. Most Traps reference a Misconception; a Trap whose error is a slip rather than a believed rule references none, and still carries its own prose. An answer matching no Trap is Wrong too, but unanticipated.
_Avoid_: distractor, diagnostic answer, "wrong" as a Trap's identity (a Trap may grade as Wrong; and w1/w2 were Fillers, never Traps)

**Trap slug**:
The name a Trap is known by within one generator — one slug per wrong rule that generator can compute. Unique within a generator, not across the Curriculum.
_Avoid_: t1, t2, t3 (positional slots, not identities)

**Filler**:
A wrong option that exists only to fill a radio button when a Level has fewer Traps than slots — an arbitrary near miss with no anticipated rule behind it, so it carries no prose and no Misconception. It grades as Wrong with the generic message, exactly as an unanticipated answer does. Once we can say how the mistake was made, it is a Trap, not a Filler.
_Avoid_: w1, w2 (positional slots), padding option

**Misconception**:
A wrong rule a Student believes and applies — a named, recurring error in their mathematical thinking (e.g. operating on only one part of a fraction), independent of any single Problem or Level. The belief is what makes it a Misconception: an error with no false rule behind it, such as misreading a symbol, is a slip, and the Trap carrying it references none. Which entry a Trap references, and whether it earns one at all, is decided by the rules in [misconceptions.yaml](backend/data/misconceptions.yaml).
_Avoid_: error pattern, bug, trap type, entry, catalogue entry, t1/t2 (positional slots, not identities)

**Misconception slug**:
The name a Misconception is known by in the catalogue — a stable, human-readable English key, not a database id. Telemetry records it alongside a Trap's own Trap slug.
_Avoid_: misconception_id, misconception number

**Wrong**:
An incorrect answer with no Misconception behind it — a slip, where the Student's rules were sound but their execution was not. Also covers a mathematically equivalent answer given in the wrong form on a Topic that requires an exact form, since there the form is part of the answer. Wrong is a grading outcome, not a category of authored answer: a Wrong answer is very often an authored Trap with its own prose, because whether a person anticipated it and whether it maps to a Misconception are separate facts.
_Avoid_: w1, w2 (internal ids)

**Unit**:
The physical dimension marker an answer carries — `cm²`, `m`, `ha`. How a Level declares Units and how the grader converts and matches them is [ADR-0005](docs/adr/0005-conversion-aware-unit-grading.md).
_Avoid_: measure, dimension (for the marker itself), suffix

**Problem fingerprint**:
A hash of a Problem's question, correct answer, and options — identifies when two generated Problems are the same content-wise even though their problem_ids differ. Used to avoid serving a Problem the Student just saw.
_Avoid_: dedup key, content hash

**Soft Error**:
The answer could not be read as a maths expression, or used a notation the Problem did not ask for. Does not penalize Streak or forfeit Flawless. Only applies where the required form was not itself part of the question — otherwise the answer is Wrong.
_Avoid_: format error

**Answer Outcome**:
Which of the above one Submission landed in — what the grader returns alongside its feedback. Telemetry records it with the Misconception slug and the Trap slug where each applies.
_Avoid_: trap_id, misconception_id, error code, result

## Session

**Submission**:
One answered Problem within a Session — grading, Streak/XP updates, and Level/Topic progression run once per Submission.
_Avoid_: turn, answer event, Advance

**Feedback**:
The graded result shown after a Submission while the Problem stays under Answer lock — message, type, and whether the answer was Correct. Cleared by Next problem.
_Avoid_: result screen, response state

**Answer lock**:
After a Submission, the active Problem cannot be re-answered until Next problem. Lifted once, exceptionally, by a completed Deconstruction.
_Avoid_: problem_answered (code name), lock_answer

**Next problem**:
The Student dismisses Feedback and continues, loading the next Problem. Unavailable while a Deconstruction is active.
_Avoid_: Advance, continue, proceed

**Navigation**:
Changing the Selected chapter, topic, or level — via the toolbar or as part of Next problem after Topic completion.
_Avoid_: Advance

**Navigation snapshot**:
The read model of what a Student can navigate to, built from a Session and the Curriculum. Answers "which Chapters, Topics, and Levels are Reachable, and which is Selected" — it does not change the Session.
_Avoid_: nav state, navigation model, snapshot (unqualified)

**Submission cycle**:
One Problem lifecycle within a Session: served → answered (Submission) → Feedback → Next problem.

**Deconstruction**:
A guided walkthrough that takes over when a Student hits the same Misconception repeatedly at a Level, breaking the Problem in front of them into steps they answer themselves before returning them to that same Problem. It is not a Submission — see [ADR-0004](docs/adr/0004-deconstruction-outside-submission-cycle.md).
_Avoid_: speed bump, intervention, hint mode, tutorial

**Abandonment**:
A Deconstruction that ended without reaching its final step — whether the Student used the walkthrough's exit control or navigated away. One concept, not two: the doors differ only in what telemetry records.
_Avoid_: skip, quit, drop out, bail

**Deconstruction step**:
One question within a Deconstruction, derived from the Problem's parameters rather than authored per Problem.
_Avoid_: sub-problem, micro-step

**Reveal**:
Showing a Student the correct answer to a Deconstruction step after they have got it wrong repeatedly. The step is not skipped — the Student still enters the revealed answer to advance.
_Avoid_: hint, give up, solution, skip

**Problem parameters**:
The structured values a Problem was generated from (operands, denominators, dimensions), carried on the Problem alongside its rendered question. What lets a Deconstruction speak about the exact Problem on screen.
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
One play session: Selected chapter/topic/level, Streak, active Problem, and Feedback state.
_Avoid_: GameState (code name)

**XP**:
Experience points earned per correct answer and Level completion.

**Admin mode**:
A play mode for designated Usernames that makes every Topic and Level Reachable without earned progression and never writes XP, Flawless, or Frontier to the profile. Invisible to normal Students.
_Avoid_: cheat mode, debug mode, preview mode, QA mode
