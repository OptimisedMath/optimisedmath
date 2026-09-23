"""Every Kolejność wykonywania działań generator's `expression` parameter must parse
and evaluate to the Problem's own answer, and its `question` must be exactly what
`backend.expression.render` draws from that same `expression` (ADR-0017) — there is
only one string, authored once as ASCII and rendered to LaTeX, not two hand-written
copies that could drift apart the way #318 found them doing.

A generator picks its template with `random.choice`, so no single call fires every
branch — the same sweep shape as `test_trap_slugs.py`. Running each of the twelve
generators (six per Chapter, #245) many times does: wrong precedence, wrong
associativity, a drifted decimal, or a `question` a template built by hand instead
of deriving, all surface as a mismatch, on any template.

`backend/expression.py` has no test file of its own; these sweeps are what exercise it.
"""

import re
from decimal import Decimal
from fractions import Fraction

import pytest

from backend import expression
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500

# Both Chapters name their generators `dec_order_N` / `frac_ord_N`, and nothing else
# in the registry contains "ord" — the count below is what keeps that true.
KOLEJNOSC_GENERATORS = sorted(name for name in FUNCTION_REGISTRY if "ord" in name)

_FRAC_TOKEN_RE = re.compile(r"\\frac\{(-?\d+)\}\{(\d+)\}")


def _latex_to_expression(latex: str) -> str:
    """The inverse of `expression.render`, kept only as a test fixture to close the
    `parse -> render -> parse` value loop below. Production code has no caller left
    for this direction (ADR-0017): a generator authors the ASCII `expression` first
    and derives its LaTeX `question` from it, never the other way round. This inverse
    can drift from `render` without a caller noticing — that drift risk is the price
    of keeping the round-trip property under test."""
    return _FRAC_TOKEN_RE.sub(r"\1/\2", latex).replace("\\cdot", "*")


def _answer_as_fraction(correct: str) -> Fraction:
    """Read a Problem's `correct` string exactly: a LaTeX `\\frac{n}{d}` or bare
    integer (Ułamki Zwykłe options, rendered per ADR-0017), or a decimal comma
    (Ułamki Dziesiętne options, unchanged by it)."""
    if "," in correct:
        return Fraction(Decimal(correct.replace(",", ".")))
    return Fraction(_latex_to_expression(correct))


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
def test_question_is_exactly_the_expression_rendered(name):
    """There is only one string: the `question` a Student reads is `render(parse(
    expression))`, not a second copy a template wrote by hand (#318's root cause).
    True by construction against today's code and blind to a `render` fault, since
    both sides run through it — what this pins is that a template cannot go back to
    hand-writing its `question` without this failing."""
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        tree = expression.parse(problem["parameters"]["expression"])
        assert problem["question"] == expression.render(tree)


@pytest.mark.parametrize("name", KOLEJNOSC_GENERATORS)
def test_rendered_latex_parses_back_to_the_same_value(name):
    """`render` puts back what `parse` read: the LaTeX it emits re-reads unchanged.

    Compared by value, not by string, so the notation choices `render` is free to make
    are not pinned as behaviour beyond what the assertion above already pins.
    """
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        tree = expression.parse(problem["parameters"]["expression"])
        round_tripped = expression.parse(_latex_to_expression(expression.render(tree)))
        assert expression.evaluate(round_tripped) == expression.evaluate(tree)
