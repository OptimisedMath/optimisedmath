# Geometria: the Topic list, decided against the podstawa programowa

Research findings for [#208](https://github.com/OptimisedMath/optimisedmath/issues/208). Part of the map [#207](https://github.com/OptimisedMath/optimisedmath/issues/207). Blocks [#211](https://github.com/OptimisedMath/optimisedmath/issues/211) and [#213](https://github.com/OptimisedMath/optimisedmath/issues/213).

**Question**: which 2D plane-geometry Topics belong to a `Geometria` Chapter for klasy 4–8, and — the load-bearing half — **what must be drawn** for each, so the SVG drawing layer has a requirements list rather than a guess.

**Scope ceiling (from #207, enforced below)**: 2D plane geometry only. Solids, volume, 3D projection and coordinate geometry are excluded and appear nowhere in the Topic list. They are listed once, explicitly, in [§5 Ruled out](#5-ruled-out-and-why).

---

## 1. Sources

Primary only. Secondary summaries were used to *find* documents and then discarded.

| Ref | Document | Use |
|---|---|---|
| **PP** | [Podstawa programowa — Matematyka, szkoła podstawowa IV–VIII, rok szkolny 2025/2026](https://zpe.gov.pl/podstawa-programowa/szkola-podstawowa/matematyka) — MEN's own Zintegrowana Platforma Edukacyjna, the current consolidated text of the podstawa programowa (Rozporządzenie MEN z 14 lutego 2017 r., Dz.U. 2017 poz. 356, as amended, incl. the 2024 trim) | Decides what is *in* the curriculum, and the klasa band |
| **INF** | [CKE, *Informator o egzaminie ósmoklasisty z matematyki*](https://cke.gov.pl/images/_EGZAMIN_OSMOKLASISTY/Informatory/Informator_P1_matematyka.pdf) (part 1, 54 pp.), with the OKE Warszawa [2025 reprint](https://www.oke.waw.pl/wp-content/uploads/OKE_WARSZAWA/E8/Informatory/2025/Informator_E8_matematyka_2025_P1-1.pdf) | Decides what is actually *examined*, at what difficulty, and — critically — **which requirements CKE presents with a figure**. Every example task in the Informator cites the PP point it tests and carries its own marking scheme |
| **2024** | [Rozporządzenie MEN z 28 czerwca 2024 r., Dz.U. 2024 poz. 996](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20240000996) — the "uszczuplenie" | Checked for geometry removals |

PP section numbering used below:

- **klasy IV–VI**: VII. *Proste i odcinki* · VIII. *Kąty* · IX. *Wielokąty, koła i okręgi* · XI. *Obliczenia w geometrii* · XII. *Obliczenia praktyczne*
- **klasy VII–VIII**: VIII. *Własności figur geometrycznych na płaszczyźnie* · IX. *Wielokąty* · XIV. *Długość okręgu i pole koła* · XV. *Symetrie*

Cited as e.g. `PP IV–VI XI.3`.

### A correction worth recording

Secondary write-ups of the 2024 trim (publishers, teacher blogs) state that *oś symetrii figury* was removed from klasy IV–VI. **It was not.** The current MEN text still reads, verbatim:

> `PP IV–VI IX.5` — "zna najważniejsze własności kwadratu, prostokąta, rombu, równoległoboku i trapezu, rozpoznaje figury osiowosymetryczne i wskazuje osie symetrii figur"

What the 2024 trim did remove from IV–VI is coordinate-plane point plotting, surface area of polyhedra, and volume of prisms — all three already outside our ceiling. **The 2024 trim costs the Geometria Chapter nothing.** Do not plan around the blog version.

---

## 2. The Topic list

22 Topics. Granularity matches `backend/data/Ułamki_Zwykłe.yaml` (14 Topics, each one skill, 2–5 Levels of increasing difficulty). IDs follow the existing step-of-10 convention. Level sketches are indicative, not decided — #207 leaves Level design to the vertical-slice ticket.

| ID | Topic | Klasa | PP citation | Examined? |
|---|---|---|---|---|
| 10 | Proste i odcinki | 4–5 | `IV–VI VII.1–5` | rarely alone |
| 20 | Rodzaje kątów i ich mierzenie | 4 | `IV–VI VIII.1–5` | yes |
| 30 | Kąty wierzchołkowe i przyległe | 5–7 | `IV–VI VIII.6`, `VII–VIII VIII.1` | yes |
| 40 | Kąty przy prostych równoległych | 7 | `VII–VIII VIII.3` | **yes, with figure** (INF) |
| 50 | Rodzaje trójkątów | 4–5 | `IV–VI IX.1` | yes |
| 60 | Nierówność trójkąta | 5–7 | `IV–VI IX.2`, `VII–VIII VIII.5` | yes |
| 70 | Suma kątów w trójkącie | 5–6 | `IV–VI IX.3`, `IX.8`, `XI.1` | yes |
| 80 | Czworokąty — rozpoznawanie i własności | 5–6 | `IV–VI IX.4`, `IX.5` | **yes, with figure** (INF) |
| 90 | Obliczanie miar kątów w wielokątach | 6–8 | `IV–VI XI.1`, `VII–VIII IX.1` | yes |
| 100 | Obwód wielokąta | 4–6 | `IV–VI XI.2` | **yes, with figure** (INF) |
| 110 | Pole prostokąta i kwadratu | 4–5 | `IV–VI XI.3` | **yes, with figure** (INF) |
| 120 | Jednostki pola i ich zamiana | 5–6 | `IV–VI XI.4` | yes |
| 130 | Pole trójkąta | 5–6 | `IV–VI XI.3` | **yes, with figure** (INF) |
| 140 | Pole równoległoboku i rombu | 6 | `IV–VI XI.3` | yes |
| 150 | Pole trapezu | 6 | `IV–VI XI.3` | yes |
| 160 | Pola figur złożonych | 6–8 | `IV–VI XI.5` | **yes, with figure** (INF) |
| 170 | Koło i okrąg — promień, średnica, cięciwa | 5–6 | `IV–VI IX.6`, `IX.7` | yes |
| 180 | Długość okręgu | 7–8 | `VII–VIII XIV.1–2` | yes |
| 190 | Pole koła | 7–8 | `VII–VIII XIV.3–4` | yes |
| 200 | Twierdzenie Pitagorasa | 8 | `VII–VIII VIII.7` | yes |
| 210 | Symetria osiowa i środkowa | 5–8 | `IV–VI IX.5`, `VII–VIII XV.1–4` | yes |
| 220 | Skala — długość odcinka | 6 | `IV–VI XII.8` | yes |

**"Examined? — with figure"** marks a requirement that CKE's own Informator illustrates with a drawn figure in at least one example task. Those six are where the drawing layer is not a nice-to-have but the question itself. `PP IV–VI XI.2` — *oblicza pola: trójkąta, kwadratu, prostokąta, rombu, równoległoboku, trapezu, **przedstawionych na rysunku** oraz w sytuacjach praktycznych* — is the podstawa programowa itself mandating a diagram. That single clause is the strongest curricular justification the drawing layer has.

### Two notes on the boundary

- **`Podobieństwo` (similarity) is not in klasy 4–8.** The candidate space in #208 pairs "scale and similarity"; similarity of figures appears nowhere in the szkoła podstawowa podstawa programowa — it is liceum material. Only **scale of a segment** survives (`PP IV–VI XII.8`, and it is filed under *Obliczenia praktyczne*, not geometry). Topic 220 is therefore a one-dimensional length conversion, not a figure-scaling Topic. It is the weakest Topic on the list and is a defensible cut.
- **`Cechy przystawania trójkątów` (`PP VII–VIII VIII.4`) and geometric proof (`VIII.8`) are deliberately absent.** The answer to a congruence-criteria question is a justification, not a number or a choice among four; it does not fit the existing `build_problem_dict` contract (correct answer + traps + fillers). Recording as out of scope for the Chapter rather than for the curriculum.

---

## 3. What must be drawn — per Topic

This is the requirements list for the SVG scene schema. Read it as "the scene description must be able to express…".

### 10 · Proste i odcinki
Two or three straight lines in general position across the frame; point markers with labels (`A`, `B`, `P`); a segment distinguishable from a full line and from a ray (endpoint dots vs. arrowheads vs. extending to frame edge); **perpendicularity marked by a right-angle square**, parallelism marked by **matching arrowheads on both lines**; a dashed perpendicular dropped from a point to a line for *odległość punktu od prostej*, with its own right-angle marker and a length label.
→ *primitives*: line, ray, segment, dashed segment, point marker, point label, right-angle square, parallel-arrow tick, edge-length label.

### 20 · Rodzaje kątów i ich mierzenie
A single angle: vertex point, two rays of unequal length (so the Student cannot read the angle off ray length), an **arc between the rays** with the measure or a variable printed at the arc, drawn **accurate to its number** (#207's invariant — a 40° angle drawn at 70° is a wrong diagram). Must survive the full 1°–179° range including near-0° and near-180°, where the arc collapses and the label collides with the rays. Ostry/prosty/rozwarty classification needs the right-angle square as the special case at exactly 90°.
→ *primitives*: ray, vertex marker, **angle arc + arc label**, right-angle square, arm labels.

### 30 · Kąty wierzchołkowe i przyległe
Two lines crossing at one point, four angles around the intersection; **two to four simultaneous arcs at the same vertex at different radii** so they nest without overlapping; one arc carries a number, another an unknown `x`. Adjacent angles need the straight-line supplement to read as a straight line.
→ *adds*: **nested arcs at differing radii**, unknown-value arc label.

### 40 · Kąty przy prostych równoległych
Two parallel lines plus a transversal — **eight angles at two vertices**, of which typically two are labelled. Needs parallel arrowheads on both lines, per-vertex arc stacks, and a labelling scheme that identifies *which* of the eight is meant without ambiguity at phone width. CKE illustrates this requirement (`VII–VIII VIII.3`) with a figure.
→ *adds*: transversal geometry, arcs at two vertices in one scene, arc placement that must dodge a third line.

### 50 · Rodzaje trójkątów
Triangle from three vertex coordinates, vertices labelled `A B C`; **congruence tick marks on equal sides** (single/double), **arc ticks on equal angles**, right-angle square for a prostokątny. Must be recognisably ostrokątny / prostokątny / rozwartokątny at a glance — the rozwartokątny case forces a frame that is much wider than tall.
→ *adds*: **side tick marks**, equal-angle tick marks, non-square aspect frame.

### 60 · Nierówność trójkąta
Either three loose segments of given lengths laid out separately (a "can these close?" scene — no polygon at all), or a triangle with two sides labelled and the third as `x`. The loose-segments layout is a genuinely different scene shape: unconnected primitives with labels, no figure.
→ *adds*: free-floating labelled segments, no closed shape.

### 70 · Suma kątów w trójkącie
Triangle with **three arcs, one per interior vertex**, two carrying degree values and one `x`. Arcs must scale with the vertex angle so a 20° corner's arc stays inside the triangle and does not swallow the vertex label. Extension for `PP IV–VI IX.8`: an isosceles triangle needs the equal-side ticks *and* the equal-angle ticks together, plus an exterior-angle case where an arc sits **outside** the polygon.
→ *adds*: per-vertex arc sizing rules, exterior arc placement.

### 80 · Czworokąty — rozpoznawanie i własności
All five named quadrilaterals — kwadrat, prostokąt, romb, równoległobok, trapez — from a vertex list; **diagonals as dashed interior segments**, with their intersection marked, their equality ticked and their perpendicularity marked (the romb case). Symmetry axes drawn as dashed lines through the figure. CKE's Informator tests `IX.5` with a square-plus-diagonals figure.
→ *adds*: **interior dashed diagonals**, intersection marker, dashed symmetry axis, right-angle marker *inside* the figure.

### 90 · Obliczanie miar kątów w wielokątach
Arbitrary n-gon (up to a regular hexagon/octagon for `VII–VIII IX.1` *wielokąt foremny*) with arcs at several vertices, plus **dashed diagonals drawn as construction lines** partitioning the polygon into triangles.
→ *adds*: regular n-gon generation, construction-line styling distinct from figure edges.

### 100 · Obwód wielokąta
Polygon — including **non-convex / L-shaped** outlines, which is exactly where CKE puts the difficulty — with a length label on **every** edge, or with some edges deliberately unlabelled so the Student must infer them. Labels must sit outside the outline on the correct side and not collide at concave corners.
→ *adds*: non-convex polygon support, **outward-normal label placement**, unlabelled-edge handling.

### 110 · Pole prostokąta i kwadratu
Rectangle, two edge labels, right-angle markers optional. The cheapest scene on the whole list. Practical variants want a **dimension line** (extension lines with arrowheads offset from the figure) rather than an inline edge label.
→ *adds*: **dimension line with arrowheads and extension lines**.

### 120 · Jednostki pola i ich zamiana
Often no figure at all. Where one helps: a **square grid** subdividing a larger square into unit squares (100 cm² inside 1 dm²), with the grid at a density that stays legible.
→ *adds*: **grid / lattice fill**.

### 130 · Pole trójkąta
Triangle with a base labelled and a **height drawn as a dashed segment from the apex perpendicular to the base, carrying a right-angle marker**. Three cases the layer must handle: height inside (ostrokątny), height coinciding with a side (prostokątny), and **height falling outside the triangle onto an extension of the base** (rozwartokątny) — which needs the base drawn extended as a dotted continuation. A second, hostile case: a triangle whose *given* dimensions pair a base with the height to a *different* base, the entire point of `confuses_base_with_the_wrong_height`.
→ *adds*: **altitude (dashed, with right-angle marker)**, **base extension line**, multiple labelled heights in one figure.

### 140 · Pole równoległoboku i rombu
Parallelogram with base, slant side, and a dashed height that is **shorter than the slant side** and visibly so — the whole misconception (`multiplies_the_two_sides_of_a_parallelogram`) dies if the height is drawn near-equal to the side. Romb additionally wants both diagonals dashed with their perpendicular intersection marked, for the `d₁·d₂/2` formula.
→ *adds*: nothing new beyond 130 + 80, but demands **adversarial extremes**: a very slanted parallelogram where the height is obviously not the side.

### 150 · Pole trapezu
Trapezoid with **two parallel bases marked as parallel** (arrowheads), a dashed height between them, and both base lengths labelled. Needs to look like a trapezoid and not an accidental parallelogram; needs to work for the trapez prostokątny (one leg is the height) and the trapez równoramienny (leg ticks). Legibility at phone width is worst here — four labels, two arrows, one dashed height, in a shape that is wide and short.
→ *adds*: parallel-marking on interior edges; the tightest label-collision budget on the list.

### 160 · Pola figur złożonych
An arbitrary rectilinear outline (L, T, plus-shape, or rectangle-minus-rectangle), a **shaded or hatched region** distinguishing "the part you want" from the whole, and **dashed decomposition lines** showing the split into rectangles. Also the circle case: a shaded annulus, or a square with a circle cut out.
→ *adds*: **region fill / hatch**, boolean-ish outlines (shape minus shape), decomposition guides.

### 170 · Koło i okrąg
Circle with a centre dot labelled `O`, a **radius segment** to a labelled point on the circumference, a **diameter** through the centre, and a **chord** between two circumference points — any subset, labelled. Must distinguish *okrąg* (outline) from *koło* (filled), which is a fill toggle carrying real semantics.
→ *primitives*: **circle (stroked and filled variants)**, centre marker, radius/diameter/chord segments, point-on-circle marker.

### 180 · Długość okręgu
Circle plus one radius or diameter labelled. Optionally the circumference emphasised as a distinct stroke, or a **circular arc** for part-circle perimeters.
→ *adds*: **arc as a path** (already needed for angle arcs — same primitive, different radius).

### 190 · Pole koła
Filled circle with radius labelled; annulus (two concentric circles, ring shaded); circular sector (a shaded pie slice with its central angle arc labelled) — the sector is where the angle-arc primitive and the region-fill primitive have to co-operate.
→ *adds*: concentric circles, **shaded sector**, sector central-angle arc.

### 200 · Twierdzenie Pitagorasa
Right triangle with the **right-angle square** mandatory and correctly placed, two of three sides labelled, the unknown as `x`. Applied contexts (`w sytuacjach praktycznych`): a ladder against a wall, a rectangle with its diagonal dashed, a rhombus split by its diagonals — all of which reduce to a triangle plus a dashed segment plus a right-angle marker.
→ *adds*: nothing new; it is the **consumer** of markers 10/50/80 already require.

### 210 · Symetria osiowa i środkowa
A figure, a **dashed axis line** (vertical, horizontal, and — the hard case — diagonal), and its mirror image, usually on a **square grid** so the reflection is countable. Środkowa needs a labelled centre point and a figure rotated 180° about it. Also "complete the figure so it is symmetric": half a figure drawn, half absent.
→ *adds*: **grid background**, mirror axis styling, a transformed copy of a figure in one scene, partial figures.

### 220 · Skala — długość odcinka
A labelled segment with a stated scale, or a simple plan (rectangle) with dimensions "in the drawing" and a scale note. Weakest drawing demand; a **scale bar** is the only new element.
→ *adds*: scale bar / caption.

---

## 4. The primitive set this implies

Deduplicating §3 into what the scene schema must be able to describe:

**Geometry**
1. `point` — dot marker, optional label, label anchor side
2. `segment` / `ray` / `line` — solid, dashed, dotted; endpoint styles
3. `polygon` — vertex list; convex and **non-convex**; stroked or filled
4. `circle` — stroked (*okrąg*) or filled (*koło*); centre marker
5. `arc` — one primitive serving both angle arcs and circle arcs/sectors

**Annotation**
6. `vertex-label` — `A B C O`, placed by outward normal
7. `edge-label` — length + unit, on-edge or offset, outward side
8. `angle-arc-label` — degree value or unknown, at a chosen arc radius (nesting)
9. `right-angle-square`
10. `tick-mark` — single/double/triple, on edges (equal lengths) and on arcs (equal angles)
11. `parallel-arrow` — matching arrowheads for parallel edges
12. `dimension-line` — extension lines + arrowheads + label, offset from the figure

**Region and background**
13. `fill` / `hatch` — a shaded region, incl. shape-minus-shape and sector
14. `grid` — square lattice background, variable density
15. `scale-bar` / free caption

Fifteen primitives. Every one of them is demanded by at least two Topics; none is purpose-built for a single figure, which is the test #207 sets ("per-figure helpers do not survive the second figure type").

**Three cross-cutting rules the schema must carry, not the generators:**

- **Outward-normal label placement.** Roughly every Topic needs "put this label outside the shape, on this edge's far side". If each generator computes it, the accuracy bugs #207 predicts will live in 22 places.
- **Arc radius allocation.** Nested arcs at one vertex (Topic 30, 40) and arcs sized against a narrow vertex angle (Topic 70) are the same problem: the scene, not the generator, should assign radii.
- **Aspect-ratio and viewBox derivation.** `generate_universal_number_line` hardcodes 4000×900. A rozwartokątny triangle, a wide trapez and a circle need three different frames; the frame must be derived from the scene's bounding box.

---

## 5. Ruled out, and why

Confirmed present in the podstawa programowa and deliberately **excluded** by #207's ceiling — recorded so a later reader does not think they were missed:

- `PP IV–VI X. Bryły`, `PP IV–VI XI.6–7` (objętość i pole powierzchni prostopadłościanu), `PP VII–VIII XI. Geometria przestrzenna` — solids and volume. CKE examines these heavily; they need projection drawing.
- `PP IV–VI X` / `PP VII–VIII X. Oś liczbowa. Układ współrzędnych na płaszczyźnie` — coordinate geometry.
- `PP VII–VIII VIII.4` (cechy przystawania) and `VIII.8` (dowody geometryczne) — free-form justification, no fit with the current answer contract.
- `Podobieństwo figur` — **not in the klasy 4–8 podstawa programowa at all**.

---

## 6. Which Topics stress the drawing layer hardest

**Hardest — build these last, and treat them as the schema's stress tests:**

1. **160 · Pola figur złożonych** — the only Topic needing arbitrary outlines *and* region fill *and* decomposition guides. Shape-minus-shape (a square with a circle removed) is the single most demanding thing on the list; it is also the Topic CKE loves most.
2. **210 · Symetria** — the only Topic needing a grid background *and* a transformed copy of a figure in one scene *and* partial figures. A diagonal axis is much worse than a vertical one.
3. **40 · Kąty przy prostych równoległych** — eight angles, two vertices, one transversal, and arcs that must not collide with a third line. Pure label-collision pain.
4. **150 · Pole trapezu** — not conceptually hard; the worst legibility budget on the list. Four labels, two parallel markers and a dashed height in a wide, short shape at phone width. If the trapez survives the adversarial gallery, most things will.
5. **130/140 · Pole trójkąta / równoległoboku** — the **altitude outside the figure** case (rozwartokątny) and the base-extension dotted line are the geometry the layer will get wrong first, and they are precisely the cases that carry the best misconceptions.

**Authorable with the fewest primitives — the natural vertical-slice candidates:**

- **110 · Pole prostokąta i kwadratu** — `polygon` + `edge-label`. Two primitives. Zero risk.
- **100 · Obwód wielokąta** — `polygon` + `edge-label`, with non-convexity as the only extra.
- **170 · Koło i okrąg** — `circle` + `point` + `segment` + labels. Four primitives, no arithmetic in the placement.
- **70 · Suma kątów w trójkącie** — `polygon` + three `arc`s + labels. Cheap *and* it forces the arc primitive, which nothing else cheap does.

**Recommendation for #207's vertical slice: Topic 130 · Pole trójkąta.** It is the sweet spot: cheap enough to build (polygon, edge label, dashed altitude, right-angle marker — 5 primitives), but it exercises the two things that will actually break — the dashed altitude with its right-angle marker, and the outside-the-figure extreme. It is explicitly named in `PP IV–VI XI.3` *with* the "przedstawionych na rysunku" clause, CKE illustrates it, it needs units (`cm²`, the map's sharpest ticket), and it carries `confuses_length_with_area` and `confuses_base_with_the_wrong_height` — two genuinely diagnostic misconceptions. **110 · Pole prostokąta** is the fallback if the layer needs to prove itself on something with no dashed lines at all, but it will not stress anything.

---

## 7. Surprises

- **The podstawa programowa mandates the diagram.** `PP IV–VI XI.3` says areas "**przedstawionych na rysunku**". The drawing layer is not an enhancement of the Chapter; a Geometria Chapter without one is not teaching the requirement as written.
- **Similarity is not in the curriculum.** The candidate space in #208 lists "scale and similarity" together; only a 1-D scale-of-a-segment point exists, and it is filed under *Obliczenia praktyczne*, not geometry.
- **The 2024 trim costs Geometria nothing.** Everything it removed was already outside the 2D ceiling — and the widely repeated claim that it removed *osie symetrii* from klasy IV–VI is false against MEN's own current text.
- **Circle area and circumference are a full two years later than the polygon areas** (klasa 7–8 vs. 5–6). They read as one Chapter but sit at opposite ends of the Student's progression; Chapter ordering should reflect that.
- **The angle arc is a circle arc.** Topics 20/30/40/70 and 180/190 want the same primitive at different radii. Collapsing them is free and stops the layer growing two arc implementations.
