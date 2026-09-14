"""Every Kolejność wykonywania działań generator's `expression` parameter must parse
and evaluate to the Problem's own answer.

A generator picks its template with `random.choice`, so no single call fires every
branch — the same sweep shape as `test_trap_slugs.py`. Running each of the twelve
generators (six per Chapter, #245) many times does: wrong precedence, wrong
associativity, or a drifted decimal all surface as a mismatch, on any template.

`backend/expression.py` has no test file of its own; these sweeps are what exercise it.
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from backend import expression
from backend.core.utils import latex_to_expression
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500

# Both Chapters name their generators `dec_order_N` / `frac_ord_N`, and nothing else
# in the registry contains "ord" — the count below is what keeps that true.
KOLEJNOSC_GENERATORS = sorted(name for name in FUNCTION_REGISTRY if "ord" in name)


def _answer_as_fraction(correct: str) -> Fraction:
    """Read a Problem's `correct` string — `n/d` or a decimal comma — exactly."""
    if "," in correct:
        return Fraction(Decimal(correct.replace(",", ".")))
    return Fraction(correct)


def test_the_sweep_covers_every_kolejnosc_generator():
    """A drifted name filter would leave the sweeps below parametrized over nothing."""
    assert len(KOLEJNOSC_GENERATORS) == 12, KOLEJNOSC_GENERATORS


@pytest.mark.parametrize("name", KOLEJNOSC_GENERATORS)
def test_expression_parameter_evaluates_to_the_problem_answer(name):
    """The emitted `expression` is the Problem it was generated from, not another one."""
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


@pytest.mark.parametrize("name", KOLEJNOSC_GENERATORS)
def test_rendered_latex_parses_back_to_the_same_value(name):
    """`render` puts back what `parse` read: the LaTeX it emits re-reads unchanged.

    Compared by value, not by string, so the notation choices `render` is free to make
    (a whole number over `\\frac{n}{1}`) are not pinned as behaviour.
    """
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        tree = expression.parse(problem["parameters"]["expression"])
        round_tripped = expression.parse(latex_to_expression(expression.render(tree)))
        assert expression.evaluate(round_tripped) == expression.evaluate(tree)
