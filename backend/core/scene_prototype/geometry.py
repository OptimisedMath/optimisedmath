"""PROTOTYPE — throwaway. Figure constructors: maths in, geometry out.

The whole point of this module is that a generator never writes a coordinate.
It states the maths ("a triangle with base 8 and height 5"), and the constructor
derives the vertices. There is no second source of truth for the renderer to
disagree with, so a diagram that contradicts its own numbers is not expressible.

Maths coordinates throughout: y is UP. The renderer flips once, at the end.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

Pt = tuple[float, float]

_NAMES = "ABCDEFGHIJKL"


def sub(p: Pt, q: Pt) -> Pt:
    return (p[0] - q[0], p[1] - q[1])


def add(p: Pt, q: Pt) -> Pt:
    return (p[0] + q[0], p[1] + q[1])


def mul(p: Pt, k: float) -> Pt:
    return (p[0] * k, p[1] * k)


def norm(p: Pt) -> float:
    return math.hypot(p[0], p[1])


def unit(p: Pt) -> Pt:
    n = norm(p)
    return (0.0, 0.0) if n == 0 else (p[0] / n, p[1] / n)


def perp(p: Pt) -> Pt:
    return (-p[1], p[0])


def dot(p: Pt, q: Pt) -> float:
    return p[0] * q[0] + p[1] * q[1]


def _signed_area(pts: list[Pt]) -> float:
    s = 0.0
    for i, (x1, y1) in enumerate(pts):
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return s / 2


@dataclass
class Figure:
    """A constructed figure. Vertices are named A, B, C... in outline order."""

    kind: str  # "polygon" | "circle"
    points: dict[str, Pt] = field(default_factory=dict)
    outline: list[str] = field(default_factory=list)
    centre: Pt = (0.0, 0.0)
    radius: float = 0.0
    #: the maths quantities the constructor was given — label text derives from
    #: these, never from a value the generator retypes.
    quantities: dict[str, float] = field(default_factory=dict)

    def p(self, name: str) -> Pt:
        return self.points[name]

    def edge(self, e: str) -> tuple[Pt, Pt]:
        return self.points[e[0]], self.points[e[1]]

    def edge_length(self, e: str) -> float:
        a, b = self.edge(e)
        return norm(sub(b, a))

    def neighbours(self, v: str) -> tuple[str, str]:
        i = self.outline.index(v)
        n = len(self.outline)
        return self.outline[i - 1], self.outline[(i + 1) % n]

    def is_convex_at(self, v: str) -> bool:
        """True unless `v` is a reflex corner. Outline is always CCW, so the
        cross product of the two edge directions settles it."""
        prev, nxt = self.neighbours(v)
        d1 = sub(self.points[v], self.points[prev])
        d2 = sub(self.points[nxt], self.points[v])
        return d1[0] * d2[1] - d1[1] * d2[0] >= 0

    def interior_angle(self, v: str) -> float:
        """Interior angle at `v` in degrees, derived from the coordinates.

        Reflex corners return > 180 — the L-shaped outlines of Topic 100/160
        have them, and an arc drawn on the wrong side is a wrong diagram.
        """
        prev, nxt = self.neighbours(v)
        u = unit(sub(self.points[prev], self.points[v]))
        w = unit(sub(self.points[nxt], self.points[v]))
        raw = math.degrees(math.acos(max(-1.0, min(1.0, dot(u, w)))))
        return raw if self.is_convex_at(v) else 360 - raw

    def centroid(self) -> Pt:
        if self.kind == "circle":
            return self.centre
        xs = [self.points[v][0] for v in self.outline]
        ys = [self.points[v][1] for v in self.outline]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def area(self) -> float:
        if self.kind == "circle":
            return math.pi * self.radius**2
        return abs(_signed_area([self.points[v] for v in self.outline]))


def polygon(pts: list[Pt], **quantities: float) -> Figure:
    """Build a polygon, forced counter-clockwise so 'outward' is unambiguous."""
    if _signed_area(pts) < 0:
        pts = list(reversed(pts))
    names = list(_NAMES[: len(pts)])
    return Figure(
        kind="polygon",
        points=dict(zip(names, pts)),
        outline=names,
        quantities=quantities,
    )


# --- Triangles ---------------------------------------------------------


class Triangle:
    @staticmethod
    def sss(a: float, b: float, c: float) -> Figure:
        """Sides a=BC, b=CA, c=AB. Raises if the triangle inequality fails."""
        if a + b <= c or b + c <= a or c + a <= b:
            raise ValueError(f"no triangle with sides {a}, {b}, {c}")
        x = (b * b + c * c - a * a) / (2 * c)
        y = math.sqrt(max(0.0, b * b - x * x))
        return polygon([(0, 0), (c, 0), (x, y)], a=a, b=b, c=c)

    @staticmethod
    def base_height(base: float, height: float, apex_frac: float = 0.35) -> Figure:
        """Base AB on the x-axis, apex C at `height` above it.

        `apex_frac` places the apex along the base; < 0 or > 1 puts it outside,
        giving the obtuse case where the altitude foot falls off the base.
        """
        return polygon(
            [(0, 0), (base, 0), (apex_frac * base, height)], base=base, height=height
        )

    @staticmethod
    def sas(b: float, angle_a: float, c: float) -> Figure:
        """Sides b=CA and c=AB with the included angle at A, in degrees."""
        t = math.radians(angle_a)
        return polygon(
            [(0, 0), (c, 0), (b * math.cos(t), b * math.sin(t))],
            b=b,
            c=c,
            angle_a=angle_a,
        )

    @staticmethod
    def angles(angle_a: float, angle_b: float, scale: float = 10.0) -> Figure:
        """Two angles fix the shape; `scale` (side AB) fixes the size."""
        if angle_a + angle_b >= 180:
            raise ValueError("angles must sum to less than 180")
        ta, tb = math.radians(angle_a), math.radians(angle_b)
        x = scale * math.tan(tb) / (math.tan(ta) + math.tan(tb))
        return polygon(
            [(0, 0), (scale, 0), (x, x * math.tan(ta))],
            angle_a=angle_a,
            angle_b=angle_b,
            angle_c=180 - angle_a - angle_b,
        )


# --- Quadrilaterals ----------------------------------------------------


def rectangle(width: float, height: float) -> Figure:
    return polygon(
        [(0, 0), (width, 0), (width, height), (0, height)], width=width, height=height
    )


def square(side: float) -> Figure:
    return rectangle(side, side)


def parallelogram(base: float, side: float, angle: float = 60.0) -> Figure:
    """Height is DERIVED (side·sinθ), never supplied — so it cannot be drawn
    near-equal to the side by accident, which is the whole of
    `multiplies_the_two_sides_of_a_parallelogram`."""
    t = math.radians(angle)
    dx, dy = side * math.cos(t), side * math.sin(t)
    return polygon(
        [(0, 0), (base, 0), (base + dx, dy), (dx, dy)],
        base=base,
        side=side,
        angle=angle,
        height=dy,
    )


def trapezoid(a: float, b: float, height: float, offset: float | None = None) -> Figure:
    """`a` = lower base AB, `b` = upper base, `height` between them.

    `offset` shifts the upper base; None centres it (równoramienny); 0 gives the
    trapez prostokątny.
    """
    if offset is None:
        offset = (a - b) / 2
    return polygon(
        [(0, 0), (a, 0), (offset + b, height), (offset, height)],
        a=a,
        b=b,
        height=height,
    )


def rhombus(side: float, angle: float = 60.0) -> Figure:
    return parallelogram(side, side, angle)


def rhombus_diagonals(d1: float, d2: float) -> Figure:
    """A rhombus given its diagonals — the shape the d₁·d₂/2 formula talks about."""
    return polygon([(0, -d2 / 2), (d1 / 2, 0), (0, d2 / 2), (-d1 / 2, 0)], d1=d1, d2=d2)


# --- General polygons --------------------------------------------------


def regular_polygon(n: int, side: float) -> Figure:
    r = side / (2 * math.sin(math.pi / n))
    start = -math.pi / 2 + math.pi / n
    pts = [
        (
            r * math.cos(start + 2 * math.pi * k / n),
            r * math.sin(start + 2 * math.pi * k / n),
        )
        for k in range(n)
    ]
    return polygon(pts, n=n, side=side)


def rectilinear(steps: list[tuple[float, float]]) -> Figure:
    """Composite L/T/plus outline from a closed walk of axis-aligned steps.

    The escape hatch for Topic 160 — still maths-in (each step IS a labelled
    length), still no free coordinates.
    """
    pts: list[Pt] = [(0.0, 0.0)]
    for step in steps:
        pts.append(add(pts[-1], step))
    if norm(sub(pts[-1], pts[0])) > 1e-9:
        raise ValueError("rectilinear walk does not close")
    return polygon(pts[:-1])


def circle(radius: float) -> Figure:
    return Figure(
        kind="circle", centre=(0.0, 0.0), radius=radius, quantities={"r": radius}
    )
