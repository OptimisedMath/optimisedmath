# Learning science and motivation: what the evidence says, and where it hits our design

Research findings for [#179](https://github.com/OptimisedMath/optimisedmath/issues/179) (Learning optimisation). Blocked by [#178](https://github.com/OptimisedMath/optimisedmath/issues/178) for roughly half of what follows.

**Question**: which principles from cognitive science, motivation psychology, and behaviour change are well enough supported to build on, and which of them collide with the mechanics we already have?

**Method**: two Gemini deep-research passes, deliberately given no knowledge of this app — one on learning and retention, one on motivation and adherence. Both were required to produce a fixed-field catalogue with graded evidence, primary citations, effect sizes, population flags, and a mandatory failure-modes clause. The raw reports are `Math Learning Cognitive Science Review.pdf` and `Youth Math Motivation Evidence Review.pdf` in this directory. **Translating findings into our vocabulary is this document's work, not theirs** — everything below the catalogue summary is our reading, not the reports'.

**Scope note**: no principle below is proposed for adoption. This is a survey with opinions attached. #179 remains a Future idea.

---

## 1. The seven findings that actually bear on our design

Ordered by how much they should change what we do, not by evidence strength.

### 1.1 Our progression is forward-only, and the evidence says that is the main defect

`Frontier` is a ratchet. A Student masters a Level, the boundary moves, and nothing ever brings them back except `Replay`, which they must choose for themselves. There is no retention check anywhere in the system: a Topic mastered in October is never revisited in November unless the Student volunteers.

Two well-replicated findings say this is the costliest gap we have:

- **Spacing** — distributed practice beats massed practice, `g = 0.28–0.43` in mathematics specifically, replicated in middle school (Murray et al., 2025). Optimal inter-study interval is roughly 10–20% of the target retention interval (Cepeda et al., 2006): for a Topic that needs to survive to the egzamin ósmoklasisty, that is weeks, not minutes.
- **Interleaving** — mixing problem types beats blocking them, `g = 0.34`, tested heavily in school mathematics (Brunmair & Richter, 2019). Our practice is maximally blocked: one Selected topic, one Selected level, one problem type until Mastery.

**And `Replay` cannot be the answer.** The clearest developmental finding in either report is that 10–14-year-olds systematically avoid exactly these strategies, *because* they feel like failure: interleaved and spaced practice depress performance during acquisition, and learners read that as not learning. Left to self-direct, this age group defaults to massed, blocked practice. A voluntary revisit mechanic will be chosen by precisely the students who need it least.

**Opinion**: this is the single most useful thing the research says. Any retention mechanic we build has to be *served*, not offered — the system decides a Topic is due and puts that Problem in front of the Student. That is a real change to what `Next problem` may serve, and it is the first thing in this document that deserves an ADR when it is decided.

### 1.2 `Deconstruction` is the best-supported thing we have built

Three separate literatures converge on it, and one of them explains why it works better than we argued at the time:

- **Element interactivity** (van Gog & Sweller, 2015) — retrieval practice *stops working, and can reverse*, when a problem requires holding too many interacting elements in working memory at once. For a 12-year-old over that limit, a test is not a learning event; it is overload. The fix in the literature is to decompose the problem into low-interactivity elements and test those. That is a literal description of a `Deconstruction step` derived from `Problem parameters`.
- **The completion-problem effect** — the supported fading strategy is worked example → problem with the last step missing → progressively more steps missing → independent solving. Our `Reveal` is a partial version of this: it shows the answer but still makes the Student enter it.
- **Productive failure** (Sinha & Kapur, 2021, `g = 0.36–0.39`) — struggling *before* instruction improves conceptual transfer, but **only if the struggle is followed by explicit instruction that resolves the gap**. Unresolved failure is just failure. `Deconstruction` firing after repeated `Misconception` hits is the resolving instruction arriving at the moment the gap is open.

**Opinion**: ADR-0004 (Deconstruction outside the Submission cycle) holds up, and the "worth less afterwards" rule is now better justified than it was — the walkthrough *is* the instruction phase, and instruction phases are not assessments.

**Caveat worth carrying**: productive failure predictably generates frustration, and the literature says it needs a facilitator to manage the affect. We have no facilitator. That is a point in favour of `Deconstruction` firing *earlier* rather than later.

### 1.3 Immediate feedback is right for novices and wrong for everyone else

We always show `Feedback` immediately, at every Level, for every Student. The evidence rates feedback timing **Contested**, and the moderator is prior knowledge (Fyfe & Rittle-Johnson, 2012/2016, tested in grades 2–8 in mathematics):

- low prior knowledge → immediate feedback clearly helps, and prevents encoding misconceptions
- **moderate-to-high prior knowledge → immediate feedback measurably harms learning and transfer**, by pre-empting the Student's own error-checking

This is the expertise-reversal effect, and it applies to our `Radio mode` → `Input mode` switch too — in the good direction. Multiple-choice retrieval carries a *larger* effect (`g = 0.70`) than short-answer (`g = 0.48`) in the broad meta-analysis, plausibly through reduced load. Serving ABCD at streak 0 and typed input at streak ≥ 1 is, accidentally, a textbook fading schedule. **That mechanic is validated; leave it alone.**

**Opinion**: the actionable version is fading `Feedback` richness `Behind the Frontier` or at high Levels — not removing it. Speculative enough to leave alone until something else forces the question.

### 1.4 The `Mastery threshold` is defensible; what follows it is not

Mastery learning is **Moderate** (`d = 0.52–0.59`), and strongest in exactly our situation: sequential subjects where knowledge stacks. Two boundary conditions land on us:

- **A threshold set too low lets gaps accumulate and cripples later learning.** The literature's operating point is 80–90% accuracy on formative assessment. Three consecutive correct answers is a *stricter* instantaneous bar (100% over a short window) but a *thinner* sample. Whether 3-in-a-row is the same thing as 85%-over-20 is an open question our telemetry could actually answer.
- **Insisting on immediate perfect mastery produces overlearning, with sharply diminishing returns compared to spacing** (Rohrer & Taylor). The literature's resolution is explicit: reach a *sufficient* threshold, move on, and let spaced retrieval close the gap later.

That resolution is unavailable to us, because we have no "later". Which is §1.1 again, from the other side.

### 1.5 XP, `Flawless`, and streaks sit on the wrong side of the undermining effect

This is where the motivation report is least comfortable reading.

- **The overjustification effect is Strong**: expected, tangible, completion-contingent rewards reduce intrinsic motivation once withdrawn — `d = -0.36` for completion-contingent, `d = -0.41` for expected tangible rewards. **The effect is significantly worse in children than in adults** (Tang & Hall, 1995; Cerasoli et al., 2014). `XP` is expected and completion-contingent by construction.
- **Gamification is Moderate but transient** — real short-term effects (`g = 0.74` behavioural, Sailer & Homner, 2020) with documented novelty decay: week-one motivator, week-six baseline, requiring escalation.
- **`Flawless` is a perfection mechanic in a domain where anxiety is the main threat.** Math anxiety carries `g = -0.467` against achievement (Barroso et al., 2021), and works by consuming working memory. A visible "Bonus — Stracony ❌" is a performance-avoidance cue attached to the exact moment a Student got something wrong.

The mitigations the literature offers are specific, and we already do some by accident: the undermining effect applies to tasks with existing intrinsic interest (much of our audience arrives with none, which is a floor not a defence); *unexpected* rewards and *informational* verbal feedback do not undermine; and process-directed feedback beats trait-directed feedback — our Trap prose is already written in the second person about what the Student *did* (`"Dodałeś do siebie mianowniki!"`), which is the correct register.

**Opinion**: not a reason to remove XP. It is a strong reason never to add a leaderboard (§2), and a reason to look hard at `Flawless`'s framing before we look at adding anything new.

### 1.6 Half of #179's original bullet list is adult psychology

The ticket lists "Atomic Rules applied" and "Commitment to regular practise (e.g. every day at 4pm)". Both were adjudicated directly:

- **"21 days to form a habit": Folk.** Lally et al. (2010) found 18–254 days, median 66, for *simple* behaviours. Voluntary mathematics is neither simple nor affectively neutral.
- **The Atomic Habits framing: Contested for children.** Making a habit obvious, attractive and easy presumes an adult who controls their own schedule, space, and devices. A 10-year-old controls none of these. Expecting them to self-engineer a context cue is developmentally inappropriate.
- **Implementation intentions ("if it is 16:00, then…"): Moderate-to-Strong, and validated on 10–14-year-olds in mathematics** (Duckworth et al., 2013) — but they require a *stable environment* to supply the cue. Shifting school timetables and homework loads destroy it.
- **Habit formation generally: Moderate for academic study, and empirically sparse for children without adult involvement.** True voluntary habits in this age group are adult-scaffolded until the behaviour stabilises.

The mechanism underneath all four is the same, and it is the most important sentence in either report: the striatal reward system peaks in reactivity during early adolescence while the prefrontal cortex matures on a linear path into the mid-twenties. **A 10-year-old is highly responsive to immediate cues and social reward, and cannot act as their own commitment device.**

**Opinion**: "commitment to practise every day at 4pm" is not a Student feature. It is either a parent feature or nothing — which makes it a `#178` design problem, not a `#179` one.

### 1.7 "Sitting in silence after learning" does not survive contact

From the ticket's tips list. Wakeful rest is **Moderate**: the consolidation mechanism is real, but the evidence is adults, in labs, on spatial memory and word lists, and the effect is *instantly nullified* by any cognitive task — including picking up a phone. It requires ~10 minutes, eyes closed, no devices, immediately after encoding.

**Opinion**: unbuildable and unenforceable in a browser app a child closes to open YouTube. Drop it from #179 rather than carrying it.

---

## 2. Decisions this makes cheap, right now

Two things can be settled without building anything:

1. **No leaderboards, ever.** Normative comparison motivates roughly the top decile and pushes everyone else into performance-avoidance; the students with math anxiety log off to protect themselves. This is the clearest "who it doesn't work for" finding in the motivation report, and our audience is the bottom 80% by construction.
2. **No variable-ratio rewards, no endowed progress, no punitive loss aversion** (the "your pet dies if you don't practise" pattern). All three reliably extend time-on-app; none improves learning; all three exploit a reward system that is at peak reactivity at exactly our users' age. Worth stating as a standing constraint so it never has to be re-argued.

---

## 3. Split: usable today vs blocked on #178

Per the brief on #179.

| Finding | Usable today | Needs #178 (accounts, deploy, out-of-app reach) |
|---|---|---|
| Interleaving within a Chapter | ✅ pure curriculum/serving logic | |
| Fading `Feedback` by prior knowledge | ✅ Session-local | |
| `Deconstruction` timing and step design | ✅ | |
| `Flawless` framing and anxiety | ✅ copy and UI only | |
| Leaderboard / dark-pattern exclusions | ✅ a constraint, not a feature | |
| Spaced revisit of mastered Topics | partially — within one long Session | mostly: intervals are days-to-weeks, so it needs durable per-Student state |
| Retention telemetry (does Mastery survive?) | | ✅ needs identity |
| Daily practice habit, implementation intentions | | ✅ needs identity + a reminder channel |
| Anything involving a parent | | ✅ entirely |

**Opinion**: the "usable today" column is larger than expected and the best of it — interleaving — needs no new infrastructure and has a real effect size in school mathematics. If #179 ever spawns a first ticket, that is the one.

---

## 4. What this does to the domain model

Three vocabulary problems surface, none of them resolved. Recording them here rather than editing `CONTEXT.md`, because nothing has been decided.

1. **`Streak` is about to become ambiguous.** It currently means consecutive correct answers *within a Level*, resetting on navigation. #179 wants a *daily practice* streak. Those are different concepts with genuinely different failure modes, and letting one word cover both would be the worst naming decision in the project. Whichever gets built, it needs its own name — and the existing meaning has seniority.
2. **We have no word for retention.** Nothing in `CONTEXT.md` describes knowledge decaying, a Topic falling due, or Mastery expiring. `Frontier` deliberately encodes "earned, permanently". If §1.1 is ever acted on, the model needs a term for a Topic that was mastered and is now due — and that term will have to coexist with `Frontier` without contradicting it.
3. **`Replay` may be the wrong shape.** It is Student-initiated by definition. If retention practice is served rather than chosen, it is not a `Replay` — same screen, different concept, and it *would* touch progression state in ways `Replay` explicitly does not.

---

## 5. Evidence ratings at a glance

Everything the two reports catalogued, compressed. Ratings are theirs.

| Principle | Rating | Effect (maths / children where available) |
|---|---|---|
| Retrieval practice / testing effect | Strong | `g = 0.50–0.61` overall; **`g = 0.18`, CI crosses zero, in mathematics** |
| Spaced / distributed practice | Strong | `g = 0.28–0.43` in mathematics |
| Interleaving | Strong | `g = 0.34` in mathematical problem solving |
| Worked examples / completion problems | Strong | large (>1.0) in early acquisition |
| Productive failure (problem-solving before instruction) | Strong | `g = 0.36–0.39` |
| Generation effect | Strong | `d = 0.40`; elaborative interrogation higher |
| Self-regulated learning instruction | Strong | `d = 0.859` in mathematics |
| Math anxiety ↔ achievement | Strong | `g = -0.467` |
| Self-determination theory (autonomy/competence/relatedness) | Strong | `r ≈ 0.43–0.45` with positive affect |
| Overjustification / reward undermining | Strong | `d = -0.36` to `-0.41`, worse in children |
| Mastery / achievement goal orientation | Strong | moderate correlations |
| Self-efficacy | Strong | `g = 0.518` on mathematical ability |
| Proximal goals over distal goals | Strong (for children, essential) | `d = 0.34` goal-setting overall |
| Goal-gradient effect | Strong | ~20% acceleration near a reward |
| Mastery learning | Moderate | `d = 0.52–0.59` |
| Implementation intentions / WOOP | Moderate–Strong | small-to-medium; validated 10–14 |
| Gamification | Moderate, transient | `g = 0.74` behavioural, decays |
| Habit formation for academic study | Moderate | 18–254 days, median 66 (adults, simple tasks) |
| Streaks / loss aversion | Moderate | adherence real; "what-the-hell" drop-off documented |
| Wakeful rest after learning | Moderate, fragile | not aggregated; nullified by any device use |
| Feedback timing (immediate vs delayed) | **Contested** | positive for novices, **negative for higher prior knowledge** |
| Growth mindset as sold | **Contested / Weak** | `d = 0.05` overall (Sisk et al., 2018) |
| Expanding vs uniform spacing schedules | **Contested → Folk** | `g = 0.034`, n.s. — absolute spacing is what matters |
| Working-memory training / dual n-back | **Weak** | near transfer only |
| Flow as a designable state for novices | **Weak** | gamification → flow: `r = 0.12`, n.s. |
| Learning styles (meshing hypothesis) | **Folk** | no crossover interaction, ever |
| "Neuroplasticity" as prescriptive advice | **Folk** | descriptive biology, not an intervention |
| 1%-better / compounding gains | **Folk** | learning follows a *power law* — diminishing, not compounding |
| "21 days to form a habit" | **Folk** | contradicted by its own source study |
| Dopamine-as-pleasure explanations | **Folk** | reward *prediction error*, not liking |

---

## 6. One Polish-context finding, unprompted

The motivation report surfaced something neither prompt asked for: **MEN's April 2024 regulation effectively eliminated mandatory graded homework in Polish primary schools.** IBE's assessment is that this shifts the burden of academic practice entirely onto the learner's intrinsic motivation or the parents' supervisory capacity.

That is a market fact, not a learning-science one, and it is the most directly commercially relevant sentence in either report — it describes the gap this app sits in. Worth verifying against the regulation itself before it is repeated anywhere that matters.

---

## Sources

The two reports carry ~120 citations between them; both PDFs are in this directory. Load-bearing sources for the opinions above:

- [Murray et al. (2025), A meta-analytic review of the effectiveness of spacing and retrieval practice — Educational Psychology Review](http://aidanhorner.org/papers/Murrayetal_EdPsychReview_2025.pdf) — the mathematics-specific numbers, including the weak testing-effect result
- [van Gog & Sweller (2015), Not New, but Nearly Forgotten: the Testing Effect Decreases or even Disappears as the Complexity of Learning Materials Increases](https://dspace.library.uu.nl/server/api/core/bitstreams/390bc589-b82a-4557-9484-8e84c8331e20/content) — element interactivity; the strongest theoretical support for `Deconstruction`
- [Fyfe & Rittle-Johnson (2012), The Effects of Feedback During Exploration Depend on Prior Knowledge](https://cdn.vanderbilt.edu/vu-sub/wp-content/uploads/sites/280/2023/08/04182512/ATME_Fyfe_CogSciPaper_2012_Final.pdf) — feedback timing, grades 2–8, mathematics
- [Sinha & Kapur (2021), When Problem Solving Followed by Instruction Works](https://www.semanticscholar.org/paper/4712a08981b614f2a06399d4da4bab7636643d78) — productive failure meta-analysis
- [Barroso et al. (2021), A meta-analysis of the relation between math anxiety and math achievement](https://pubmed.ncbi.nlm.nih.gov/33119346/)
- [Tang & Hall (1995), The overjustification effect: a meta-analysis](https://www.semanticscholar.org/paper/bcf84e2e08b82cb62836a3e2edc68a6ad53f35e2) and [Deci, Koestner & Ryan (1999)](https://yukaichou.com/behavioral-analysis/overjustification-effect-lepper-greene-intrinsic-motivation/) — reward undermining, and that it is worse in children
- [Sisk et al. (2018), Do growth mindset interventions impact students' academic achievement?](https://www.researchgate.net/publication/365261074) — `d = 0.05`
- [Latimier et al. (2021), A meta-analytic review of the benefit of spacing out retrieval practice episodes](https://www.researchgate.net/publication/344611197) — expanding vs uniform schedules, `g = 0.034`
- [Sailer & Homner (2020), A meta-analysis on the influence of gamification in formal educational settings](https://www.researchgate.net/publication/353815817)
- [Duckworth et al. (2013), Mental Contrasting With Implementation Intentions improves academic performance in children](https://www.researchgate.net/publication/256294319)
- [IBE, Raport dotyczący prac domowych](https://ibe.edu.pl/pl/aktualnosci/3354-raport-dotyczacy-prac-domowych-trafil-do-men) — the 2024 homework regulation

### Caveats

- **The reports are LLM-generated syntheses, not a systematic review.** Citations were spot-checked for plausibility, not verified one by one. Any number quoted above should be checked against the primary source before it is used to justify building something — particularly the effect sizes, where an LLM attaching the wrong number to the right study is the characteristic failure.
- **Two numbers deserve early scrutiny**, because they carry the most weight here: the mathematics-specific testing-effect result (`g = 0.18`, CI crossing zero) and the `d = 0.859` SRL-in-mathematics figure, which is unusually large for an educational intervention.
- **The reports were given no knowledge of this app**, by design. Every claim in §1 about how a principle collides with `Frontier`, `Mastery`, `Deconstruction`, or `Flawless` is our inference, and none of it was reviewed by the research.
- **The Polish homework-regulation finding is second-hand** via the IBE summary and was not part of either prompt's scope. Verify against the regulation itself.
