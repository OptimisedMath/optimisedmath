# Geometria: figure notation conventions, and where the app breaks them

Research findings for [#281](https://github.com/OptimisedMath/optimisedmath/issues/281). Part of the map [#207](https://github.com/OptimisedMath/optimisedmath/issues/207). Companion to [0003](0003-geometria-topic-list-podstawa-programowa.md), which decided *what* to draw; this decides *how to mark it up*.

**Question**: how does a Polish klasa 4–8 figure mark itself up — vertices, sides, unknowns, heights, right angles, equalities, circles — and which of those does the drawing layer currently get wrong?

**Headline**: the app's right-angle marker is the English one, not the Polish one; its circle-centre letter is the Polish symbol for *obwód*; and its `x` for an unknown does not appear on a single CKE figure in six documents.

---

## 1. Sources

Primary only. Everything below is either MEN's own text, a CKE document, or a figure read off a CKE exam paper page by eye. Secondary write-ups appear once, flagged, and only where a primary source is silent.

| Ref | Document | Use |
|---|---|---|
| **ZPE** | MEN's [Zintegrowana Platforma Edukacyjna](https://zpe.gov.pl), e-materials [*Rodzaje kątów*](https://zpe.gov.pl/a/rodzaje-katow/D18ElkF5J), [*Kąty i ich rodzaje*](https://zpe.gov.pl/a/katy-i-ich-rodzaje/DUMe8Id18), [*Trójkąty i ich własności*](https://zpe.gov.pl/a/trojkaty-i-ich-wlasnosci/Dp4OWTyJp), [*Pole trójkąta*](https://zpe.gov.pl/a/pole-trojkata/D1011a4cs), [*Obliczanie pól i obwodów trójkątów*](https://zpe.gov.pl/a/obliczanie-pol-i-obwodow-trojkatow/DiCZQs27f), [*Długość okręgu*](https://zpe.gov.pl/a/dlugosc-okregu/DmQwgAlcy) | The ministry's own teaching text. Says the conventions out loud, which exam papers never do |
| **INF** | CKE, [*Informator o egzaminie ósmoklasisty z matematyki*](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Informatory/Informator_P1_matematyka.pdf) (54 pp.) and the [2025 edition](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Informatory/2025/standard/Informator_E8_matematyka_2025_P1.pdf) (68 pp.) | Task statements *and* CKE's own worked solutions — the only place CKE writes maths in prose rather than drawing it |
| **E8-21** | CKE, [egzamin ósmoklasisty 2021, arkusz `OMAP-900-2105`](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Arkusze-egzaminacyjne/2021/matematyka/OMAP-900-2105.pdf) | Figures |
| **E8-22** | CKE, [2022, `OMAP-100-2205`](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Arkusze-egzaminacyjne/2022/matematyka/OMAP-100-2205.pdf) | Figures |
| **E8-23** | CKE, [2023, `OMAP-900-2305`](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Arkusze-egzaminacyjne/2023/matematyka/OMAP-900-2305.pdf) | Figures — the richest source here |
| **E8-24** | CKE, [2024, `OMAP-800-2405`](https://www.oke.poznan.pl/files/cms/830/omap_800_2405.pdf) | Figures |

**Method note, because it changes how much the negative results are worth.** CKE figures are vector drawings whose label glyphs are sometimes extractable text (E8-21) and sometimes not (E8-23, E8-24). Every claim below about what a figure *shows* was made by rendering the page and looking at it, not by grepping. Claims about what a corpus *never contains* are grep results over extracted text and are stated as such.

**The publisher gap, stated up front.** The ticket asks for GWO *Matematyka z plusem*, Nowa Era *Matematyka z kluczem* and WSiP house style. GWO publishes its klasa 5 textbook only as a paginated flipbook viewer (`flipbook.apps.gwo.pl/display/3162`) that serves no page text or images to a fetcher; Nowa Era and WSiP samples behave the same. **No publisher house style below is sourced to a publisher.** Where a convention is marked *publisher-variable*, that is a gap in this research, not a finding about publishers.

---

## 2. The conventions

Each row: what the convention is, its source, and how firm it is.

### 2.1 Right-angle marker — **łuk z kropką**, not a square

The single firmest and most consequential finding.

ZPE, *Rodzaje kątów*, verbatim:

> **„Kąt prosty oznaczamy łukiem z kropką w środku."**

Every right angle in every CKE figure examined is drawn this way: a quarter-arc across the corner with a dot at its centre. Never a square. Confirmed in four independent figures:

- **E8-21 Zadanie 19** (p. 18) — two arc-with-dot markers in one triangle
- **E8-23 Zadanie 12** (p. 26) — two, at the feet of two heights
- **E8-23 Zadanie 14** (p. 30) — two, at the feet of a triangle's and a parallelogram's height
- **E8-24 Zadanie 14** (p. 10) — one, at the foot of the height *AD*

The dot is literally a `.` glyph placed inside the arc: E8-21's page text extracts as `D`, `.`, `.`, `α`, `138°` — the two dots are the two right-angle markers.

*Secondary corroboration that this is a language convention rather than a CKE quirk*: [pl.wikipedia, *Kąt prosty*](https://pl.wikipedia.org/wiki/K%C4%85t_prosty) — „W polskojęzycznej literaturze matematycznej kąt prosty oznacza się zwykle kropką, w literaturze anglojęzycznej stosuje się oznaczenie kwadracikiem". Flagged as secondary; the four CKE figures and the ZPE sentence carry the claim on their own.

**Firmness: settled.** MEN states it in words; CKE draws it 7 times out of 7. No Polish klasy 4–8 source using the square was found.

### 2.2 Unknown angles — `α`, `β`, `γ`; never `x`

The ticket's assumption, confirmed, and confirmed *on the figure* rather than only in prose.

- **E8-24 Zadanie 14** (p. 10): „Literami  α  i  β  oznaczono dwa inne kąty." The figure carries italic `α` and `β` inside arcs at two vertices; the given angle carries `20°`. The follow-up prose reads „Kąt  α,  zaznaczony na rysunku, ma miarę ________ ."
- **E8-23 Zadanie 10** (p. 22): the trapezoid's unknown base angle is `α`; the given is `20°`.
- **E8-21 Zadanie 19** (p. 18): unknown `α`, given `138°`.
- ZPE, *Trójkąty i ich własności*: vertices `A, B, C`; sides `AC, CB, AB`; angles `α, β, γ`.
- ZPE, *Kąty i ich rodzaje*: uses `α, β, γ, δ`.

`x` as an angle label appears **zero times** across all six CKE documents.

**Firmness: settled.** `α β γ (δ)` in figure order, italic.

### 2.3 Unknown lengths — a lettered dimension, **not `x`**

This is where the ticket's own scope list left the question open, and the answer overturns the app's default.

**E8-23 Zadanie 14** (p. 30) is the decisive figure: a triangle labelled `10 cm` (base) and `12 cm` (height) beside a parallelogram labelled `5 cm` (height) and — for the unknown base — **`a`**, italic lowercase. The question reads „Ile jest równa długość boku  *a*  równoległoboku?"

Across all six documents, `x` occurs as a length only inside CKE's *own worked solutions*, where a solver introduces it: „Jeśli długość boku małego kwadratu oznaczymy przez x, to duży kwadrat ma bok długości 3x" (INF, *Zasady oceniania*). It is an algebra variable a student may invent, never a label CKE prints on a drawing.

**Firmness: strong.** One direct figure plus a clean negative across six documents. A second figure printing a different letter would make it settled; none was found, because CKE geometry tasks mostly ask for a number rather than name an unknown.

### 2.4 Height — `h`, subscripted by the vertex when there are two

- ZPE, *Pole trójkąta*: „Pole trójkąta jest równe połowie iloczynu długości jego podstawy oraz wysokości poprowadzonej do tej podstawy", written `P = a·h/2`, with **`P` = pole, `a` = podstawa, `h` = wysokość**. „Podstawą trójkąta nazywamy ten bok trójkąta, do którego poprowadzona jest wysokość."
- ZPE, *Obliczanie pól i obwodów trójkątów*: sides `a, b, c`; heights `h, h₁, h₂, h₃`; **`O` = obwód**.
- **E8-23 Zadanie 10**: a single height on a trapezoid, labelled `h`.
- **E8-23 Zadanie 12**: two heights in one figure, labelled **`h_D`** and **`h_B`** — subscripted by the vertex they are dropped from. Prose: „Wysokość  *h_D*  trójkąta  *ACD*  poprowadzona z wierzchołka  *D*  do prostej  *AC*  jest równa  2 cm".
- **E8-24 Zadanie 14**: a height named by its endpoints instead — „poprowadzono wysokość *AD*".

**Firmness: settled for the letter `h`.** The vertex subscript `h_B` is CKE's device for disambiguating two heights and is well evidenced but appears in one paper.

### 2.5 Height — drawn **solid**, not necessarily dashed

**This overturns [0003](0003-geometria-topic-list-podstawa-programowa.md) §3 (Topic 130) and the ticket's own phrasing.** 0003 wrote the altitude into the requirements list as „a **height drawn as a dashed segment**". CKE draws it both ways:

| Figure | Height drawn |
|---|---|
| E8-23 Zadanie 14 — triangle, height inside | **solid** |
| E8-23 Zadanie 14 — parallelogram, height inside | **solid** |
| E8-24 Zadanie 14 — height *AD* inside an isosceles triangle | **solid** |
| E8-23 Zadanie 12 — `h_D`, `h_B` added to an existing quadrilateral | dashed |

The pattern that fits all four: a segment that is **part of the figure as posed** is solid; a segment **the task adds on top of a figure already drawn** is dashed. 3 of 4 are solid, and the two that match the app's Topic 130 shape most closely (a triangle with base and height, height inside) are both solid.

**Firmness: the dashed height is *not* a convention.** Solid is at least as correct and is what CKE uses for the exact figure Topic 130 draws.

### 2.6 Vertex naming — italic capitals, anticlockwise, and **not always starting at `A`**

- ZPE, *Trójkąty i ich własności*: „A, B, C – wierzchołki trójkąta".
- Every CKE figure examined labels vertices with **italic** capitals placed outside the figure along the outward direction.
- The walk is **anticlockwise** in all three lettered CKE figures examined (E8-21 `ABC` with `A` bottom-left, `B` bottom-right, `C` apex; E8-23 Zadanie 12 `ABCD`; E8-24 `ABC`).
- **E8-22 Zadanie 15** poses „trapez  *KLMN*". Vertex letters are a contiguous run of capitals, not necessarily `A`-first.

**Firmness: anticlockwise is consistent (3/3) but never stated by a source** — treat as strong house practice, not a rule. Italic capitals: settled. Non-`A` starts: settled, single example, unambiguous.

### 2.7 Side lettering — `a, b, c` exists; **"a is opposite A" could not be established**

ZPE's area/perimeter material uses `a, b, c` for a triangle's sides. But no MEN or CKE klasy 4–8 source examined states, or draws, the rule that `a` is the side *opposite vertex A*. ZPE's *Trójkąty i ich własności* names sides by their endpoints instead — „AC, CB, AB – boki trójkąta" — and CKE's `a` in E8-23 Zadanie 14 sits on a figure with no vertex letters at all.

**This is a scope item the ticket asked for and this research could not settle from primary sources.** The opposite-vertex rule is genuinely standard in Polish *liceum* trigonometry, and secondary klasy 4–8 sites assert it, but it has no klasy 4–8 primary warrant here. The practical consequence is small: klasy 4–8 figures print `a` next to the side it names, so the reader never has to know the rule.

### 2.8 Angle naming in prose — `kąt ABC` in tasks, `|∢ABC|` only in solutions

- Task statements say it in words: „kąt *BCA* ma miarę 35°" (E8-22 Zadanie 13), „Jaką miarę ma kąt  α  w tym trapezie?" (E8-23), „kąt ABC" / „kąta AED" (INF, throughout).
- CKE's **worked solutions** use `|∢ABC|` — the symbol wrapped in bars because it denotes the *measure*: `|∢APB| = 27° + 63° = 90°`. 12 occurrences in each Informator, all inside *Zasady oceniania* / *Rozwiązanie*.
- The symbol is **`∢` (U+2222)**, not `∡` (U+2221). `∡` occurs **zero times** in all six documents. The ticket guessed `∡ABC`; that is the wrong codepoint.
- ZPE also uses `∡`-style prose sparingly and prefers „kąt ABC".

**Firmness: settled.** Student-facing prose: `kąt ABC` or `kąt α`. Never print `|∢ABC|` in a question — CKE reserves it for the marking scheme.

### 2.9 `∥` and `⊥` do not appear at all

Zero occurrences of `∥`, `‖`, `∦` or `⊥` across all six CKE documents. Parallelism and perpendicularity are stated in Polish words — „prostą c prostopadłą do a i b" (INF) — or drawn.

**Firmness: settled as a negative for klasy 4–8 CKE prose.** Do not put `AB ∥ CD` in a question.

### 2.10 Equal sides and equal angles — CKE says it in words, not with ticks

**E8-24 Zadanie 14** poses „W trójkącie równoramiennym *ABC* o podstawie *AB*" and the figure carries **no tick marks on the equal sides**. The equality is in the sentence. No tick-marked or double-arced figure was found in any of the six documents.

**Firmness: the tick convention could not be confirmed from primary Polish sources, and one counter-example exists.** Ticks are near-universal internationally and almost certainly appear in Polish textbooks; nothing here proves it, and CKE demonstrably does not rely on them. Marked **publisher-variable** — and see §1's publisher gap.

### 2.11 Parallel arrows — no primary evidence either way

**E8-23 Zadanie 10** draws a trapezoid whose two parallel bases carry **no arrow marks**. That is the only trapezoid figure available. Same verdict as §2.10: **not established**, one counter-example, publisher-variable.

### 2.12 Circle notation — the centre is **`S`**, not `O`

The second overturned assumption. The ticket's scope list says „`O` for the centre"; CKE says `S`, for *środek*.

- INF 2025, Zadanie 22: „Na okręgu o środku w punkcie  *S*  zaznaczono punkty  *A*, *B*, *C*, *D*…"
- INF 2025, Zadanie 37: „Na okręgu o środku  *S*  i promieniu  *r* = 10 cm  zaznaczono punkty  *A*  i  *B*…"
- ZPE, *Długość okręgu* and the *Okrąg i koło* e-materials likewise speak of „koło o środku S i promieniu r".

`r` for promień is confirmed directly (`r = 10 cm`). `d` for średnica was **not** found in any CKE text examined — CKE writes „średnica" in words and gives its length. PP `IV–VI IX.6–7` is quoted in INF 2025 as „wskazuje na rysunku cięciwę, średnicę oraz promień koła i okręgu", with no letters.

**Why `O` is actively wrong and not merely unusual**: ZPE's *Obliczanie pól i obwodów trójkątów* uses **`O` for obwód** alongside `P` for pole. A figure that labels a circle's centre `O` next to a task asking for the *obwód* collides with the one letter the Student has already been taught means something else.

The liceum form `o(O, r)` for "the circle with centre O and radius r" was found **nowhere** in klasy 4–8 material and should not be used.

**Firmness: settled for `S` and `r`. `d` for średnica: not established.**

### 2.13 Units and the decimal comma in labels — nothing differs

- Edge labels are `«liczba»␣«jednostka»`: `10 cm`, `12 cm`, `5 cm`, `8 cm`, `3 cm` (E8-23 Zad. 14, E8-24 Zad. 12).
- Areas use a true superscript: `40 cm²`, `48 cm²`.
- No decimal value appeared on any figure label examined — every CKE figure dimension was a whole number. The comma separator is settled elsewhere in the app and nothing here contradicts it, but **figure labels supply no positive evidence for it either**.
- Degree labels are `20°`, `138°` — no space before `°`.

### 2.14 Colour

Every CKE figure is **monochrome black line on white**, with light grey area fill where a region needs distinguishing (E8-24 Zadanie 12, a shaded pentagon). No hatching, no accent colour, in any figure examined.

**Firmness: settled for CKE.** Textbooks are demonstrably colourful, so this is an exam-paper convention, not a Polish one. Recorded because the app's accent red is a deliberate departure and should stay a deliberate one.

---

## 3. Where the app departs

**Read this first.** The scene layer landed by [#214](https://github.com/OptimisedMath/optimisedmath/issues/214) is **not on `main`** — `backend/core/scene/` on `main` contains only stale `__pycache__`. Every line reference below is against commit `f2d312b` on branch `geometria/vertical-slice`. A reader on `main` will find no such files.

### Wrong against a settled convention

| # | Where | What it does | What the source says |
|---|---|---|---|
| **D1** | `backend/core/scene/render.py:467–482` (`RightAngle`) | Draws an open **square**: `ctx.path([v+u1, v+u1+u2, v+u2])` | §2.1 — Polish is `łuk z kropką`. This is the English marker |
| **D2** | `backend/core/scene/render.py:584–592` (`Altitude`, the foot marker) | The same square, a second implementation, in `ACCENT` | §2.1. This is the one a Student sees on **every Topic 130 figure** — `topic_130_pole_trojkata.py:237`, `:317`, `:362` |
| **D3** | `backend/core/scene/render.py:722` (`Centre`) | `label: str = "O"` | §2.12 — CKE uses `S`; `O` is *obwód* |
| **D4** | `backend/core/scene/render.py:400`, `:441`, `:749`, `:599` | `x` is the default and, for `Altitude` and `Radius`, the **only** unknown text — both hardcode the literal `"x"` with no override | §2.2 (angles: `α β γ`) and §2.3 (lengths: a lettered dimension). `AngleArc(unknown=True)` renders `x` where CKE renders `α`; `Altitude(unknown=True)` renders `x` where CKE renders `h` |
| **D5** | `backend/chapters/geometria/topic_130_pole_trojkata.py:368–371` | The klasa 5–6 prompt is `\text{Pole trójkąta wynosi } {area}\ \text{cm}^2\text{. Oblicz } x \text{.}` | §2.3. The figure's unknown should carry the letter the question names — `h` when the height is withheld (`height_unknown`), `a` when the base is. As written, one prompt string serves both cases and names neither |

### Wrong against a strong-but-not-settled convention

| # | Where | What it does | What the source says |
|---|---|---|---|
| **D6** | `backend/core/scene/render.py:577` (`Altitude`) | The height is **always** dashed; there is no solid option | §2.5 — CKE draws an interior height **solid** in 3 of 4 figures, including both figures that match Topic 130's shape exactly. `Altitude` needs a `dash: bool = False` and the rozwartokątny rung (`topic_130:317`) is the one case that keeps the dash |
| **D7** | `backend/core/scene/geometry.py:18` | `_NAMES = "ABCDEFGHIJKL"`, assigned in `polygon()` at `:137` with no override | §2.6 — CKE poses „trapez *KLMN*". A figure can never be lettered other than from `A` |
| **D8** | `backend/core/scene/render.py:594–603` (`Altitude`'s label) | Pushes the height's label **outward**, away from the centroid | §2.5 figures place `12 cm` and `5 cm` **inside** the figure, beside the height. Outward placement on an interior height puts the number in empty space away from the segment it names |

### Defensible, but record it

| # | Where | Note |
|---|---|---|
| **D9** | `render.py:37–39`, and every `color=ACCENT` on `Altitude`/`AngleArc`/`Radius`/`Sector` | §2.14 — CKE is monochrome. The accent is a screen-legibility choice, not a school one. Keep it, knowing it is a departure |
| **D10** | `topic_130_pole_trojkata.py:233–236`, `:314–316` | Labels **all three sides plus the height**. CKE labels only what the task needs (§2.3's figure labels two of five available lengths). The extra label is deliberate — `TRAP_PERIMETER` and `TRAP_SIDE_AS_HEIGHT` have nothing to fire on without it (`topic_130:22–26`). A real departure with a real reason |
| **D11** | `topic_130_pole_trojkata.py:232`, `:275`, `:313`, `:359` | Always draws `VertexLabels()`. Both CKE triangle-area figures (§2.3, §2.13) carry **no vertex letters** — the task does not need them. Harmless, but heavier than the school form |

### Correct — confirmed, not assumed

- `geometry.py:133–143` forces every polygon **anticlockwise** (§2.6). ✓
- `render.py:46` `_fmt` emits the Polish decimal comma (§2.13). ✓
- `render.py:408` edge labels are `«value»␣«unit»` (§2.13). ✓
- `render.py:460` angle labels are `«value»°`, no space (§2.13). ✓
- `render.py:474–477` `RightAngle` refuses a vertex that is not 90° — the marker can never lie. ✓ (the *shape* is D1; the *discipline* is right)
- `render.py:109–124` `arc_radius` nests arcs at one vertex — exactly what E8-24 Zadanie 14 does with `β` outside `20°` at vertex `A`. ✓
- `geometry.py:153` `Triangle.sss` documents `a=BC, b=CA, c=AB`. Internationally standard and internally consistent; §2.7 records that it has **no klasy 4–8 primary warrant**, not that it is wrong.

### A bug found while auditing

`render.py:486–505` — `Ticks`'s docstring says „Congruence marks: on an edge for equal lengths, **on an arc for equal angles**". `render()` takes only an `edge` and draws only across an edge. **Equal-angle marking is not expressible.** [0003](0003-geometria-topic-list-podstawa-programowa.md) §3 requires it for Topics 50 and 70 („equal-side ticks *and* the equal-angle ticks together"). Either the docstring is wrong or the class is half-built; §2.10 says the missing half is the one with no primary Polish evidence behind it, so this may be the cheapest thing on the list to simply delete from the docstring.

---

## 4. Surprises

- **The right-angle square is the English convention.** MEN says `łuk z kropką` in so many words, and CKE draws the arc-and-dot 7 times out of 7 across four years. The app draws the square, twice, in two separate implementations — and one of them is on every single Topic 130 figure a Student will ever see. This is the highest-value fix in the ticket.
- **`O` for a circle centre is not merely unconventional, it is the symbol for *obwód*.** CKE and MEN both use `S` (*środek*). The ticket's scope list asserted `O`, and the app implements `O`.
- **`x` never appears on a CKE figure.** In six documents it occurs only inside CKE's own worked solutions, as a variable a solver invents. On figures, an unknown length is a lettered dimension (`a`) and an unknown angle is `α`. The app's `unknown=True` prints `x` in four places, two of which cannot be overridden.
- **The dashed height was wrong in the previous research note.** [0003](0003-geometria-topic-list-podstawa-programowa.md) specified a dashed altitude as a requirement; CKE draws an interior height **solid**, including in the two figures that are the closest possible match to Topic 130. The dash belongs to the *added construction line*, which is the rozwartokątny case — where the app is right for the wrong reason.
- **`∡` is the wrong codepoint.** CKE uses `∢` (U+2222), always inside measure bars, and only in marking schemes. Neither symbol belongs in a question a Student reads.
- **CKE marks nothing it can say in a sentence.** No equal-side ticks on an explicitly *równoramienny* triangle, no parallel arrows on an explicitly *trapez*, no `∥`, no `⊥`, no `|AB|`. The exam's house style is that the prose carries the constraints and the figure carries the numbers. That is a defensible model for question text generally, and worth weighing before adding tick marks the Student may never have seen.

## 5. What could not be established

Stated plainly, because the ticket asked for each of these:

1. **"Side `a` is opposite vertex `A`"** for klasy 4–8. `a, b, c` as side letters is sourced (ZPE); the opposite-vertex rule is not, in any MEN or CKE klasy 4–8 material examined. §2.7.
2. **Equal-side ticks and equal-angle arcs.** No Polish primary source found using them, and one CKE counter-example that states the equality in prose instead. §2.10.
3. **Parallel arrowheads.** Same, with one counter-example. §2.11.
4. **`d` for średnica.** CKE writes the word. `r` is confirmed; `d` is not. §2.12.
5. **All three publisher house styles** — GWO, Nowa Era, WSiP. Their klasa 4–8 samples are served only through flipbook viewers that expose neither text nor page images to a fetcher. Every "publisher-variable" label above is therefore an *unknown*, not a *finding*. Closing items 2, 3 and 4 almost certainly needs a physical or PDF copy of one klasa 5 textbook; that is the single highest-yield next source.
