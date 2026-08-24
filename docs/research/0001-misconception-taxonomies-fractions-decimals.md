# Prior art: misconception taxonomies for fractions and decimals

Research findings for [#167](https://github.com/OptimisedMath/optimisedmath/issues/167). Blocks [#168](https://github.com/OptimisedMath/optimisedmath/issues/168) (the Misconception catalogue).

**Question**: before clustering 227 hand-written traps into a named Misconception catalogue, what vocabulary and what *granularity precedent* exists in maths-education literature?

**Scope note**: we want vocabulary and a precedent. No taxonomy below is proposed for wholesale adoption — none of them is shaped like our problem (each covers one task, or one arithmetic procedure, not two whole Chapters of a Polish klasy 4–8 curriculum).

---

## 1. What the local error set actually looks like

Counted from `backend/data/Ułamki_Zwykłe.yaml` and `backend/data/Ułamki_Dziesiętne.yaml`:

| | Ułamki Zwykłe | Ułamki Dziesiętne | Total |
|---|---|---|---|
| Levels | 50 | 45 | 95 |
| Trap explanations (`t1`/`t2`/`t3`) | 116 | 111 | 227 |
| Textually distinct | | | 218 |

Reading the prose, the traps fall into three clearly different *kinds*, and this matters more than any count:

1. **Genuine conceptual misconceptions** — a wrong mental model, reusable across Topics.
   e.g. `"Dodałeś do siebie mianowniki! Przy dodawaniu ułamków mianownik ZAWSZE przepisujemy bez zmian."`, `"Pomnożyłeś na krzyż! Przy mnożeniu ułamków zasada to: 'Góra z górą, dół z dołem'."`, `"Przesunąłeś przecinek w lewą stronę! Mnożenie robi liczbę WIĘKSZĄ..."`
2. **Procedural slips inside a correct method** — the model is right, one step was dropped.
   e.g. `"Zapomniałeś przenieść '1' do wyższego rzędu!"`, `"Zapomniałeś o pożyczaniu z sąsiedniego rzędu!"`
3. **Non-errors** — pure arithmetic failure with no theory behind it.
   e.g. `"Błąd sumowania."`, `"Zły wynik mnożenia."`, `"Błąd w obliczeniach."`

Category 3 is already `Wrong` under `CONTEXT.md`, not a Misconception. That is a meaningful slice of the 227 — a first pass suggests **20–30 traps are category 3 and should never enter the catalogue at all**.

The same misconception is also *already* duplicated across Topics under different prose. "Operated on only one part of the fraction" appears at least six times with different wording (rozszerzanie t1/t2, skracanie t1/t2, skracanie-do-końca t2/t3, wspólny mianownik t2). That repetition is the strongest evidence the catalogue is worth building.

---

## 2. Brown & Burton — "bugs" (1978)

[Diagnostic Models for Procedural Bugs in Basic Mathematical Skills](https://onlinelibrary.wiley.com/doi/pdf/10.1207/s15516709cog0202_4), Cognitive Science 2(2), and the follow-up [Repair Theory](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog0404_3) (Brown & VanLehn, 1980).

The founding work. Key claims relevant to us:

- A bug is a **deterministic perturbation of a correct procedure**, not a random slip — the model "provides a mechanism for explaining *why* a student is making a mistake as opposed to simply identifying the mistake." That is exactly the Trap→Misconception relationship we are proposing.
- The BUGGY/DEBUGGY systems catalogued bugs for **multidigit subtraction alone** — a single procedure, narrower than one of our Levels — and still converged on a database of **roughly 100 systematically defined bugs**.
- Bugs are named descriptively and mechanically, not thematically: e.g. *smaller-from-larger*, *borrow-across-zero*, *diff-0-N=N*.

**Granularity verdict on Brown & Burton: very fine, and deliberately so.** Their unit of analysis is one broken step in one algorithm. Note the naming convention though — a bug name states *the wrong rule the student is following*, in the student's terms. That is the right register for our names, and it is what most of our good trap prose already does.

**Warning**: Brown & Burton's fineness is affordable because BUGGY was a *diagnostic* system — it only had to label, never to teach. We have to author a Deconstruction against each Misconception. Their granularity is not ours to copy.

---

## 3. Ashlock — "error patterns"

[Error Patterns in Computation: Using Error Patterns to Improve Instruction](https://www.pearson.com/en-us/subject-catalog/p/Ashlock-Error-Patterns-in-Computation-Using-Error-Patterns-to-Help-Each-Student-Learn-10th-Edition/P200000000739/9780135009109) (Ashlock, 10th ed.). [Archive copy](https://archive.org/details/errorpatternsinc0000ashl).

- Ashlock's unit is the **error pattern**: a consistent wrong procedure inferred from several worked examples, presented to teachers as a diagnostic exercise ("here are five of a student's answers — find the pattern").
- Organised **by operation and number domain**, with dedicated chapters for addition/subtraction with fractions and decimals, and multiplication/division with fractions and decimals. Patterns are given opaque catalogue identifiers rather than evocative names (e.g. `A-W-1` for the first error pattern in Addition–Whole numbers), with a prose description carrying the meaning.

I could not obtain the full per-chapter pattern list from a primary source — the book is not freely available and the Pearson sample chapter would not extract. Treat the identifier-scheme detail as second-hand.

**Granularity verdict on Ashlock: fine, and per-operation.** Roughly a dozen or two named patterns per operation family. Critically, Ashlock's patterns are **scoped to an operation** — the "adds denominators" pattern lives in the fractions-addition chapter and is not shared with the fraction-comparison chapter, even where the underlying thinking is the same.

**Opinion**: this is a precedent to *reject*. Our whole reason for a catalogue is cross-Topic reuse — telemetry grouping and one Deconstruction serving many Traps. Ashlock's operation-scoped filing would give us back the duplication we are trying to remove.

---

## 4. Resnick et al. / Sackur-Grisvard & Leonard — decimal comparison rules

Resnick et al. (1989) renamed the erroneous decimal-comparison rules identified by Sackur-Grisvard & Leonard (1985):

| Rule | Name | Thinking |
|---|---|---|
| Rule 1 | **whole number rule** | reads the decimal part as a whole number, so 0.125 > 0.3 (immature conception based on natural numbers) |
| Rule 2 | **fraction rule** | over-generalises "a tenth is always bigger than a hundredth", so 0.3 > 0.45 |
| Rule 3 | **zero rule** | a leading zero in the decimal part makes the number small |

Source: [PME30 review of decimal comparison research](https://www.emis.de/proceedings/PME30/4/425.pdf); [Developmental changes in the comparison of decimal fractions](https://www.sciencedirect.com/science/article/abs/pii/S0959475209000711).

**This is the single most useful naming precedent in the survey.** Three names cover the entire error space of one task, and each name states a *rule the student is applying*, sourced to *where the student learned it* (whole numbers; fractions). Resnick's framing — prior knowledge of whole numbers and of fractions each both supports *and* interferes with the decimal concept — is directly applicable to our two Chapters, which are exactly those two prior knowledge bases sitting next to each other.

**Granularity verdict: very coarse. Three named misconceptions for a task on which we have at least four Levels and a dozen traps.**

---

## 5. Stacey & Steinle — the Decimal Comparison Test (the key precedent)

[The incidence of misconceptions of decimal notation amongst students in Grades 5 to 10](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/backinfo/refs/merga98stst.pdf) (MERGA 1998); [Incidence of the various ways of thinking](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/tests/incidenc.htm); [Steinle thesis, 2004](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/backinfo/refs/steinlethesis2004.pdf). Data: 3204 students, 12 schools, Years 4–10, 1995–1999.

This is the most rigorous decimals taxonomy found, and it is explicitly **three-tiered** — which is why it matters more to #168 than anything else here.

**Tier 1 — 4 coarse codes:**

| Code | Behaviour |
|---|---|
| **A** | Apparent-expert |
| **L** | Longer-is-larger (0.125 > 0.3) |
| **S** | Shorter-is-larger (0.3 > 0.496) |
| **U** | Unclassified |

**Tier 2 — 12 fine codes** (response-pattern classifications), each linking to one or two ways of thinking.

**Tier 3 — the named ways of thinking**, which is the layer we would actually reuse:

| Coarse | Named way of thinking | Incidence Yr5 → Yr10 |
|---|---|---|
| L | **whole number thinking** | 35% → 2% |
| L | **column overflow thinking** (squeezes a multi-digit number into one column) | 5% → 1% (combined) |
| L | **zero makes small thinking** | " |
| L | **reverse thinking** | 1% → 0% |
| S | **denominator focussed thinking** (4.65 < 4.3 as hundredths < tenths) | 4% → 2% |
| S | **reciprocal thinking** (0.3 > 0.4 by analogy with 1/3 > 1/4) | 6% → 3% (combined) |
| S | **negative thinking** | " |
| A | **expert thinking** | 24% → 70% |
| A | **money thinking** (correct until >2 decimal places are needed) | 2% → 5% |

**Take this number seriously: a four-year research programme, 3204 students, dedicated to the single task of comparing two decimals, names roughly 9 ways of thinking and 12 fine codes.**

Three things to steal:

1. **The named-way-of-thinking register.** Every name is a gerund phrase describing what the student is doing — "column overflow thinking", "money thinking" — never a description of the wrong answer. `CONTEXT.md`'s example ("operating on only one part of a fraction") is already in this register. Keep it.
2. **The two-tier split of coarse family + specific thinking.** L and S are behavioural families; the ways of thinking are the diagnoses under them. Several distinct misconceptions produce the *same* observable wrong answer.
3. **"Apparent-expert" and "unclassified" are first-class categories.** They resisted the temptation to force every response pattern into a misconception. Our `Wrong` term already does this job — hold the line on it.

---

## 6. Fractions: named misconceptions from the cognitive literature

There is no single fractions equivalent of the DCT, but a small stable vocabulary exists:

- **Natural number bias / whole number bias** — "the tendency to apply natural number features in rational number tasks where this is inappropriate" ([Van Hoof et al., Memory & Cognition](https://link.springer.com/article/10.3758/s13421-020-01045-1); [Developmental Changes in the Whole Number Bias](https://files.eric.ed.gov/fulltext/ED572370.pdf)). The umbrella term. Covers the classic 1/8 + 1/8 = 2/16 — "children often add or subtract fractions by adding or subtracting both their numerators and denominators."
- **Gap thinking** — comparing the numerator–denominator difference and calling the fraction with the smaller gap larger. Documented in about 30% of Grade 10 students ([Incorrect Ways of Thinking About the Size of Fractions](https://link.springer.com/article/10.1007/s10763-022-10338-7)).
- **Larger-denominator-is-larger** — the direct natural-number transfer to comparison.
- **Part–whole fixation** — treating a fraction only as shaded parts of a shape, so improper fractions and fractions-as-quotient are unavailable ([Robertson Program, OISE](https://www.oise.utoronto.ca/robertson/blog/whole-number-bias-and-3-misconceptions-about-fractions-junior-math-2022-05-26)).

**Granularity verdict on the fractions literature: coarse to the point of being unusable alone.** "Natural number bias" is one label covering at least eight distinct traps in `Ułamki_Zwykłe.yaml` (adding denominators, multiplying across when comparing, treating a mixed number's parts independently, multiplying only the numerator when expanding...). A Deconstruction authored against "natural number bias" would be useless — it has no steps.

This is the clearest evidence in the survey that the academic granularity is **too coarse for our purpose**, in the same way Brown & Burton is too fine.

---

## 7. DfE / NCETM

- NCETM's [Curriculum Prioritisation / ready-to-progress materials](https://www.ncetm.org.uk/classroom-resources/exemplification-of-ready-to-progress-criteria/) — 79 PowerPoints, one per DfE ready-to-progress criterion — organise everything by **curriculum criterion**, not by error. Misconceptions appear as prose asides inside a unit's teaching guidance (e.g. "a common misconception is that the number half always lies halfway between 2 labelled integers on a number line"), scoped to that unit.
- There is **no NCETM/DfE named misconception catalogue with stable identifiers.** I looked; the unit pages ([Y5 decimal fractions](https://www.ncetm.org.uk/classroom-resources/cp-year-5-unit-1-decimal-fractions/), [Y5 fractions](https://www.ncetm.org.uk/classroom-resources/cp-year-5-unit-8-fractions/)) list learning outcomes only, with misconception notes buried in downloadable slide decks.

**Verdict: no vocabulary to borrow, but a useful negative result.** The largest, best-funded curriculum body in the anglophone world did *not* build a cross-curriculum misconception catalogue. It filed misconceptions under curriculum units — which is where ours are today, as trap prose under Levels. If a catalogue were free, they'd have one. This is a real cost signal for #168, not a reason not to proceed — our justification is Deconstruction reuse and telemetry grouping, which NCETM has no equivalent of.

---

## 8. Polish-curriculum framing

**There is no named misconception taxonomy in Polish maths education.** I searched both the didactic literature and CKE materials. What exists instead:

- **Podstawa programowa** and the [egzamin ósmoklasisty informator](https://www.oke.waw.pl/wp-content/uploads/OKE_WARSZAWA/E8/Informatory/2025/Informator_E8_matematyka_2025_P1-1.pdf) are stated as *wymagania* (skills a student should have), never as errors.
- CKE's [zasady oceniania](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Arkusze-egzaminacyjne/2025/matematyka/OMAP-100-2505-zasady.pdf) does carry one load-bearing distinction, applied to every open-response item: **błąd rachunkowy** vs **błąd metody**. A błąd rachunkowy costs one point and lets the rest of the solution be marked consequentially; a błąd metody costs the method point.
- CKE's post-exam sprawozdania describe recurring errors in prose only ("uczniowie dodają liczniki i mianowniki"), with no identifiers or reuse across years.

**This is the most directly usable finding for us.** `błąd metody` vs `błąd rachunkowy` is *exactly* the `Misconception` vs `Wrong` split already in `CONTEXT.md`, and it is the distinction Polish teachers and students already have language for. Two consequences:

1. The `Misconception` / `Wrong` boundary in `CONTEXT.md` is not an invention — it is the national marking scheme's own boundary. Cite it there.
2. **Misconception names should be written in Polish**, in the register of the existing trap prose, and the catalogue should not import English research labels as identities. "Whole number thinking" has no Polish currency; "dodaje mianowniki" does. The English literature gives us the *shape* of a catalogue, not its words.

---

## 9. OPINION: granularity

**The question #168 needs answered: how coarse or fine do the standard taxonomies group these errors? Answer: they disagree by an order of magnitude, and the disagreement is fully explained by what each taxonomy was built to do.**

| Taxonomy | Scope | Named items | Purpose |
|---|---|---|---|
| Brown & Burton | multidigit subtraction | ~100 bugs | machine diagnosis |
| Ashlock | one operation × one number domain | ~10–20 patterns each | teacher diagnosis |
| Stacey & Steinle | comparing two decimals | 4 coarse / 12 fine / ~9 ways of thinking | research classification + teaching |
| Resnick et al. | comparing two decimals | 3 rules | explaining conceptual origin |
| Fractions cognitive lit. | all of fractions | ~4 umbrella biases | explaining conceptual origin |

**The rule that falls out: granularity tracks what you do with the label, not how the mathematics decomposes.** Taxonomies built to *diagnose* go fine (Brown & Burton, Ashlock). Taxonomies built to *explain* go coarse (Resnick, natural number bias). Only Stacey & Steinle does both, and it solves the conflict by being **explicitly two-tiered** — a coarse behavioural family over a finer named way of thinking.

We are a *do* taxonomy, not an *explain* one: a Misconception has to be specific enough that someone can author a Deconstruction against it — a sequence of steps derived from `Problem parameters`. That is a much harder constraint than any of these taxonomies faced, and it binds the answer.

### Recommendation

1. **Aim coarser than the map's current 60–90 estimate. Target 35–50.** The estimate came from counting textually distinct traps (218) and dividing; but roughly 20–30 of the 227 are `Wrong`, not Misconceptions at all, and the identified duplication across Topics is heavier than the raw text suggests. Every precedent that had to *teach* against its labels — not merely name them — ended up in the tens, not the hundreds. 60–90 is Brown-&-Burton territory, and Brown & Burton never had to write a lesson.

2. **Use one flat tier of named Misconceptions, and resist a second.** Stacey & Steinle's coarse tier (L/S) exists to classify *response patterns on a fixed 30-item test* — we have no fixed test, and our Traps are already the observable layer their coarse codes describe. A coarse tier would earn its place only if telemetry wanted to roll up ("this Student is a longer-is-larger thinker across all Topics"), and that's speculative. Note it as a possible later addition, do not build it now. This is consistent with the map's standing "no new abstractions justified by taste".

3. **Set the granularity test explicitly, as an authorability test, not a mathematical one.** A candidate is one Misconception if **a single Deconstruction step sequence would fix it for every Trap that references it**. If two Traps would need different walkthroughs, they are different Misconceptions — even if the literature would call them one bias. If they'd take the same walkthrough with different numbers, they are one Misconception — even if they sit in different Topics or different Chapters. This is the operational form of "granularity tracks purpose", and it is what makes the retrofit decidable per-Trap rather than a matter of taste.

4. **Expect the test to cut against the fractions literature and with Ashlock's fineness, in one specific place.** "Natural number bias" splits into many Misconceptions under this test, because "adds denominators when adding" and "multiplies only the numerator when expanding" need different walkthroughs. But it should *not* split by Topic where the walkthrough is shared: "operated on only one part of the fraction" covers rozszerzanie, skracanie, and sprowadzanie do wspólnego mianownika with one step sequence, and should be one Misconception across all three — the opposite of Ashlock's operation-scoped filing.

5. **Name in Polish, in the student's voice, as a rule they are following.** Follow Resnick and Stacey & Steinle's register (a named rule / way of thinking), not Ashlock's opaque identifiers. `dodaje_mianowniki`, `mnozy_tylko_licznik`, `przecinek_w_zla_strone`, `dluzszy_znaczy_wiekszy`. Slug identifiers in code; Polish prose label for anything a human reads. The existing trap prose is already written this way — most names can be lifted from it.

6. **Hold `Wrong` firm as a category and use it early.** Both Stacey & Steinle ("unclassified", 11–12% of students at every year level) and CKE (`błąd rachunkowy`) keep an explicit not-a-misconception bucket. Sweeping the ~20–30 category-3 traps into `Wrong` *before* clustering will make the remaining clustering much cleaner, and is the cheapest single thing #168 can do first.

### What this does not settle

- Whether a Trap may reference **more than one** Misconception. Stacey & Steinle's fine codes explicitly map to "one or two ways of thinking", so the precedent permits it. Our trap prose is one-per-slot, so we can defer — but the retrofit will surface traps that genuinely blend two errors, and #168 should decide the cardinality before it starts, not during.
- Whether Misconceptions are **Chapter-scoped or global**. The mixed fractions/decimals Levels at the end of `Ułamki_Dziesiętne.yaml` (`"Gdy masz zmieszane ułamki zwykłe i dziesiętne..."`) are evidence for global, and Resnick's whole-number/fraction interference framing says the two Chapters' misconceptions genuinely interact. Recommend global, but it is #168's call.

---

## Sources

- [Brown & Burton, Diagnostic Models for Procedural Bugs in Basic Mathematical Skills (1978)](https://onlinelibrary.wiley.com/doi/pdf/10.1207/s15516709cog0202_4)
- [Brown & VanLehn, Repair Theory: A Generative Theory of Bugs in Procedural Skills (1980)](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog0404_3)
- [Ashlock, Error Patterns in Computation (10th ed.)](https://www.pearson.com/en-us/subject-catalog/p/Ashlock-Error-Patterns-in-Computation-Using-Error-Patterns-to-Help-Each-Student-Learn-10th-Edition/P200000000739/9780135009109) · [archive.org copy](https://archive.org/details/errorpatternsinc0000ashl)
- [PME30: When successful comparison of decimals... (review of Sackur-Grisvard & Leonard, Resnick et al.)](https://www.emis.de/proceedings/PME30/4/425.pdf)
- [Developmental changes in the comparison of decimal fractions](https://www.sciencedirect.com/science/article/abs/pii/S0959475209000711)
- [Stacey & Steinle, The incidence of misconceptions of decimal notation, Grades 5–10 (MERGA 1998)](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/backinfo/refs/merga98stst.pdf)
- [Learning Decimals Project: incidence of ways of thinking](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/tests/incidenc.htm) · [column overflow](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/cases/zecase/zeideas.htm) · [money thinking](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/cases/rocase/ro.htm) · [zero makes small](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/sources/glossary/defs/dtc-zr.htm)
- [Steinle, Changes with age in students' misconceptions of decimal numbers (thesis, 2004)](https://extranet.education.unimelb.edu.au/SME/TNMY/Decimals/Decimals/backinfo/refs/steinlethesis2004.pdf)
- [Van Hoof et al., Intuitive errors in learners' fraction understanding (Memory & Cognition)](https://link.springer.com/article/10.3758/s13421-020-01045-1)
- [Incorrect Ways of Thinking About the Size of Fractions (IJSME) — gap thinking](https://link.springer.com/article/10.1007/s10763-022-10338-7)
- [Robertson Program (OISE), Whole Number Bias and 3 Misconceptions about Fractions](https://www.oise.utoronto.ca/robertson/blog/whole-number-bias-and-3-misconceptions-about-fractions-junior-math-2022-05-26)
- [NCETM, Exemplification of ready-to-progress criteria](https://www.ncetm.org.uk/classroom-resources/exemplification-of-ready-to-progress-criteria/)
- [CKE, Zasady oceniania rozwiązań zadań — egzamin ósmoklasisty, matematyka 2025](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Arkusze-egzaminacyjne/2025/matematyka/OMAP-100-2505-zasady.pdf)
- [CKE, Sprawozdanie — egzamin ósmoklasisty, matematyka 2023](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Informacje_o_wynikach/2023/sprawozdanie/EO_matematyka_sprawozdanie_2023.pdf)

### Caveats

- Ashlock's identifier scheme (`A-W-1`) is second-hand — the book is paywalled and the Pearson sample chapter would not extract. The *organisation* (by operation and number domain, with fraction and decimal chapters) is confirmed from the publisher's and Semantic Scholar's chapter listings.
- Steinle's 12 fine codes are confirmed in count from the project materials, but I could not retrieve the full code-by-code table (`A1`, `L2`, …) from a primary source — the PDFs would not extract in this environment. The **coarse codes and the named ways of thinking are primary-sourced** from the incidence tables, and those are the layers the recommendation rests on.
- The Polish negative result ("no named taxonomy exists") is an absence-of-evidence claim from searching CKE, podstawa programowa, and Polish didactic sources. Worth a second look by a Polish-speaking maths teacher before it is treated as settled.
