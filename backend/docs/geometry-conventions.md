# Geometry conventions

How a generator writes geometry for klasy 4–8 — in its question prose and in the choices it makes around a figure. The scene (`core/scene/`) already enforces every convention it can make unwriteable: the right-angle marker, solid versus dashed heights, `S` for a circle's centre, and the fixed unknown symbols. This page holds only what an author chooses. Why the split: [ADR-0011](../../docs/adr/0011-geometry-conventions-split-between-scene-and-doc.md). Sources for every rule: [research 0005](../../docs/research/0005-geometria-notation-conventions.md).

## Adopted

1. **Angles in prose** — „kąt ABC" or „kąt α". Angle symbols and measure bars (`∢`, `∡`, `|∢ABC|`) belong to CKE marking schemes and stay out of questions.
2. **Parallel and perpendicular** — said in Polish words; the symbols `∥` and `⊥` stay out of questions.
3. **Equal sides and equal angles** — stated in the prose, so the Student derives them. Ticks go on the figure only on the Levels chosen to show them, or where the author judges the figure needs them.
4. **Unknowns** — when the prose names an unknown by symbol, it reads that symbol off the figure's annotation rather than retyping it. A diameter is named by the word: the figure labels it `d`, the prose says „Oblicz średnicę."
5. **Sides** — named by their endpoints (`AB`) or by the label beside them. A side `a` need not be opposite vertex `A`.
6. **Klasy 4–8 forms only** — liceum notation such as `o(S, r)` stays out.

## Not adopted

Findings in research 0005 the app departs from on purpose. These are settled, not bugs to fix.

- **Monochrome figures** (CKE) — the accent colour stays, for legibility on screen.
- **Italic vertex letters** — vertex letters are upright; only unknown symbols are italic.
- **A height's label inside the figure** — it is placed outward.
- **Vertex letters only when the prose names them** — figures draw them regardless.
- **Vertex runs not starting at `A`** (CKE's „trapez KLMN") — figures are lettered `ABCDE…`.
- **Parallel arrows** — not used in Polish klasy 4–8 material; parallelism is stated in prose (rule 2).
- **Pooled unknown letters** — each unknown has one fixed symbol.
