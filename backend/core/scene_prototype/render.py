"""PROTOTYPE — throwaway. Annotations + the single SVG renderer.

Annotations name parts of the figure symbolically ("edge AB", "vertex C") and
never carry coordinates. Their *text* is derived from the constructed figure,
so a label that disagrees with the drawing is not expressible.

Three things this module owns, so that 22 generators do not:
  1. outward-normal label placement (right-hand perp of a CCW outline — locally
     correct even at the concave corners of an L-shape, where a centroid test
     would put the label inside the figure);
  2. arc radius allocation — nested arcs at one vertex, and arcs shrunk to fit
     a narrow vertex angle;
  3. viewBox derived from the content bounding box, labels included.

Colour policy: the figure draws in `currentColor`, so it inherits the page's
text colour and is correct in light and dark mode for free. Only construction
lines and fills carry an explicit accent.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field

from backend.core.scene_prototype.geometry import (
    Figure,
    Pt,
    add,
    dot,
    mul,
    norm,
    sub,
    unit,
)

INK = "currentColor"
ACCENT = "#f43f5e"
MUTED = "#94a3b8"


def _fmt(v: float) -> str:
    """Polish decimal comma; integers stay bare."""
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _pts(points: list[Pt]) -> str:
    # Maths y is up, SVG y is down: the flip happens here, once, per coordinate
    # — never as a group transform, which would mirror every text glyph.
    return " ".join(f"{x:.3f},{-y:.3f}" for x, y in points)


@dataclass
class Label:
    """A requested label. Its final position is decided by `Ctx.place_labels`."""

    anchor: Pt
    direction: Pt
    text: str
    color: str
    size: float
    gap: float
    half_w: float
    half_h: float

    def reach(self) -> float:
        """Half-extent of the glyph box along the placement direction, so the
        box clears the anchor rather than merely its centre."""
        return (
            abs(self.direction[0]) * self.half_w + abs(self.direction[1]) * self.half_h
        )


Box = tuple[float, float, float, float]


def _overlap(a: Box, b: Box) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _hits(box: Box, seg: tuple[Pt, Pt]) -> bool:
    """Segment vs axis-aligned box, by the slab method."""
    (x0, y0), (x1, y1) = seg
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q, lo, hi in ((x0, dx, box[0], box[2]), (y0, dy, box[1], box[3])):
        if abs(q) < 1e-12:
            if p < lo or p > hi:
                return False
        else:
            a, b = (lo - p) / q, (hi - p) / q
            t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
            if t0 > t1:
                return False
    return True


@dataclass
class Ctx:
    """Render context: the figure, the derived size unit, and the output."""

    fig: Figure
    u: float  # one "pen unit" — every stroke width and font size is a multiple
    parts: list[str] = field(default_factory=list)
    defs: list[str] = field(default_factory=list)
    extent: list[Pt] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)
    #: every stroke drawn so far, so labels can avoid sitting on the figure
    obstacles: list[tuple[Pt, Pt]] = field(default_factory=list)
    #: how many arcs have been drawn at each vertex, for radius allocation
    arc_count: dict[str, int] = field(default_factory=dict)

    # --- sizes ---------------------------------------------------------
    @property
    def stroke(self) -> float:
        return self.u * 1.1

    @property
    def thin(self) -> float:
        return self.u * 0.65

    @property
    def font(self) -> float:
        return self.u * 6.0

    def include(self, *points: Pt) -> None:
        self.extent.extend(points)

    # --- placement rules -----------------------------------------------
    def outward_normal(self, e: str) -> Pt:
        """Outward unit normal of edge `e`. The outline is CCW, so the outward
        side is always the right-hand perp — no centroid test, which is what
        makes this correct on non-convex outlines."""
        a, b = self.fig.edge(e)
        d = unit(sub(b, a))
        return (d[1], -d[0])

    def outward_bisector(self, v: str) -> Pt:
        prev, nxt = self.fig.neighbours(v)
        u1 = unit(sub(self.fig.p(prev), self.fig.p(v)))
        u2 = unit(sub(self.fig.p(nxt), self.fig.p(v)))
        b = add(u1, u2)
        if norm(b) < 1e-9:  # straight angle — fall back to the edge normal
            b = (u1[1], -u1[0])
        b = unit(b)
        inward = b if self.fig.is_convex_at(v) else mul(b, -1)
        return mul(inward, -1)

    def arc_radius(self, v: str) -> float:
        """Rule 2. Sized against the SHORTER adjacent edge so the arc cannot
        overrun the figure, shrunk further at narrow vertices so a 20° corner's
        arc still leaves room for its own label, and grown for each arc already
        drawn at this vertex so nested arcs nest."""
        prev, nxt = self.fig.neighbours(v)
        shortest = min(
            norm(sub(self.fig.p(prev), self.fig.p(v))),
            norm(sub(self.fig.p(nxt), self.fig.p(v))),
        )
        angle = self.fig.interior_angle(v)
        squeeze = min(1.0, angle / 60.0) ** 0.5  # narrow angle -> smaller arc
        r = shortest * 0.26 * max(0.45, squeeze)
        n = self.arc_count.get(v, 0)
        self.arc_count[v] = n + 1
        return r * (1 + 0.42 * n)

    # --- emit ----------------------------------------------------------
    def line(
        self,
        a: Pt,
        b: Pt,
        *,
        color: str = INK,
        width: float | None = None,
        dash: str = "",
    ) -> None:
        w = self.stroke if width is None else width
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{a[0]:.3f}" y1="{-a[1]:.3f}" x2="{b[0]:.3f}" y2="{-b[1]:.3f}" '
            f'stroke="{color}" stroke-width="{w:.3f}" stroke-linecap="round"{d}/>'
        )
        self.include(a, b)
        self.obstacles.append((a, b))

    def path(
        self,
        points: list[Pt],
        *,
        color: str = INK,
        width: float | None = None,
        dash: str = "",
        fill: str = "none",
    ) -> None:
        w = self.stroke if width is None else width
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<polyline points="{_pts(points)}" fill="{fill}" stroke="{color}" '
            f'stroke-width="{w:.3f}" stroke-linecap="round" stroke-linejoin="round"{d}/>'
        )
        self.include(*points)
        self.obstacles.extend(zip(points, points[1:]))

    def text(
        self,
        anchor: Pt,
        direction: Pt,
        label: str,
        *,
        color: str = INK,
        scale: float = 1.0,
        gap: float = 1.6,
    ) -> None:
        """Rule 1. Request a label placed outside the figure along `direction`.

        Nothing is emitted here. Labels are the one thing that cannot be placed
        in isolation — two annotations that know nothing about each other will
        happily write over the same spot — so placement is deferred to
        `place_labels`, once every stroke in the scene is known.
        """
        size = self.font * scale
        self.labels.append(
            Label(
                anchor=anchor,
                direction=unit(direction) or (0.0, 1.0),
                text=label,
                color=color,
                size=size,
                gap=gap,
                half_w=0.30 * size * max(1, len(label)),
                half_h=0.58 * size,
            )
        )

    # --- Rule 4: label placement is a whole-scene pass ------------------
    def place_labels(self) -> None:
        """Push each label out along its own direction until it clears both the
        strokes of the figure and every label already placed.

        Sliding along the placement direction is what keeps the result
        *meaningful*: a length label stays on the outward side of its own edge,
        it just moves further out. Nudging sideways would be free but could park
        a label beside the wrong edge.
        """
        placed: list[Box] = []
        for lab in self.labels:
            best_box, best_cost = None, None
            # Two candidate sides. Sliding outward is tried first and preferred,
            # but a label that starts inside a narrow wedge — the height of a
            # squat trapezoid, the arc of a 25 degree vertex — can never escape
            # by sliding one way, so the opposite side is a candidate too.
            for sign in (1.0, -1.0):
                d = mul(lab.direction, sign)
                for step in range(0, 14):
                    c = add(
                        lab.anchor,
                        mul(d, lab.gap * self.u + lab.reach() + step * self.u * 1.7),
                    )
                    box = (
                        c[0] - lab.half_w,
                        c[1] - lab.half_h,
                        c[0] + lab.half_w,
                        c[1] + lab.half_h,
                    )
                    cost = sum(1.0 for q in placed if _overlap(box, q))
                    cost += sum(0.75 for seg in self.obstacles if _hits(box, seg))
                    # tie-breakers: stay near what the label describes, and
                    # prefer the outward side when both are clear
                    cost += step * 0.05 + (0.12 if sign < 0 else 0.0)
                    if best_cost is None or cost < best_cost:
                        best_box, best_cost = box, cost
                    if cost < 0.5:
                        break
                if best_cost is not None and best_cost < 0.5:
                    break
            assert best_box is not None
            placed.append(best_box)
            cx = (best_box[0] + best_box[2]) / 2
            cy = (best_box[1] + best_box[3]) / 2
            self.parts.append(
                f'<text x="{cx:.3f}" y="{-cy:.3f}" fill="{lab.color}" font-size="{lab.size:.3f}" '
                f'font-family="system-ui, -apple-system, sans-serif" font-weight="600" '
                f'text-anchor="middle" dominant-baseline="central">{lab.text}</text>'
            )
            self.include((best_box[0], best_box[1]), (best_box[2], best_box[3]))

    def arc_points(
        self,
        centre: Pt,
        radius: float,
        from_dir: Pt,
        to_dir: Pt,
        through: Pt,
        steps: int = 28,
    ) -> list[Pt]:
        """Arc from one direction to another, taking the side that passes
        `through`. Drawn as a polyline — same picture, none of the sweep-flag
        bugs, and reflex arcs come out right."""
        a0 = math.atan2(from_dir[1], from_dir[0])
        a1 = math.atan2(to_dir[1], to_dir[0])
        d = (a1 - a0) % (2 * math.pi)
        mid = a0 + d / 2
        if dot((math.cos(mid), math.sin(mid)), through) < 0:
            d -= 2 * math.pi
        return [
            add(
                centre,
                mul(
                    (math.cos(a0 + d * k / steps), math.sin(a0 + d * k / steps)), radius
                ),
            )
            for k in range(steps + 1)
        ]


# --- Annotations -------------------------------------------------------


class Annotation:
    def render(self, ctx: Ctx) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class Outline(Annotation):
    """The figure itself. Filled = koło / a shaded region; stroked = okrąg."""

    fill: bool = False
    dash: str = ""

    def render(self, ctx: Ctx) -> None:
        f = ctx.fig
        fill = f'{INK}" fill-opacity="0.12' if self.fill else "none"
        d = (
            f' stroke-dasharray="{ctx.u * 3:.2f} {ctx.u * 2.4:.2f}"'
            if self.dash
            else ""
        )
        if f.kind == "circle":
            cx, cy = f.centre
            ctx.parts.append(
                f'<circle cx="{cx:.3f}" cy="{-cy:.3f}" r="{f.radius:.3f}" fill="{fill}" '
                f'stroke="{INK}" stroke-width="{ctx.stroke:.3f}"{d}/>'
            )
            ctx.include((cx - f.radius, cy - f.radius), (cx + f.radius, cy + f.radius))
            ring = [
                (
                    cx + f.radius * math.cos(2 * math.pi * k / 36),
                    cy + f.radius * math.sin(2 * math.pi * k / 36),
                )
                for k in range(37)
            ]
            ctx.obstacles.extend(zip(ring, ring[1:]))
        else:
            pts = [f.p(v) for v in f.outline]
            ctx.parts.append(
                f'<polygon points="{_pts(pts)}" fill="{fill}" stroke="{INK}" '
                f'stroke-width="{ctx.stroke:.3f}" stroke-linejoin="round"{d}/>'
            )
            ctx.include(*pts)
            ctx.obstacles.extend(zip(pts, pts[1:] + pts[:1]))


@dataclass
class VertexLabels(Annotation):
    """`A B C` placed along each outward angle bisector."""

    only: list[str] | None = None

    def render(self, ctx: Ctx) -> None:
        for v in ctx.fig.outline:
            if self.only is None or v in self.only:
                ctx.text(ctx.fig.p(v), ctx.outward_bisector(v), v, scale=0.92, gap=2.2)


@dataclass
class EdgeLabel(Annotation):
    """A length label on an edge.

    The text is DERIVED from the constructed edge, so it cannot contradict the
    picture. `unknown` prints `x` instead of the value — the only supported way
    to withhold it, and the generator still cannot print a *different* number.
    """

    edge: str
    unit_label: str = ""
    unknown: bool = False
    unknown_text: str = "x"
    inside: bool = False

    def text_for(self, ctx: Ctx) -> str:
        if self.unknown:
            return self.unknown_text
        value = _fmt(ctx.fig.edge_length(self.edge))
        return f"{value} {self.unit_label}".strip()

    def render(self, ctx: Ctx) -> None:
        a, b = ctx.fig.edge(self.edge)
        mid = mul(add(a, b), 0.5)
        n = ctx.outward_normal(self.edge)
        if self.inside:
            n = mul(n, -1)
        ctx.text(mid, n, self.text_for(ctx))


#: #212 found the placement floor by scanning: below this, `place_labels` cannot
#: find a spot for the angle's own label that clears the vertex — verified by
#: `find_threshold.py`, which crosses the collision-cost threshold between 12°
#: and 13°. 15° keeps a margin. There is no matching ceiling: 179.4° (the
#: narrowest margin tested) placed cleanly.
MIN_LABELLED_ANGLE = 15.0


@dataclass
class AngleArc(Annotation):
    """An arc at a vertex, labelled with the angle DERIVED from the figure.

    Refuses a labelled arc below `MIN_LABELLED_ANGLE` — below that floor the
    label cannot be placed clear of the vertex it describes, so a diagram
    would show a label sitting on top of its own figure. #212 declared this a
    generator-side range limit rather than a placement algorithm to fix
    further: every Geometria generator using AngleArc must keep the angle at
    or above this floor.
    """

    vertex: str
    unknown: bool = False
    unknown_text: str = "x"
    show_label: bool = True

    def render(self, ctx: Ctx) -> None:
        f = ctx.fig
        v = f.p(self.vertex)
        prev, nxt = f.neighbours(self.vertex)
        u1 = unit(sub(f.p(prev), v))
        u2 = unit(sub(f.p(nxt), v))
        if self.show_label and f.interior_angle(self.vertex) < MIN_LABELLED_ANGLE:
            raise ValueError(
                f"vertex {self.vertex} is {f.interior_angle(self.vertex):.1f}°, "
                f"below the {MIN_LABELLED_ANGLE}° minimum for a labelled AngleArc"
            )
        r = ctx.arc_radius(self.vertex)
        inward = mul(ctx.outward_bisector(self.vertex), -1)
        ctx.path(ctx.arc_points(v, r, u1, u2, inward), color=ACCENT, width=ctx.thin)
        if self.show_label:
            deg = f.interior_angle(self.vertex)
            label = self.unknown_text if self.unknown else f"{_fmt(deg)}°"
            ctx.text(
                add(v, mul(inward, r)), inward, label, color=ACCENT, scale=0.85, gap=1.2
            )


@dataclass
class RightAngle(Annotation):
    """The mandatory square marker. Refuses to draw on a vertex that is not a
    right angle — a right-angle marker on a 72° corner is a wrong diagram."""

    vertex: str

    def render(self, ctx: Ctx) -> None:
        f = ctx.fig
        angle = f.interior_angle(self.vertex)
        if abs(angle - 90) > 0.5:
            raise ValueError(f"vertex {self.vertex} is {angle:.1f}°, not a right angle")
        v = f.p(self.vertex)
        prev, nxt = f.neighbours(self.vertex)
        u1 = mul(unit(sub(f.p(prev), v)), ctx.u * 5)
        u2 = mul(unit(sub(f.p(nxt), v)), ctx.u * 5)
        ctx.path([add(v, u1), add(v, add(u1, u2)), add(v, u2)], width=ctx.thin)


@dataclass
class Ticks(Annotation):
    """Congruence marks: on an edge for equal lengths, on an arc for equal angles."""

    edge: str
    count: int = 1

    def render(self, ctx: Ctx) -> None:
        a, b = ctx.fig.edge(self.edge)
        mid = mul(add(a, b), 0.5)
        d = unit(sub(b, a))
        n = (d[1], -d[0])
        spacing = ctx.u * 2.6
        for i in range(self.count):
            off = mul(d, (i - (self.count - 1) / 2) * spacing)
            c = add(mid, off)
            ctx.line(
                add(c, mul(n, ctx.u * 2.4)),
                add(c, mul(n, -ctx.u * 2.4)),
                width=ctx.thin,
            )


@dataclass
class ParallelMarks(Annotation):
    """Matching chevrons marking edges as parallel (the trapezoid's two bases)."""

    edges: list[str]
    count: int = 1

    def render(self, ctx: Ctx) -> None:
        reference: Pt | None = None
        for e in self.edges:
            a, b = ctx.fig.edge(e)
            mid = mul(add(a, b), 0.5)
            d = unit(sub(b, a))
            if reference is None:
                reference = d
            elif dot(d, reference) < 0:
                d = mul(d, -1)  # keep every chevron in the group pointing alike
            n = (d[1], -d[0])
            s = ctx.u * 2.6
            for i in range(self.count):
                c = add(mid, mul(d, (i - (self.count - 1) / 2) * s * 1.3))
                ctx.path(
                    [
                        add(add(c, mul(d, -s * 0.8)), mul(n, s)),
                        c,
                        add(add(c, mul(d, -s * 0.8)), mul(n, -s)),
                    ],
                    width=ctx.thin,
                )


@dataclass
class Altitude(Annotation):
    """A height, dashed, from `apex` perpendicular to edge `base`.

    Derives the foot. When the foot lands off the segment — the rozwartokątny
    case of Topic 130 — it also draws the dotted base extension, because the
    figure is wrong without it.
    """

    apex: str
    base: str
    label: bool = True
    unit_label: str = ""
    unknown: bool = False

    def foot(self, ctx: Ctx) -> tuple[Pt, bool]:
        f = ctx.fig
        p = f.p(self.apex)
        q, r = f.edge(self.base)
        d = unit(sub(r, q))
        t = dot(sub(p, q), d)
        return add(q, mul(d, t)), 0 <= t <= norm(sub(r, q))

    def render(self, ctx: Ctx) -> None:
        f = ctx.fig
        p = f.p(self.apex)
        q, r = f.edge(self.base)
        foot, on_segment = self.foot(ctx)
        if not on_segment:
            near = q if norm(sub(foot, q)) < norm(sub(foot, r)) else r
            ctx.line(
                near,
                foot,
                color=MUTED,
                width=ctx.thin,
                dash=f"{ctx.u:.2f} {ctx.u * 2:.2f}",
            )
        ctx.line(p, foot, color=ACCENT, dash=f"{ctx.u * 3:.2f} {ctx.u * 2.2:.2f}")
        # right-angle marker at the foot, opening toward the apex
        toward_apex = unit(sub(p, foot))
        along = unit(sub(r, q))
        if not on_segment:
            along = mul(along, -1) if dot(sub(q, foot), along) > 0 else along
        s = ctx.u * 4.5
        ctx.path(
            [
                add(foot, mul(along, s)),
                add(foot, add(mul(along, s), mul(toward_apex, s))),
                add(foot, mul(toward_apex, s)),
            ],
            color=ACCENT,
            width=ctx.thin,
        )
        if self.label:
            mid = mul(add(p, foot), 0.5)
            n = unit((sub(p, foot)[1], -sub(p, foot)[0]))
            if dot(n, sub(mid, f.centroid())) < 0:
                n = mul(n, -1)
            text = (
                "x"
                if self.unknown
                else f"{_fmt(norm(sub(p, foot)))} {self.unit_label}".strip()
            )
            ctx.text(mid, n, text, color=ACCENT, scale=0.9)


@dataclass
class Segment(Annotation):
    """An interior segment between two named vertices — a diagonal, a symmetry
    axis, a chord. Dashed by default: these are construction lines, and Topic 90
    needs them visibly distinct from the figure's own edges."""

    frm: str
    to: str
    dash: bool = True
    color: str = MUTED
    label: str | None = None

    def render(self, ctx: Ctx) -> None:
        a, b = ctx.fig.p(self.frm), ctx.fig.p(self.to)
        ctx.line(
            a,
            b,
            color=self.color,
            dash=f"{ctx.u * 3:.2f} {ctx.u * 2.2:.2f}" if self.dash else "",
        )
        if self.label:
            mid = mul(add(a, b), 0.5)
            d = unit(sub(b, a))
            ctx.text(mid, (d[1], -d[0]), self.label, color=self.color, scale=0.85)


@dataclass
class DimensionLine(Annotation):
    """Extension lines + arrowheads + label, offset clear of the figure —
    the practical-measurement look Topic 110 asks for."""

    edge: str
    offset: float = 6.0
    unit_label: str = ""

    def render(self, ctx: Ctx) -> None:
        a, b = ctx.fig.edge(self.edge)
        n = mul(ctx.outward_normal(self.edge), self.offset * ctx.u)
        a2, b2 = add(a, n), add(b, n)
        ext = mul(unit(n), ctx.u * 1.8)
        ctx.line(add(a, ext), add(a2, ext), color=MUTED, width=ctx.thin)
        ctx.line(add(b, ext), add(b2, ext), color=MUTED, width=ctx.thin)
        ctx.line(a2, b2, color=MUTED, width=ctx.thin)
        d = unit(sub(b2, a2))
        h = ctx.u * 3.0
        for tip, sign in ((a2, 1), (b2, -1)):
            back = mul(d, sign * h)
            side = mul((d[1], -d[0]), h * 0.38)
            ctx.parts.append(
                f'<polygon points="{_pts([tip, add(add(tip, back), side), add(add(tip, back), mul(side, -1))])}" fill="{MUTED}"/>'
            )
        ctx.text(
            mul(add(a2, b2), 0.5),
            unit(n),
            f"{_fmt(ctx.fig.edge_length(self.edge))} {self.unit_label}".strip(),
            color=MUTED,
            scale=0.85,
        )


@dataclass
class Hatch(Annotation):
    """Diagonal hatching over the figure — 'the part you want' in Topic 160."""

    def render(self, ctx: Ctx) -> None:
        pid = f"h{uuid.uuid4().hex[:6]}"
        s = ctx.u * 5
        ctx.defs.append(
            f'<pattern id="{pid}" width="{s:.2f}" height="{s:.2f}" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="{s:.2f}" '
            f'stroke="{ACCENT}" stroke-width="{ctx.thin:.2f}" opacity="0.65"/></pattern>'
        )
        pts = [ctx.fig.p(v) for v in ctx.fig.outline]
        ctx.parts.append(f'<polygon points="{_pts(pts)}" fill="url(#{pid})"/>')


@dataclass
class Grid(Annotation):
    """Square lattice behind the figure — Topic 120's unit squares, Topic 210's
    countable reflection."""

    spacing: float = 1.0
    pad: float = 0.0

    def render(self, ctx: Ctx) -> None:
        xs = [p[0] for p in ctx.fig.points.values()] or [0]
        ys = [p[1] for p in ctx.fig.points.values()] or [0]
        if ctx.fig.kind == "circle":
            xs = [
                ctx.fig.centre[0] - ctx.fig.radius,
                ctx.fig.centre[0] + ctx.fig.radius,
            ]
            ys = [
                ctx.fig.centre[1] - ctx.fig.radius,
                ctx.fig.centre[1] + ctx.fig.radius,
            ]
        x0, x1 = min(xs) - self.pad, max(xs) + self.pad
        y0, y1 = min(ys) - self.pad, max(ys) + self.pad
        n = self.spacing
        k = x0
        while k <= x1 + 1e-9:
            ctx.line((k, y0), (k, y1), color=MUTED, width=ctx.thin * 0.55)
            k += n
        k = y0
        while k <= y1 + 1e-9:
            ctx.line((x0, k), (x1, k), color=MUTED, width=ctx.thin * 0.55)
            k += n


# --- Circle-specific ---------------------------------------------------


@dataclass
class Centre(Annotation):
    label: str = "O"

    def render(self, ctx: Ctx) -> None:
        c = ctx.fig.centre
        ctx.parts.append(
            f'<circle cx="{c[0]:.3f}" cy="{-c[1]:.3f}" r="{ctx.u * 1.5:.3f}" fill="{INK}"/>'
        )
        ctx.text(c, (-0.7, -0.7), self.label, scale=0.9, gap=1.0)


@dataclass
class Radius(Annotation):
    """Radius, diameter or chord — all the same primitive at different angles."""

    at: float = 35.0
    unit_label: str = ""
    diameter: bool = False
    unknown: bool = False

    def render(self, ctx: Ctx) -> None:
        f = ctx.fig
        t = math.radians(self.at)
        d = (math.cos(t), math.sin(t))
        end = add(f.centre, mul(d, f.radius))
        start = add(f.centre, mul(d, -f.radius)) if self.diameter else f.centre
        ctx.line(start, end, color=ACCENT)
        length = f.radius * (2 if self.diameter else 1)
        text = "x" if self.unknown else f"{_fmt(length)} {self.unit_label}".strip()
        ctx.text(
            mul(add(start, end), 0.5), (d[1], -d[0]), text, color=ACCENT, scale=0.9
        )


@dataclass
class Sector(Annotation):
    """A shaded pie slice with its central angle arc — where the arc primitive
    and the fill primitive have to co-operate (Topic 190)."""

    start: float = 0.0
    end: float = 70.0

    def render(self, ctx: Ctx) -> None:
        f = ctx.fig
        a0, a1 = math.radians(self.start), math.radians(self.end)
        steps = 40
        arc = [
            add(
                f.centre,
                mul(
                    (
                        math.cos(a0 + (a1 - a0) * k / steps),
                        math.sin(a0 + (a1 - a0) * k / steps),
                    ),
                    f.radius,
                ),
            )
            for k in range(steps + 1)
        ]
        ctx.parts.append(
            f'<polygon points="{_pts([f.centre] + arc)}" fill="{ACCENT}" fill-opacity="0.18" '
            f'stroke="{ACCENT}" stroke-width="{ctx.stroke:.3f}" stroke-linejoin="round"/>'
        )
        ctx.include(*arc)
        r = f.radius * 0.28
        small = [
            add(
                f.centre,
                mul(
                    (
                        math.cos(a0 + (a1 - a0) * k / 20),
                        math.sin(a0 + (a1 - a0) * k / 20),
                    ),
                    r,
                ),
            )
            for k in range(21)
        ]
        ctx.path(small, color=ACCENT, width=ctx.thin)
        mid = (a0 + a1) / 2
        bis = (math.cos(mid), math.sin(mid))
        ctx.text(
            add(f.centre, mul(bis, r)),
            bis,
            f"{_fmt(self.end - self.start)}°",
            color=ACCENT,
            scale=0.85,
            gap=1.0,
        )


@dataclass
class Caption(Annotation):
    """Free caption under the figure — Topic 220's scale note."""

    text_value: str

    def render(self, ctx: Ctx) -> None:
        xs = [p[0] for p in ctx.extent] or [0.0]
        ys = [p[1] for p in ctx.extent] or [0.0]
        anchor = ((min(xs) + max(xs)) / 2, min(ys))
        ctx.text(anchor, (0, -1), self.text_value, color=MUTED, scale=0.85, gap=3.0)


# --- The scene ---------------------------------------------------------


@dataclass
class Scene:
    figure: Figure
    annotations: list[Annotation]

    def to_svg(self, pad: float = 4.0) -> str:
        f = self.figure
        # Pass 1: the pen unit, from the figure's own size. Every stroke and
        # glyph is a multiple of it, so an 8-unit triangle and a 200-unit
        # rectangle come out looking identical.
        if f.kind == "circle":
            gw = gh = 2 * f.radius
        else:
            xs = [p[0] for p in f.points.values()]
            ys = [p[1] for p in f.points.values()]
            gw, gh = max(xs) - min(xs), max(ys) - min(ys)
        diag = max(math.hypot(gw, gh), 1e-6)
        ctx = Ctx(fig=f, u=diag / 100.0)

        # Pass 2: draw. Every emitter registers what it occupies.
        for a in self.annotations:
            a.render(ctx)

        # Pass 2b: resolve every label against every stroke and every other
        # label, now that the whole scene is known.
        ctx.place_labels()

        # Pass 3: viewBox from the content bbox — labels included, so nothing clips.
        xs = [p[0] for p in ctx.extent]
        ys = [p[1] for p in ctx.extent]
        p = pad * ctx.u
        x0, x1 = min(xs) - p, max(xs) + p
        y0, y1 = min(ys) - p, max(ys) + p
        w, h = x1 - x0, y1 - y0

        # Maths y is up, SVG y is down. One flip, applied to the viewBox rather
        # than to the elements, so text is never mirrored.
        body = "".join(ctx.parts)
        defs = f"<defs>{''.join(ctx.defs)}</defs>" if ctx.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.3f} {-y1:.3f} {w:.3f} {h:.3f}" '
            f'width="100%" style="max-width:100%;height:auto;overflow:visible" '
            f'role="img">{defs}{body}</svg>'
        )
