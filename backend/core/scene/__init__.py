"""Declarative geometry scenes: a figure built from maths, annotated symbolically.

A generator states the maths (`Triangle.base_height(base=8, height=5)`), names the
parts it wants annotated (`EdgeLabel("AB")`, `Altitude(apex="C", base="AB")`), and
calls `Scene(...).to_svg()`. It never writes a coordinate and never types a label's
number — both are read back off the constructed figure, so a diagram that
contradicts its own labels is not expressible (#211).

`unknown=True` on a label is the only supported way to withhold a value; it prints
`x` and still cannot print a *different* number.
"""

from backend.core.scene.geometry import (
    Figure,
    Pt,
    circle,
    parallelogram,
    polygon,
    rectangle,
    rectilinear,
    regular_polygon,
    rhombus,
    rhombus_diagonals,
    square,
    trapezoid,
    Triangle,
)
from backend.core.scene.render import (
    MIN_LABELLED_ANGLE,
    Altitude,
    AngleArc,
    Annotation,
    Caption,
    Centre,
    DimensionLine,
    EdgeLabel,
    Grid,
    Hatch,
    Outline,
    ParallelMarks,
    Radius,
    RightAngle,
    Scene,
    Sector,
    Segment,
    Ticks,
    VertexLabels,
)

__all__ = [
    "MIN_LABELLED_ANGLE",
    "Altitude",
    "AngleArc",
    "Annotation",
    "Caption",
    "Centre",
    "DimensionLine",
    "EdgeLabel",
    "Figure",
    "Grid",
    "Hatch",
    "Outline",
    "ParallelMarks",
    "Pt",
    "Radius",
    "RightAngle",
    "Scene",
    "Sector",
    "Segment",
    "Ticks",
    "Triangle",
    "VertexLabels",
    "circle",
    "parallelogram",
    "polygon",
    "rectangle",
    "rectilinear",
    "regular_polygon",
    "rhombus",
    "rhombus_diagonals",
    "square",
    "trapezoid",
]
