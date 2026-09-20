"""`frac_pow_1` and `frac_pow_2`'s `multiplies_by_the_exponent` Trap must multiply
only the numerator by the exponent (#273).

Multiplying both parts is an equivalent fraction, and the display simplifies it
back down to the question's own fraction — so a Student who picked the Trap saw
feedback that did not match what they clicked, and every draw offered the
question's fraction as one of its own options.
"""

from backend.core.utils import format_answers
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 200


def test_frac_pow_1_trap_multiplies_only_the_numerator():
    generator = FUNCTION_REGISTRY["frac_pow_1"]

    emitted = 0
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        emitted += 1

        n, d, p = (
            problem["parameters"]["n"],
            problem["parameters"]["d"],
            problem["parameters"]["p"],
        )
        question_fraction, _ = format_answers(n, d)
        expected_trap, _ = format_answers(n * p, d)

        assert problem["options_map"].get(expected_trap) == "multiplies_by_the_exponent"
        # Multiplying both parts always reduced back to the question's own
        # fraction; multiplying only the numerator must not.
        assert expected_trap != question_fraction

    assert emitted


def test_frac_pow_2_trap_multiplies_only_the_numerator():
    generator = FUNCTION_REGISTRY["frac_pow_2"]

    emitted = 0
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        emitted += 1

        n, d, p = (
            problem["parameters"]["n"],
            problem["parameters"]["d"],
            problem["parameters"]["p"],
        )
        question_fraction, _ = format_answers(n, d)
        expected_trap, _ = format_answers(n * p, d)

        assert problem["options_map"].get(expected_trap) == "multiplies_by_the_exponent"
        assert expected_trap != question_fraction

    assert emitted


def test_frac_pow_2_can_draw_a_unit_fraction_cube():
    """Level 2 previously discarded every unit-fraction draw (n=1) because the old
    Trap formula collided with `raises_only_the_numerator` — the pool was 6 rather
    than 10. It should reach n=1 now."""
    generator = FUNCTION_REGISTRY["frac_pow_2"]

    seen_unit_fraction = False
    for _ in range(500):
        problem = generator()
        if problem is None:
            continue
        if problem["parameters"]["n"] == 1:
            seen_unit_fraction = True
            break

    assert seen_unit_fraction
