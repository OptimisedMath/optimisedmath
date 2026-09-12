"""Every Kolejność wykonywania działań generator's `expression` parameter must parse
and evaluate to the Problem's own answer.

A generator picks its template with `random.choice`, so no single call fires every
branch — the same sweep shape as `test_trap_slugs.py`. Running each of the twelve
generators (six per Chapter, #245) many times does: wrong precedence, wrong
associativity, or a drifted decimal all surface as a mismatch, on any template.
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from backend import expression
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500

KOLEJNOSC_GENERATORS = sorted(name for name in FUNCTION_REGISTRY if "ord" in name)


def _answer_as_fraction(correct: str) -> Fraction:
    if "," in correct:
        return Fraction(Decimal(correct.replace(",", ".")))
    return Fraction(correct)


@pytest.mark.parametrize("name", KOLEJNOSC_GENERATORS)
def test_expression_parameter_evaluates_to_the_problem_answer(name):
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        assert (
            "expression" in problem["parameters"]
        ), f"{name} emitted a Problem with no `expression` parameter"
        tree = expression.parse(problem["parameters"]["expression"])
        assert expression.evaluate(tree) == _answer_as_fraction(problem["correct"])
