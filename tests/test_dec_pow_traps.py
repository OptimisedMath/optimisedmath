"""`Ułamki Dziesiętne, Potęgowanie` grows from one Level to four (#264).

`dec_pow_2`, `dec_pow_3`, `dec_pow_4` are new; `dec_pow_1`'s
`ignores_the_point_before_squaring` Trap is renamed to
`ignores_the_point_before_powering` because the same Trap now also runs on
`dec_pow_4`'s cube. The rename needs no test here — `test_trap_slugs.py` holds
every generator's declaration to exactly what it emits, and the loader refuses a
Level whose authored `traps` and declared slugs disagree, so the old slug cannot
survive in either place.

L3 and L4 must compute in `Decimal`, not floats: `0.015 ** 2` is
`0.00022500000000000002` as a float, and `fmt_dec` formats exactly what it is
handed, so a float slip would leak digits into an option string. Every
expectation here is therefore built from `Decimal` locally rather than from the
generator's own helper, so a float creeping into the generator fails the assert
instead of travelling into it.

That each new Level still serves four distinct options without authoring its own
`fillers=` (ADR-0009) needs no test here — `test_filler_rule.py` sweeps every
generator in the registry for both.
"""

from decimal import Decimal

from backend.core.utils import fmt_dec
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 300


def _draws(name: str) -> list[dict]:
    """Every Problem `name` emits over `ROLLS` rolls."""
    rolls = (FUNCTION_REGISTRY[name]() for _ in range(ROLLS))
    return [problem for problem in rolls if problem is not None]


def _exact(digits: int, places: int) -> Decimal:
    """`digits` with the decimal point moved `places` to the left, exactly."""
    return Decimal(digits) / (Decimal(10) ** places)


def _places(value: Decimal) -> int:
    """How many digits `value` carries after the decimal point."""
    return -value.as_tuple().exponent


def test_dec_pow_2_draws_one_decimal_between_1_and_2():
    """Every L2 draw is a one-decimal value from 1,1 to 1,9."""
    problems = _draws("dec_pow_2")
    assert problems, "dec_pow_2 emitted no Problem in ROLLS rolls"

    for v in {problem["parameters"]["v"] for problem in problems}:
        assert 1.1 <= v <= 1.9
        assert round(v, 1) == v


def test_dec_pow_2_trap_formulas():
    """Each L2 Trap models the error its slug names, and the answer is the square."""
    for problem in _draws("dec_pow_2"):
        v = problem["parameters"]["v"]
        options_map = problem["options_map"]

        assert problem["correct"] == fmt_dec(round(v**2, 2))
        assert options_map.get(fmt_dec(round(v * 2, 1))) == "multiplies_by_the_exponent"
        assert (
            options_map.get(fmt_dec(round(v * 10) ** 2))
            == "ignores_the_point_before_powering"
        )
        assert (
            options_map.get(fmt_dec(round(v**2 + 0.01, 2))) == "one_hundredth_too_large"
        )


def test_dec_pow_3_squares_a_decimal_finer_than_the_earlier_levels():
    """L3 is "mały ułamek" squared: below 1, and finer than L1 and L2's single place.

    The band is the point, not the base roster — restating the generator's own
    `random.choice` list would only fail when someone edits it. Two or three
    places is what makes the square land in the ten-thousandths or below, which
    is the error this Level's Traps are built to catch.
    """
    problems = _draws("dec_pow_3")
    assert problems, "dec_pow_3 emitted no Problem in ROLLS rolls"

    for problem in problems:
        v = _exact(problem["parameters"]["b"], problem["parameters"]["k"])
        assert 0 < v < 1
        assert 2 <= _places(v) <= 3
        assert "^2" in problem["question"]


def test_dec_pow_3_trap_formulas_are_exact_decimal():
    """Each L3 Trap and the answer carry the exact Decimal value, with no float tail."""
    for problem in _draws("dec_pow_3"):
        b, k = problem["parameters"]["b"], problem["parameters"]["k"]
        v = _exact(b, k)
        options_map = problem["options_map"]

        assert problem["correct"] == fmt_dec(v**2)
        assert options_map.get(fmt_dec(v * 2)) == "multiplies_by_the_exponent"
        assert options_map.get(fmt_dec(b**2)) == "ignores_the_point_before_powering"
        if b != 2:  # b=2 collides — its own test below
            assert (
                options_map.get(fmt_dec(_exact(b**2, k)))
                == "keeps_the_operands_decimal_places"
            )


def test_dec_pow_3_b_equals_2_collision_falls_back_to_filler():
    """At b=2 `keeps_the_operands_decimal_places` loses its slot, because 2b equals b^2."""
    b2_problems = [p for p in _draws("dec_pow_3") if p["parameters"]["b"] == 2]
    assert b2_problems, "dec_pow_3 drew no b=2 problem in ROLLS rolls"

    for problem in b2_problems:
        k = problem["parameters"]["k"]
        options_map = problem["options_map"]
        assert (
            options_map.get(fmt_dec(_exact(2, k) * 2)) == "multiplies_by_the_exponent"
        )
        assert "keeps_the_operands_decimal_places" not in options_map.values()


def test_dec_pow_4_cubes_a_base_coarse_enough_to_stay_readable():
    """L4 is the cube, on a base of one or two places so the answer stays readable.

    Cubing triples the decimal places, so the coarser base is deliberate: three
    places in would put the answer at nine places out. Asserting that band says
    why the Level draws as it does; listing its bases would not.
    """
    problems = _draws("dec_pow_4")
    assert problems, "dec_pow_4 emitted no Problem in ROLLS rolls"

    for problem in problems:
        v = _exact(problem["parameters"]["b"], problem["parameters"]["k"])
        assert 0 < v < 1
        assert 1 <= _places(v) <= 2
        assert "^3" in problem["question"]


def test_dec_pow_4_trap_formulas_are_exact_decimal():
    """Each L4 Trap and the answer carry the exact Decimal value, with no float tail."""
    for problem in _draws("dec_pow_4"):
        b, k = problem["parameters"]["b"], problem["parameters"]["k"]
        v = _exact(b, k)
        options_map = problem["options_map"]

        assert problem["correct"] == fmt_dec(v**3)
        assert options_map.get(fmt_dec(v * 3)) == "multiplies_by_the_exponent"
        assert options_map.get(fmt_dec(b**3)) == "ignores_the_point_before_powering"
        assert (
            options_map.get(fmt_dec(_exact(b**3, k)))
            == "keeps_the_operands_decimal_places"
        )
