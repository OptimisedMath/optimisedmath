"""Geometria — Pole trójkąta: generatory Problemów."""

import math
import random

from backend.core.scene import (
    Altitude,
    EdgeLabel,
    Outline,
    RightAngle,
    Scene,
    Triangle,
    VertexLabels,
)
from backend.core.utils import (
    build_problem_dict,
    declared_units,
    declares_traps,
    declares_units,
)

# The ladder's one axis is how far the picture departs from the canonical
# altitude (#237), so the arithmetic stays on small integers on every rung and
# only the figure changes. Every rung labels a length that is neither the base
# nor the height, because without one `confuses_base_with_height` and
# `computes_the_perimeter_instead_of_the_area` have nothing to fire on.

TRAP_DOUBLES = "treats_the_triangle_area_as_base_times_height"  # b·h, no halving
TRAP_PERIMETER = "computes_the_perimeter_instead_of_the_area"  # suma boków
TRAP_SIDE_AS_HEIGHT = "confuses_base_with_height"  # bierze bok zamiast wysokości

# A figure is labelled in a length Unit; an area answer is that Unit squared.
# The Level declares the answer's Units, so this maps back to what the drawing says.
_LENGTH_FOR_AREA = {"mm²": "mm", "cm²": "cm", "dm²": "dm"}

# `m` and `km` are excluded deliberately: a drawn triangle measured in kilometres
# is not a figure anyone reads off a page, and word problems own those (#237).
AREA_UNITS = ("mm²", "cm²", "dm²")
LENGTH_UNITS = ("mm", "cm", "dm")

_MAX_BASE = 22
_MAX_HEIGHT = 24
# The arithmetic is not this Topic's axis (#237), so the pool is capped by the
# size of the numbers rather than by the size of the drawing.
_MAX_AREA = 170


def _int_sqrt(n: int) -> int | None:
    """The integer square root of `n`, or None when `n` is not a perfect square."""
    root = math.isqrt(n)
    return root if root * root == n else None


def _distinct(*values: int) -> bool:
    """Whether every option value differs — a collision would drop the Problem."""
    return len(set(values)) == len(values)


def _side_read_as_height(base: int, side_a: int, side_b: int) -> int | None:
    """The labelled side a Student is likeliest to multiply by instead of the height.

    The longer side, which is the one the dashed altitude runs nearest to — unless
    halving `base × side` would land off the integers, in which case the shorter
    one. None when neither works, which drops the triangle from the pool.
    """
    for side in sorted((side_a, side_b), reverse=True):
        if (base * side) % 2 == 0:
            return side
    return None


def _forward_options_agree(base: int, height: int, side_a: int, side_b: int) -> bool:
    """Whether the four forward options come out distinct on this triangle.

    Checked while enumerating rather than left to `build_problem_dict`'s collision
    return: a triangle whose perimeter equals its area is *always* dropped, so
    leaving it in the pool only burns retries and narrows the Problems a Student
    actually sees.
    """
    side = _side_read_as_height(base, side_a, side_b)
    if side is None:
        return False
    return _distinct(
        base * height // 2,
        base * height,
        base + side_a + side_b,
        base * side // 2,
    )


def _acute_triangles() -> list[tuple[int, int, int, int]]:
    """`(base, height, side CA, side BC)` with the altitude foot strictly inside.

    Enumerated rather than tabulated because the constraints are the interesting
    part: every printed length must be a whole number, so both feet of the
    altitude have to be legs of Pythagorean triples on the same height — and the
    apex angle must stay acute (`h² > d·e`), or the picture stops being the one
    the formula is taught with.
    """
    found: list[tuple[int, int, int, int]] = []
    for height in range(3, _MAX_HEIGHT + 1):
        feet = [d for d in range(1, 40) if _int_sqrt(d * d + height * height)]
        for index, left in enumerate(feet):
            for right in feet[index:]:
                base = left + right
                if base > _MAX_BASE or height * height <= left * right:
                    continue
                if (base * height) % 2 or base * height // 2 > _MAX_AREA:
                    continue
                side_a = _int_sqrt(left * left + height * height)
                side_b = _int_sqrt(right * right + height * height)
                assert side_a is not None and side_b is not None
                if _forward_options_agree(base, height, side_a, side_b):
                    found.append((base, height, side_a, side_b))
    return found


def _obtuse_triangles() -> list[tuple[int, int, int, int, int]]:
    """`(base, height, foot offset, side CA, side BC)` with the foot off the base.

    Same integrality constraint as `_acute_triangles`, but the apex hangs beyond
    vertex A, so the far foot is `offset + base` rather than `base - offset`.
    """
    found: list[tuple[int, int, int, int, int]] = []
    for height in range(3, _MAX_HEIGHT + 1):
        feet = [d for d in range(1, 60) if _int_sqrt(d * d + height * height)]
        for near in feet:
            for far in feet:
                base = far - near
                if not 0 < base <= _MAX_BASE or (base * height) % 2:
                    continue
                if height > 3 * base or base * height // 2 > _MAX_AREA:
                    continue
                side_a = _int_sqrt(near * near + height * height)
                side_b = _int_sqrt(far * far + height * height)
                assert side_a is not None and side_b is not None
                if _forward_options_agree(base, height, side_a, side_b):
                    found.append((base, height, near, side_a, side_b))
    return found


def _right_triangles() -> list[tuple[int, int, int]]:
    """`(base, height, hypotenuse)` — the height degenerated into a side."""
    found: list[tuple[int, int, int]] = []
    for leg in range(3, 25):
        for other in range(leg, 25):
            hypotenuse = _int_sqrt(leg * leg + other * other)
            if hypotenuse is None:
                continue
            for base, height in ((leg, other), (other, leg)):
                if _forward_options_agree(base, height, height, hypotenuse):
                    found.append((base, height, hypotenuse))
    return found


def _reverse_triangles() -> list[tuple[int, int, int]]:
    """`(base, height, side CA)` where every reverse answer is a whole number.

    The reverse rung divides, so the constraints are divisibility ones: the side
    has to divide `base·height` for `confuses_base_with_height` to land on a
    whole number, and the base has to be even for the halving-skipped Trap to.
    """
    found: list[tuple[int, int, int]] = []
    for height in range(4, _MAX_HEIGHT + 1, 2):
        for side in range(height + 1, 30):
            foot = math.sqrt(side * side - height * height)
            for base in range(4, _MAX_BASE + 3, 2):
                if foot > base or side in (base, height) or (base * height) % side:
                    continue
                area = base * height // 2
                if area > _MAX_AREA or area % base or area % height:
                    continue
                if not _distinct(2 * area // base, area // base, 2 * area // side):
                    continue
                if not _distinct(
                    2 * area // height, area // height, base * height // side
                ):
                    continue
                found.append((base, height, side))
    return found


ACUTE = _acute_triangles()
OBTUSE = _obtuse_triangles()
RIGHT = _right_triangles()
REVERSE = _reverse_triangles()


def _area_problem(
    q_str: str,
    svg: str,
    *,
    base: int,
    height: int,
    sides: tuple[int, ...],
    side_as_height: int,
    unit: str,
    parameters: dict,
) -> dict | None:
    """Assemble one forward Problem — figure in, area out — with the three Traps."""
    area = base * height // 2
    return build_problem_dict(
        q_str,
        str(area),
        traps={
            TRAP_DOUBLES: str(base * height),
            TRAP_PERIMETER: str(base + sum(sides)),
            TRAP_SIDE_AS_HEIGHT: str(base * side_as_height // 2),
        },
        parameters=parameters,
        image_html=svg,
        expected_unit=unit,
    )


_FORWARD_QUESTION = r"\text{Oblicz pole trójkąta.}"


@declares_units(*AREA_UNITS)
@declares_traps(TRAP_DOUBLES, TRAP_PERIMETER, TRAP_SIDE_AS_HEIGHT)
def geo_triangle_area_1() -> dict | None:
    """Wysokość narysowana wewnątrz trójkąta (poziom 1)."""
    unit = random.choice(declared_units(geo_triangle_area_1))
    length_unit = _LENGTH_FOR_AREA[unit]
    base, height, side_a, side_b = random.choice(ACUTE)
    foot = math.sqrt(side_a * side_a - height * height)

    figure = Triangle.base_height(base, height, apex_frac=foot / base)
    svg = Scene(
        figure,
        [
            Outline(),
            VertexLabels(),
            EdgeLabel("AB", length_unit),
            EdgeLabel("BC", length_unit),
            EdgeLabel("CA", length_unit),
            Altitude(apex="C", base="AB", unit_label=length_unit),
        ],
    ).to_svg()

    side_as_height = _side_read_as_height(base, side_a, side_b)
    assert side_as_height is not None  # the pool only admits triangles where it is
    return _area_problem(
        _FORWARD_QUESTION,
        svg,
        base=base,
        height=height,
        sides=(side_a, side_b),
        side_as_height=side_as_height,
        unit=unit,
        parameters={
            "base": base,
            "height": height,
            "side_a": side_a,
            "side_b": side_b,
            "unit": length_unit,
        },
    )


@declares_units(*AREA_UNITS)
@declares_traps(TRAP_DOUBLES, TRAP_PERIMETER, TRAP_SIDE_AS_HEIGHT)
def geo_triangle_area_2() -> dict | None:
    """Trójkąt prostokątny — wysokość jest bokiem (poziom 2)."""
    unit = random.choice(declared_units(geo_triangle_area_2))
    length_unit = _LENGTH_FOR_AREA[unit]
    base, height, hypotenuse = random.choice(RIGHT)

    # apex_frac 0 stands the height on vertex A, so the height IS side CA.
    figure = Triangle.base_height(base, height, apex_frac=0.0)
    svg = Scene(
        figure,
        [
            Outline(),
            VertexLabels(),
            RightAngle("A"),
            EdgeLabel("AB", length_unit),
            EdgeLabel("CA", length_unit),
            EdgeLabel("BC", length_unit),
        ],
    ).to_svg()

    return _area_problem(
        _FORWARD_QUESTION,
        svg,
        base=base,
        height=height,
        sides=(height, hypotenuse),
        side_as_height=_side_read_as_height(base, height, hypotenuse) or hypotenuse,
        unit=unit,
        parameters={
            "base": base,
            "height": height,
            "hypotenuse": hypotenuse,
            "unit": length_unit,
        },
    )


@declares_units(*AREA_UNITS)
@declares_traps(TRAP_DOUBLES, TRAP_PERIMETER, TRAP_SIDE_AS_HEIGHT)
def geo_triangle_area_3() -> dict | None:
    """Wysokość wypada poza trójkątem rozwartokątnym (poziom 3)."""
    unit = random.choice(declared_units(geo_triangle_area_3))
    length_unit = _LENGTH_FOR_AREA[unit]
    base, height, offset, side_a, side_b = random.choice(OBTUSE)

    figure = Triangle.base_height(base, height, apex_frac=-offset / base)
    svg = Scene(
        figure,
        [
            Outline(),
            VertexLabels(),
            EdgeLabel("AB", length_unit),
            EdgeLabel("BC", length_unit),
            EdgeLabel("CA", length_unit),
            Altitude(apex="C", base="AB", unit_label=length_unit),
        ],
    ).to_svg()

    side_as_height = _side_read_as_height(base, side_a, side_b)
    assert side_as_height is not None
    return _area_problem(
        _FORWARD_QUESTION,
        svg,
        base=base,
        height=height,
        sides=(side_a, side_b),
        side_as_height=side_as_height,
        unit=unit,
        parameters={
            "base": base,
            "height": height,
            "side_a": side_a,
            "side_b": side_b,
            "unit": length_unit,
        },
    )


@declares_units(*LENGTH_UNITS)
@declares_traps(TRAP_DOUBLES, TRAP_SIDE_AS_HEIGHT)
def geo_triangle_area_4() -> dict | None:
    """Szukana podstawa lub wysokość, gdy dane jest pole (poziom 4)."""
    unit = random.choice(declared_units(geo_triangle_area_4))
    base, height, side = random.choice(REVERSE)
    area = base * height // 2
    # Which dimension is withheld is drawn per Problem: fixing it would make the
    # rung solvable by dividing whatever number is on the page, without looking.
    height_unknown = random.random() < 0.5

    figure = Triangle.base_height(
        base, height, apex_frac=math.sqrt(side * side - height * height) / base
    )
    svg = Scene(
        figure,
        [
            Outline(),
            VertexLabels(),
            EdgeLabel("AB", unit, unknown=not height_unknown),
            EdgeLabel("CA", unit),
            Altitude(apex="C", base="AB", unit_label=unit, unknown=height_unknown),
        ],
    ).to_svg()

    given = base if height_unknown else height
    answer = 2 * area // given
    q_str = (
        rf"\text{{Pole trójkąta wynosi }} {area}\ \text{{{unit}}}^2"
        rf"\text{{. Oblicz }} x \text{{.}}"
    )

    return build_problem_dict(
        q_str,
        str(answer),
        traps={
            # The same belief as on the forward rungs, mirrored: dividing by the
            # base without also doubling is `b·h` read backwards.
            TRAP_DOUBLES: str(area // given),
            TRAP_SIDE_AS_HEIGHT: str(base * height // side),
        },
        fillers=[str(answer + 1)],
        parameters={
            "area": area,
            "base": base,
            "height": height,
            "side": side,
            "height_unknown": height_unknown,
            "unit": unit,
        },
        image_html=svg,
        expected_unit=unit,
    )
