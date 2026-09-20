"""`frac_pow_1` and `frac_pow_2`'s `multiplies_by_the_exponent` Trap must multiply
only the numerator by the exponent (#273).

Multiplying both parts is an equivalent fraction, and the display simplifies it
back down to the question's own fraction — so a Student who picked the Trap saw
feedback that did not match what they clicked, and every draw offered the
question's fraction as one of its own options.

A generator draws its numbers at random, so no single call proves the guarantee —
the same sweep shape as `test_trap_slugs.py`. Running each generator many times does.
"""

import pytest

from backend.core.utils import format_answers
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 200


@pytest.mark.parametrize("name", ["frac_pow_1", "frac_pow_2"])
def test_frac_pow_trap_multiplies_only_the_numerator(name):
    """The Trap is n*p over d, and so is never the fraction the question printed."""
    generator = FUNCTION_REGISTRY[name]

    emitted = 0
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        emitted += 1

        parameters = problem["parameters"]
        n, d, p = parameters["n"], parameters["d"], parameters["p"]
        question_fraction, _ = format_answers(n, d)
        expected_trap, _ = format_answers(n * p, d)

        assert (
            problem["options_map"].get(expected_trap) == "multiplies_by_the_exponent"
        ), f"{name} did not offer {expected_trap!r} as the Trap for ({n}/{d})^{p}"
        # Multiplying both parts always reduced back to the question's own
        # fraction; multiplying only the numerator must not.
        assert (
            expected_trap != question_fraction
        ), f"{name} offered the question's own fraction {question_fraction!r} as a Trap"

    assert emitted, f"{name} emitted no Problem in {ROLLS} rolls"


def test_frac_pow_2_draws_a_unit_fraction_to_cube():
    """Level 2 reaches n=1, which the old Trap formula collided away (#273).

    Multiplying both parts gave 3n/3d, which reduced to n/d and so equalled the
    `raises_only_the_numerator` Trap on every unit-fraction draw; the colliding
    options were discarded, leaving the Level a pool of 6 rather than 10.
    """
    generator = FUNCTION_REGISTRY["frac_pow_2"]

    numerators = set()
    for _ in range(ROLLS):
        problem = generator()
        if problem is not None:
            numerators.add(problem["parameters"]["n"])

    assert 1 in numerators, f"frac_pow_2 drew no unit fraction in {ROLLS} rolls"
