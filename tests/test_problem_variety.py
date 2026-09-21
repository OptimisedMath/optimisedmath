"""Every generator must actually draw more than a handful of distinct problems.

`frac_div_frac_2` and `frac_mult_2` seeded a rejection-sampling loop with a pair
that already satisfied the loop condition, so the body never ran (#226).
`frac_ord_3` assigned literal Fractions instead of drawing random operands, so
the Level had exactly 2 problems, forever (#231/A2). None of that is visible to
`test_parameter_variety.py`, which only checks integer `parameters` values —
`frac_ord_3`'s parameters are formatted Fraction strings.

So: sweep every generator, draw it N times, and require a floor on the number
of distinct `parameters` tuples seen. This is a regression tripwire, not a
pedagogy check — it asks whether randomisation broke, not whether a Level has
enough Problems to be good practice. Number-line Levels are skipped — their
`question` is a constant string and the variation lives in the rendered SVG, so
they would always measure as 1 distinct tuple.

The floor started at 5, which was too low to be a guard at all: `dec_mult_3` drew
its operands from two four-item lists, so the Level was 16 Problems forever, and
this test passed it (#233). A floor has to sit above the pool sizes it is meant
to catch.

Raising the floor to 20 (#233) put three generators below it. Rather than skip
them — which hides them from any variety check at all, not even the old floor —
each is named in `VARIETY_EXEMPTIONS` with its actual pool size and a one-line
reason its pool is the Level's design, not a defect, following the
`STRUCTURALLY_CONSTANT` idiom in `test_parameter_variety.py`. Each still runs
the sweep, against its own recorded pool instead of `MIN_DISTINCT`, and each
reason names the issue that owns widening or retiring the exemption. An entry
leaves only once its generator's pool is widened past `MIN_DISTINCT`, never by
lowering `MIN_DISTINCT` to meet it (#274 widened `frac_ord_5` this way).
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 300
MIN_DISTINCT = 20

NUMBER_LINE_GENERATORS = {name for name in FUNCTION_REGISTRY if "number_line" in name}

# (pool size, reason) for generators whose distinct-parameters pool sits below
# MIN_DISTINCT by design rather than by defect. Each reason names the issue
# that owns widening or retiring the exemption.
VARIETY_EXEMPTIONS = {
    "frac_pow_2": (
        10,
        "the denominator cap (d = 2..5) keeps cube denominators small for "
        "this Level. Tracked as #263.",
    ),
    "frac_pow_3": (
        18,
        "the whole-part range keeps the improper numerator inside a "
        "Student's cube range; widening it to three would make the largest "
        "cube 11 cubed, which is not a times-table fact at this Level. "
        "Tracked as #263.",
    ),
    "dec_pow_1": (
        8,
        "the draw is eight one-digit tenths by construction. Tracked as #264.",
    ),
}


def _parameters_key(parameters: dict) -> tuple:
    return tuple(sorted(parameters.items()))


@pytest.mark.parametrize(
    "name", sorted(set(FUNCTION_REGISTRY) - NUMBER_LINE_GENERATORS)
)
def test_generator_draws_varied_problems(name):
    generator = FUNCTION_REGISTRY[name]
    pool, reason = VARIETY_EXEMPTIONS.get(name, (MIN_DISTINCT, None))

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

    floor = min(pool, emitted)
    detail = f" (exempt: {reason})" if reason else ""
    assert len(seen) >= floor, (
        f"{name} only drew {len(seen)} distinct problem(s) across {emitted} "
        f"Problems (expected at least {floor}){detail}"
    )
