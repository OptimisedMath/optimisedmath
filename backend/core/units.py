"""The Unit table, and the split of a typed answer into number and Unit.

Deliberately separate from `parse_to_fraction`: that parser is shared by every
Chapter, and teaching it to swallow a trailing word would make `"5 kotów"` parse
as `5` everywhere (ADR-0005). Splitting happens *above* it, and only where a
Level declares `expected_units`.
"""

from __future__ import annotations

import re
from fractions import Fraction

LENGTH = "length"
AREA = "area"

#: Unit -> (dimension, factor to that dimension's base unit — mm or mm²).
#: Factors are integers, so conversion is exact and `0,0024 m²` compares equal
#: to `24 cm²` rather than nearly equal.
UNITS: dict[str, tuple[str, Fraction]] = {
    "mm": (LENGTH, Fraction(1)),
    "cm": (LENGTH, Fraction(10)),
    "dm": (LENGTH, Fraction(100)),
    "m": (LENGTH, Fraction(1_000)),
    "km": (LENGTH, Fraction(1_000_000)),
    "mm²": (AREA, Fraction(1)),
    "cm²": (AREA, Fraction(100)),
    "dm²": (AREA, Fraction(10_000)),
    "m²": (AREA, Fraction(1_000_000)),
    "a": (AREA, Fraction(100_000_000)),
    "ha": (AREA, Fraction(10_000_000_000)),
    "km²": (AREA, Fraction(1_000_000_000_000)),
}

# A Unit is a trailing run of letters plus an optional square marker. The square
# marker has to be part of the token — `m2` is one Unit, not `m` after the number
# `2` — which is why the split cannot simply strip trailing non-digits.
_SPLIT = re.compile(r"^(.*?)\s*([^\W\d_]+(?:\s*(?:²|\^?2|\*\*2))?)\s*$")

_SQUARE_MARKERS = ("²", "2", "^2", "**2")


def normalize_unit(raw: str) -> str | None:
    """Return the catalogue form of a typed Unit, or None if it is not a Unit.

    Case- and whitespace-insensitive, and `cm2` / `cm^2` / `CM²` all land on `cm²`:
    a phone keyboard has no `²`, so demanding one would penalize the device.
    """
    text = raw.strip().lower().replace(" ", "")
    if text in UNITS:
        return text
    for marker in _SQUARE_MARKERS:
        if marker != "²" and text.endswith(marker):
            candidate = text[: -len(marker)] + "²"
            if candidate in UNITS:
                return candidate
    return None


def split_answer(text: str) -> tuple[str, str | None]:
    """Split a typed answer into its numeric text and its raw trailing Unit.

    Returns the Unit as typed, not normalized — an unrecognised trailing word is
    returned rather than discarded, so the grader can tell *no Unit given* from
    *a Unit that is not a Unit*. Both are Wrong, but only the first is silence.
    """
    match = _SPLIT.match(text.strip())
    if match is None:
        return text.strip(), None
    number, unit = match.group(1).strip(), match.group(2).strip()
    if not number:
        return text.strip(), None
    return number, unit


def dimension_of(unit: str) -> str | None:
    """The dimension a normalized Unit measures, or None if it is not in the table."""
    entry = UNITS.get(unit)
    return entry[0] if entry else None


def convert(value: Fraction, frm: str, to: str) -> Fraction | None:
    """Convert a magnitude between two same-dimension Units; None across dimensions.

    There is no factor between `cm` and `cm²`, so a wrong dimension can never
    convert to right — which is what lets the grader treat conversion as
    resolving Correct *before* any Trap is considered (ADR-0005).
    """
    source, target = UNITS.get(frm), UNITS.get(to)
    if source is None or target is None or source[0] != target[0]:
        return None
    return value * source[1] / target[1]
