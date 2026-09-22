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
# only the figure changes. Levels 2 and 3 each label a length that is neither
# the base nor the height, because without one `confuses_base_with_height` and
# `computes_the_perimeter_instead_of_the_area` have nothing to fire on — Level 1
# has no such length, so neither Trap is reachable there (#294).

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

# Level 1's base and height are the only lengths it prints, so they are the only
# thing to bound — small enough to multiply in the head (#294).
_LEVEL_1_MIN_DIM = 3
_LEVEL_1_MAX_DIM = 12


def _int_sqrt(n: int) -> int | None:
    """The integer square root of `n`, or None when `n` is not a perfect square."""
    root = math.isqrt(n)
    return root if root * root == n else None


def _distinct(*values: int) -> bool:
    """Whether every option value differs — a collision would cost a Trap its slot."""
    return len(set(values)) == len(values)


def _side_read_as_height(side_a: int, side_b: int) -> int:
    """The labelled side a Student is likeliest to multiply by instead of the height.

    The longer side, which is the one the dashed altitude runs nearest to.
    """
    return max(side_a, side_b)


def _small_base_heights() -> list[tuple[int, int]]:
    """`(base, height)` pairs whose area is a whole number, for Level 1 (#294).

    Level 1 draws no slant side, so nothing forces the altitude's feet to be
    legs of a Pythagorean triple — only the area needs to land on a whole
    number, which leaves the pool free to stay small.
    """
    return [
        (base, height)
        for base in range(_LEVEL_1_MIN_DIM, _LEVEL_1_MAX_DIM + 1)
        for height in range(_LEVEL_1_MIN_DIM, _LEVEL_1_MAX_DIM + 1)
        if not (base * height) % 2
    ]


def _obtuse_triangles() -> list[tuple[int, int, int, int, int]]:
    """`(base, height, foot offset, side CA, side BC)` with the foot off the base.

    Every printed length must be a whole number, so both feet of the altitude
    have to be legs of Pythagorean triples on the same height — but here the
    apex hangs beyond vertex A, so the far foot is `offset + base` rather than
    `base - offset`.
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


SMALL_BASE_HEIGHTS = _small_base_heights()
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
@declares_traps(TRAP_DOUBLES)
def geo_triangle_area_1() -> dict | None:
    """Wysokość narysowana wewnątrz trójkąta (poziom 1)."""
    unit = random.choice(declared_units(geo_triangle_area_1))
    length_unit = _LENGTH_FOR_AREA[unit]
    base, height = random.choice(SMALL_BASE_HEIGHTS)

    # No printed slant side means the apex is free to sit anywhere (#294); the
    # range keeps the altitude's foot well inside the base, which is the rung.
    figure = Triangle.base_height(base, height, apex_frac=random.uniform(0.3, 0.7))
    svg = Scene(
        figure,
        [
            Outline(),
            VertexLabels(),
            Altitude(apex="C", base="AB", unit_label=length_unit),
        ],
    ).to_svg()

    return build_problem_dict(
        _FORWARD_QUESTION,
        str(base * height // 2),
        traps={TRAP_DOUBLES: str(base * height)},
        parameters={"base": base, "height": height, "unit": length_unit},
        image_html=svg,
        expected_unit=unit,
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
        side_as_height=_side_read_as_height(height, hypotenuse),
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

    side_as_height = _side_read_as_height(side_a, side_b)
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
    edge_ab = EdgeLabel("AB", unit, unknown=not height_unknown)
    altitude = Altitude(apex="C", base="AB", unit_label=unit, unknown=height_unknown)
    svg = Scene(
        figure,
        [Outline(), VertexLabels(), edge_ab, EdgeLabel("CA", unit), altitude],
    ).to_svg()

    given = base if height_unknown else height
    answer = 2 * area // given
    # The figure claims its own symbol as it renders; read it back rather than
    # naming the letter again, so the prose and the figure cannot disagree (#293).
    symbol = altitude.unknown_text if height_unknown else edge_ab.unknown_text
    q_str = (
        rf"\text{{Pole trójkąta wynosi }} {area}\ \text{{{unit}}}^2"
        rf"\text{{. Oblicz }} {symbol} \text{{.}}"
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
