# No answer option may carry raw binary-float noise (e.g. `0,4800000000000001`).
#
# `fmt_dec` (backend/core/utils.py) formats a Decimal built from `str(val)` exactly and
# never rounds, so any generator that does its display-critical arithmetic in `float`
# rather than `Decimal`/`Fraction` leaks IEEE-754 artefacts straight into an answer
# option a child sees. See issue #234.
#
# No Level in this curriculum legitimately needs more than a handful of fractional
# digits (the deepest intentional rounding call is 6 places, in `dec_comma_2`), so a
# fractional part past ``MAX_LEGITIMATE_DECIMAL_PLACES`` digits is unambiguously float
# noise rather than a genuinely long answer — the gap between "clean" and "leaking" is
# wide (float noise runs to 15-17 digits), so this bound never fights a real Level.
import re

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 600
MAX_LEGITIMATE_DECIMAL_PLACES = 10

# A decimal option looks like `-12,345` (Polish comma) — possibly embedded in a
# LaTeX fraction's numerator/denominator too, so scan for the bare pattern anywhere.
_DECIMAL_RE = re.compile(r"-?\d+,(\d+)")


def _dirty_options(generator) -> set[str]:
    dirty: set[str] = set()
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        for option in problem["options_map"]:
            for match in _DECIMAL_RE.finditer(option):
                if len(match.group(1)) > MAX_LEGITIMATE_DECIMAL_PLACES:
                    dirty.add(option)
    return dirty


@pytest.mark.parametrize("name", sorted(FUNCTION_REGISTRY))
def test_no_option_carries_float_artefacts(name):
    generator = FUNCTION_REGISTRY[name]
    dirty = _dirty_options(generator)
    assert not dirty, (
        f"{name} produced option(s) with implausibly long decimal tails "
        f"(binary-float noise): {sorted(dirty)}"
    )
