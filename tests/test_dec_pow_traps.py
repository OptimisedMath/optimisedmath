"""`Ułamki Dziesiętne, Potęgowanie` grows from one Level to four (#264).

`dec_pow_2`, `dec_pow_3`, `dec_pow_4` are new; `dec_pow_1`'s
`ignores_the_point_before_squaring` Trap is renamed to
`ignores_the_point_before_powering` because the same Trap now also runs on
`dec_pow_4`'s cube.

L3 and L4 must compute in `Decimal`, not floats: `0.015 ** 2` is
`0.00022500000000000002` as a float, and `fmt_dec` formats exactly what it is
handed, so a float slip would leak digits into an option string.
"""

from decimal import Decimal

import pytest

from backend.core.utils import FILLER_SLUG, declared_trap_slugs, fmt_dec
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 300


def _draws(name: str) -> list[dict]:
    rolls = (FUNCTION_REGISTRY[name]() for _ in range(ROLLS))
    return [problem for problem in rolls if problem is not None]


def test_dec_pow_1_trap_renamed():
    """`ignores_the_point_before_squaring` no longer exists; the Trap runs under the new name."""
    declared = declared_trap_slugs(FUNCTION_REGISTRY["dec_pow_1"])
    assert "ignores_the_point_before_powering" in declared
    assert "ignores_the_point_before_squaring" not in declared


def test_dec_pow_2_draws_one_decimal_between_1_and_2():
    problems = _draws("dec_pow_2")
    assert problems, "dec_pow_2 emitted no Problem in ROLLS rolls"

    values = {problem["parameters"]["v"] for problem in problems}
    assert values, "dec_pow_2 drew no values"
    for v in values:
        assert 1.1 <= v <= 1.9
        assert round(v, 1) == v


def test_dec_pow_2_trap_formulas():
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


def test_dec_pow_3_draws_documented_bases_and_scales():
    problems = _draws("dec_pow_3")
    assert problems, "dec_pow_3 emitted no Problem in ROLLS rolls"

    bases = {problem["parameters"]["b"] for problem in problems}
    scales = {problem["parameters"]["k"] for problem in problems}
    assert bases <= {2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 25}
    assert scales <= {2, 3}


def test_dec_pow_3_trap_formulas_are_exact_decimal():
    for problem in _draws("dec_pow_3"):
        b, k = problem["parameters"]["b"], problem["parameters"]["k"]
        v = Decimal(b) / (Decimal(10) ** k)
        options_map = problem["options_map"]

        assert problem["correct"] == fmt_dec(v**2)
        assert options_map.get(fmt_dec(v * 2)) == "multiplies_by_the_exponent"
        assert options_map.get(fmt_dec(b**2)) == "ignores_the_point_before_powering"
        # Never a float artefact: no option string exceeds the exact answer's
        # own decimal places.
        for option in problem["options"]:
            assert "e" not in option.lower()


def test_dec_pow_3_worked_example_from_the_issue():
    """(0,015)^2 = 0,000225, against 0,03, 225, 0,225 — the issue's own table."""
    b, k = 15, 3
    v = Decimal(b) / (Decimal(10) ** k)
    assert fmt_dec(v**2) == "0,000225"
    assert fmt_dec(v * 2) == "0,03"
    assert fmt_dec(b**2) == "225"
    assert fmt_dec(Decimal(b**2) / (Decimal(10) ** k)) == "0,225"


def test_dec_pow_3_b_equals_2_collision_falls_back_to_filler():
    """`multiplies_by_the_exponent` (2b) and `keeps_the_operands_decimal_places` (b^2)
    collide in value whenever b=2; the later-declared Trap loses its slot to a Filler.
    """
    b2_problems = [p for p in _draws("dec_pow_3") if p["parameters"]["b"] == 2]
    assert b2_problems, "dec_pow_3 drew no b=2 problem in ROLLS rolls"

    for problem in b2_problems:
        k = problem["parameters"]["k"]
        trap_value = fmt_dec(Decimal(2) / (Decimal(10) ** k) * 2)
        assert problem["options_map"].get(trap_value) == "multiplies_by_the_exponent"
        assert (
            "keeps_the_operands_decimal_places" not in problem["options_map"].values()
        )


def test_dec_pow_4_draws_documented_bases_and_scales():
    problems = _draws("dec_pow_4")
    assert problems, "dec_pow_4 emitted no Problem in ROLLS rolls"

    bases = {problem["parameters"]["b"] for problem in problems}
    scales = {problem["parameters"]["k"] for problem in problems}
    assert bases <= {2, 3, 4, 5}
    assert scales <= {1, 2}


def test_dec_pow_4_worked_example_from_the_issue():
    """(0,05)^3 = 0,000125, against 0,15, 125, 1,25 — the issue's own table."""
    b, k = 5, 2
    v = Decimal(b) / (Decimal(10) ** k)
    assert fmt_dec(v**3) == "0,000125"
    assert fmt_dec(v * 3) == "0,15"
    assert fmt_dec(b**3) == "125"
    assert fmt_dec(Decimal(b**3) / (Decimal(10) ** k)) == "1,25"


def test_dec_pow_4_trap_formulas_are_exact_decimal():
    for problem in _draws("dec_pow_4"):
        b, k = problem["parameters"]["b"], problem["parameters"]["k"]
        v = Decimal(b) / (Decimal(10) ** k)
        options_map = problem["options_map"]

        assert problem["correct"] == fmt_dec(v**3)
        assert options_map.get(fmt_dec(v * 3)) == "multiplies_by_the_exponent"
        assert options_map.get(fmt_dec(b**3)) == "ignores_the_point_before_powering"


@pytest.mark.parametrize("name", ["dec_pow_2", "dec_pow_3", "dec_pow_4"])
def test_no_generator_passes_an_explicit_filler_list(name):
    """Per the issue's amendment (#272/ADR-0009), no generator authors `fillers=`.

    Every draw still serves four distinct options, via the shared Filler rule.
    """
    for problem in _draws(name):
        assert len(problem["options"]) == 4
