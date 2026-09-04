# PROTOTYPE — Geometria scene schema

Throwaway. Built to answer [#211](https://github.com/OptimisedMath/optimisedmath/issues/211)
on the map [#207](https://github.com/OptimisedMath/optimisedmath/issues/207).
Nothing here is production code; the validated decision is recorded on the ticket.

## Run

```
python -m backend.core.scene_prototype.gallery       # writes gallery.html — open it
python -m backend.core.scene_prototype.adversarial   # writes adversarial.html — #212's hostile cases
python -m backend.core.scene_prototype.check         # does the picture agree with the numbers?
python -m backend.core.scene_prototype.audit_collisions  # numeric collision audit, no eyeballing
python backend/core/scene_prototype/shoot.py dark 760 3000              # headless PNG of gallery.html
python backend/core/scene_prototype/shoot.py light 390 3600 adversarial.html  # phone width
python -m backend.core.scene_prototype.focus trapezu 25      # a few gallery cases, rendered big
python -m backend.core.scene_prototype.focus_adv "1°" słowne  # a few adversarial cases, rendered big
```

## The three layers

| File | Owns |
|---|---|
| `geometry.py` | Figure constructors. Maths in, vertices out. A generator never writes a coordinate. |
| `render.py` | Annotations (symbolic — "edge AB", "vertex C") and the single SVG renderer. |
| `gallery.py` | 18 cases spanning the primitive set from #208. The code shown on each card is the code that ran. |

## What was being tested

That the to-scale invariant can be guaranteed **by construction** rather than by
validation: `trapezoid(a=12, b=6, height=4)` produces both the vertices and the
label text, so there is no second source of truth to fall out of sync. `check.py`
confirms the constructors are exact (`Triangle.angles(25, 110)` → 25/110/45 to
two decimals; hexagon area 64.952).

## Known limits, left for #212

- Collision-avoided labels can drift a long way from what they describe (see the
  two-altitudes card). Past some density the answer is a leader line, not a nudge.
- Topic 160's decomposition lines want a segment to a *derived* point, not a
  vertex. The schema cannot express that yet; nothing in the vertical slice needs it.
- The label box is estimated from character count, not measured. Fine for digits
  and `cm`; would need revisiting for long Polish words inside a figure.

## #212's adversarial findings

`adversarial.py` renders the hostile cases from the ticket (extreme aspect
ratios, extreme angles, colliding labels, long Polish words, phone width).
`audit_collisions.py` re-derives every case's label placement outside the SVG
and reports the placement algorithm's own collision cost numerically, so the
verdict doesn't depend on eyeballing a screenshot.

- **Extreme aspect ratios (1×40, 40×1 rectangles) render correctly.** The
  pen-unit-from-diagonal rule holds at a 40:1 ratio; no collisions.
- **179.4° renders correctly** — arc and label both place cleanly. There is no
  wide-angle ceiling.
- **Below ~13° the angle's own label cannot clear the vertex — a real
  collision, not a near miss.** `find_threshold.py` scanned the placement
  cost and found it crosses the algorithm's own collision threshold between
  12° and 13°. **Declared out of a generator's legal parameter range**:
  `AngleArc` now refuses (`ValueError`, mirroring `RightAngle`'s existing
  refusal on a non-90° vertex) below `MIN_LABELLED_ANGLE = 15°` in
  `render.py`. Every Geometria generator drawing a labelled angle must keep
  it at or above that floor.
- **Word labels (`wysokość`, `podstawa`, `przekątna`) never technically
  collide, at any density tested — including a dense small triangle with
  three long words at once.** The schema's viewBox derives from the content
  bounding box (Rule 3), so the canvas simply grows around whatever is
  placed; there is no fixed budget for a label to overrun internally. This
  confirms the *existing* known limit (drift, not collision) rather than
  finding a new one, and it does **not** resolve the map's still-open
  question of whether a to-scale figure survives the app's actual (fixed)
  image slot — a self-sizing SVG has nothing to test that against, so that
  question stays in `## Not yet specified` on the map, not answered here.
- **Phone-width cards (16×3 rectangle with `DimensionLine`s; word-label
  triangle) both scale cleanly with no clipping** — same reason: the SVG
  scales as one unit (`width="100%" height="auto"`), so container width
  never separates the geometry from its own labels. Same caveat as above:
  this shows the *schema* is width-agnostic, not that the real app's image
  slot renders a small figure legibly.
- Multi-digit/decimal labels (`12,5 cm`), a near-equilateral triangle's three
  tight edge labels, a 20:1 trapezoid, a very obtuse (178°) triangle with the
  altitude foot off the base, and a small-radius circle with a decimal
  radius label all render without collision. The 20:1 trapezoid's two short
  vertex labels (`D`, `C`) sit close together but stay clear — worth a second
  look if a real Topic ever needs a base ratio that extreme, but not a break.
- Polish diacritics (`ą ę ó ł`) render correctly in this gallery, which
  declares `<meta charset="utf-8">` like the fix already applied to
  `gallery.html` — #211's mojibake finding was the harness page, not the
  fragment, and stays fixed.
