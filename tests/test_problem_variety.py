"""Every generator must actually draw more than a handful of distinct problems.

`frac_div_frac_2` and `frac_mult_2` seeded a rejection-sampling loop with a pair
that already satisfied the loop condition, so the body never ran (#226).
`frac_ord_3` assigned literal Fractions instead of drawing random operands, so
the Level had exactly 2 problems, forever (#231/A2). None of that is visible to
`test_parameter_variety.py`, which only checks integer `parameters` values —
`frac_ord_3`'s parameters are formatted Fraction strings.

So: sweep every generator, draw it N times, and require a floor on the number
of distinct `parameters` tuples seen. Number-line Levels are skipped — their
`question` is a constant string and the variation lives in the rendered SVG, so
they would always measure as 1 distinct tuple.
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 300
MIN_DISTINCT = 5

NUMBER_LINE_GENERATORS = {name for name in FUNCTION_REGISTRY if "number_line" in name}


def _parameters_key(parameters: dict) -> tuple:
    return tuple(sorted(parameters.items()))


@pytest.mark.parametrize(
    "name", sorted(set(FUNCTION_REGISTRY) - NUMBER_LINE_GENERATORS)
)
def test_generator_draws_varied_problems(name):
    generator = FUNCTION_REGISTRY[name]

    seen = set()
    emitted = 0
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        emitted += 1
        seen.add(_parameters_key(problem["parameters"]))

    if not emitted:
        pytest.skip(f"{name} emitted no Problem in {ROLLS} rolls")

    floor = min(MIN_DISTINCT, emitted)
    assert len(seen) >= floor, (
        f"{name} only drew {len(seen)} distinct problem(s) across {emitted} "
        f"Problems (expected at least {floor})"
    )
