# PROTOTYPE — Geometria scene schema

Throwaway. Built to answer [#211](https://github.com/OptimisedMath/optimisedmath/issues/211)
on the map [#207](https://github.com/OptimisedMath/optimisedmath/issues/207).
Nothing here is production code; the validated decision is recorded on the ticket.

## Run

```
python -m backend.core.scene_prototype.gallery   # writes gallery.html — open it
python -m backend.core.scene_prototype.check     # does the picture agree with the numbers?
python backend/core/scene_prototype/shoot.py dark 760 3000   # headless PNG (macOS Chrome)
python -m backend.core.scene_prototype.focus trapezu 25      # a few cases, rendered big
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
